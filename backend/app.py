from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

class ChatManager:
    def __init__(self):
        # Get API key from environment variable
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conversations: Dict[str, List[Dict]] = {}
        self.models = {
            "gpt-4-0": {"name": "GPT-4-0", "max_tokens": 4096},
            "gpt-4": {"name": "GPT-4", "max_tokens": 8192},
            "gpt-3.5-turbo": {"name": "GPT-3.5 Turbo", "max_tokens": 4096}
        }

    def get_response(self, conversation_id: str, message: str, model: str = "gpt-3.5-turbo") -> dict:
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        # Prepare the messages including conversation history
        messages = [
            {"role": "system", "content": "You are Tyo Technologies' advanced AI assistant. You are helpful, knowledgeable, and professional."}
        ]
        messages.extend(self.conversations[conversation_id])
        messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=self.models[model]["max_tokens"],
                presence_penalty=0.6,
                frequency_penalty=0.5
            )

            # Store the conversation
            self.conversations[conversation_id].append({"role": "user", "content": message})
            self.conversations[conversation_id].append({"role": "assistant", "content": response.choices[0].message.content})

            return {
                "status": "success",
                "message": response.choices[0].message.content,
                "conversation_id": conversation_id
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def clear_conversation(self, conversation_id: str) -> dict:
        if conversation_id in self.conversations:
            self.conversations[conversation_id] = []
            return {"status": "success", "message": "Conversation cleared"}
        return {"status": "error", "message": "Conversation not found"}

chat_manager = ChatManager()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    conversation_id = data.get('conversation_id', str(datetime.now().timestamp()))
    message = data.get('message')
    model = data.get('model', 'gpt-3.5-turbo')
    
    if not message:
        return jsonify({"status": "error", "message": "No message provided"}), 400
        
    response = chat_manager.get_response(conversation_id, message, model)
    return jsonify(response)

@app.route('/api/clear', methods=['POST'])
def clear():
    data = request.json
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({"status": "error", "message": "No conversation ID provided"}), 400
        
    response = chat_manager.clear_conversation(conversation_id)
    return jsonify(response)

@app.route('/api/models', methods=['GET'])
def get_models():
    return jsonify({"models": list(chat_manager.models.keys())})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
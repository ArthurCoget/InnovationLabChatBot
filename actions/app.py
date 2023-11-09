from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    user_message = data['message']  # Veronderstel dat het bericht in een veld met de naam 'message' wordt verzonden vanuit de frontend
    
    # Stuur het gebruikersbericht naar de Rasa-chatbot en ontvang het antwoord
    rasa_response = send_message_to_rasa(user_message)
    
    # Stuur het antwoord van de Rasa-chatbot terug naar de frontend
    return jsonify({'response': rasa_response})

def send_message_to_rasa(message):
    # Stuur het gebruikersbericht naar de Rasa-chatbot API
    rasa_api_url = 'http://localhost:5005/webhooks/rest/webhook'  # Vervang dit door de daadwerkelijke URL van je Rasa-chatbot
    response = requests.post(rasa_api_url, json={'message': message})
    
    # Ontvang en retourneer het antwoord van de Rasa-chatbot
    rasa_response = response.json()
    return rasa_response

if __name__ == '__main__':
    app.run(port=5000)
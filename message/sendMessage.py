import os
import requests

#CHAVES
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE")

# FUNÇÃO DE ENVIO DE MENSAGEM
def send_whatsapp_message(to_number, message_text):
    
    
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }
    # Formato do corpo da mensagem
    data = {
        "number": to_number,
        "textMessage": {
            "text": message_text
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"Mensagem enviada para {to_number}: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem via Evolution API: {e}")
        if e.response is not None:
            print(f"Detalhes do erro: {e.response.text}")
        return False

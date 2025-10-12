import json
import logging
import requests
from data.apis import evo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EvoConnection:
    def __init__(self):
        self.EVO_URL = evo.get_url()
        self.EVO_INSTANCIA = evo.get_instancia()
        self.EVO_TOKEN = evo.get_token()

    async def processar_webhook(self, data: dict):
        if 'messages' not in data or not data['messages']:
            logger.info("Nenhuma mensagem encontrada para processamento no webhook.")
            return {"status": "ok", "message": "Nenhuma mensagem encontrada para processamento."}
        
        for message in data['messages']:
            
            if message.get('key', {}).get('fromMe', False):
                logger.debug("Mensagem ignorada: enviada pela própria instância (fromMe=True).")
                continue
            
            usr_text = message.get('message', {}).get('conversation') or \
                        message.get('message', {}).get('extendedTextMessage', {}).get('text')
            
            numero = message.get('key', {}).get('remoteJid', '')       
            f_numero = numero.split('@')[0]
            
            if usr_text:
                logger.info(f"Mensagem de texto recebida. De: {f_numero}. Texto: '{usr_text[:50]}...'")
                return {'Mensagem': usr_text, 'Numero': f_numero}

        logger.info("Nenhuma mensagem de texto válida encontrada no payload.")
        return {"status": "ok", "message": "Nenhuma mensagem de texto válida para processamento."}
    
    
    def enviar_resposta(self, numero: str, resposta: str):

        if not self.EVO_URL or not self.EVO_INSTANCIA or not self.EVO_TOKEN:
            logger.error("Erro: URL, Instância ou Chave da Evolution não configuradas.")
            return False

        url = f"{self.EVO_URL}/message/sendText/{self.EVO_INSTANCIA}" 
        
        payload = json.dumps({
        "number": numero,
        "text": resposta
        })
        
        headers = {
        'Content-Type': 'application/json', 
        'apikey': self.EVO_TOKEN, 
        }
        
        
        logger.debug(f"Tentando enviar para URL: {url}")
        logger.debug(f"Payload de Envio: {payload}")
        logger.debug(f"Chave API: {self.EVO_TOKEN}")

        
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status() 
            logger.info(f"Resposta Evolution API enviada para {numero}. Status: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem pela Evolution API: {e}")
            if response is not None:
                logger.error(f"Detalhes do erro da Evolution: {response.text}")
            return False
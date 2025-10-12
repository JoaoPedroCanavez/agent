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
        if 'data' not in data:
            logger.warning("Payload do webhook recebido sem a chave 'data'.")
            return {"status": "ok", "message": "Payload malformado."}

        message = data['data'] 
        
        if message.get('key', {}).get('fromMe', False):
            logger.debug("Mensagem ignorada: enviada pela própria instância (fromMe=True).")
            return {"status": "ok", "message": "Mensagem de saída ignorada."}
        
        numero = message.get('key', {}).get('remoteJid', '')       
        f_numero = numero.split('@')[0]
        
        usr_text = message.get('message', {}).get('conversation') or \
                   message.get('message', {}).get('extendedTextMessage', {}).get('text')
        
        tipo, conteudo = None, None

        if usr_text:
            tipo = 'text'
            conteudo = usr_text
            logger.info(f"Mensagem de texto recebida. De: {f_numero}. Texto: '{usr_text[:50]}...'")
            
        elif 'imageMessage' in message.get('message', {}):
            tipo = 'image'
            midia_data = message['message']['imageMessage']
            caption = midia_data.get('caption', '').strip()
            
            if not caption:
                caption = "analise e descreva esta imagem"
            
            conteudo = {
                'caption': caption,
                'url': midia_data.get('url', 'URL_NAO_DISPONIVEL') 
            }
            logger.info(f"Mensagem de imagem recebida. Legenda/Instrução: {conteudo['caption'][:30]}...")

        elif 'audioMessage' in message.get('message', {}):
            tipo = 'audio'
            midia_data = message['message']['audioMessage']
            
            instrucao = "transcreva este áudio" 
            
            conteudo = {
                'instrucao': instrucao, 
                'url': midia_data.get('url', 'URL_NAO_DISPONIVEL'),
                'ptt': midia_data.get('ptt', False) 
            }
            logger.info(f"Mensagem de áudio recebida. Instrução: {instrucao}")

        elif 'documentMessage' in message.get('message', {}):
            tipo = 'document'
            midia_data = message['message']['documentMessage']
            caption = midia_data.get('caption', '').strip()
            
            if not caption:
                caption = "extraia o texto e resuma este documento"

            conteudo = {
                'caption': caption,
                'fileName': midia_data.get('fileName', 'arquivo'),
                'mimetype': midia_data.get('mimetype', ''),
                'url': midia_data.get('url', 'URL_NAO_DISPONIVEL')
            }
            logger.info(f"Mensagem de documento/PDF recebida. Instrução: {caption[:30]}...")
            
        else:
            logger.info("Mensagem ignorada: Tipo não suportado ou vazio.")
            return {"status": "ok", "message": "Tipo de mensagem não suportado."}
        return {
            'Tipo': tipo, 
            'Conteudo': conteudo, 
            'Numero': f_numero
        }

    
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
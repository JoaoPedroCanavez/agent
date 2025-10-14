import json
import logging
import requests
from data.apis import evo
from negocio.servico.processador_midia import ProcessadorDeMidia
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
class EvoConnection:
    def __init__(self):
        self.EVO_URL = evo.get_url()
        self.EVO_INSTANCIA = evo.get_instancia()
        self.EVO_TOKEN = evo.get_token()
#--------------------------------------------------------------------------------------------------------------------#
    #Função assincrona que faz o processamento dos dados trazidos pelo webhook em formato json,
    #e devolve somente os dados necessarios
    async def processar_webhook(self, data: dict, processador_midia = ProcessadorDeMidia):
        if 'data' not in data:
            logger.warning("Payload do webhook recebido sem a chave     'data'.")
            return {"status": "ok", "message": "Payload malformado."}
        
        #Abstrai o conjunto de dados do dicionario em uma varivel,
        #filtra para processar somente a mensagem do remetente
        mensagem = data['data'] 
        if mensagem.get('key', {}).get('fromMe', False):
            logger.debug("Mensagem ignorada: enviada pela própria instância (fromMe=True).")
            return {"status": "ok", "message": "Mensagem de saída ignorada."}   
        #Instancia a mesagem recebida em uma variavel e vefica o tipo de mensagem 
        usr_text = processador_midia.verfica_tipo(mensagem.get('message', {}))   
        if usr_text is None:
            logger.info("Mensagem ignorada: não é um texto simples.")
            return {"status": "ok", "message": "Não é uma mensagem de texto."}
        
        #Capta e formata o numero do remetente
        numero = mensagem.get('key', {}).get('remoteJid', '')       
        f_numero = numero.split('@')[0]
    
        #envia log de confirmação da filtragem dos dados e devolve os dados em um dicionario
        logger.info(f"Mensagem de texto recebida. De: {f_numero}. Texto: '{usr_text[:50]}...'")
        return {'Mensagem': usr_text, 'Numero': f_numero}
#--------------------------------------------------------------------------------------------------------------------#
    def enviar_resposta(self, numero: str, resposta: str):

        #Vefica se está sendo recebido todos os paramentos da url
        if not self.EVO_URL or not self.EVO_INSTANCIA or not self.EVO_TOKEN:
            logger.error("Erro: URL, Instância ou Chave da Evolution não configuradas.")
            return False

        #Instancia a variavel para chamada do http para envio de mensagem, 
        #e faz o log de debug 
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

        #faz a requisição de envio(POST) capturando possiveis erros na requisição http,
        #e faz log de possivel sucesso e erros
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
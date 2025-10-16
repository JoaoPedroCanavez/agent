import json
import logging
import requests
from data.apis import z
from data.apis import evo
from negocio.servico.processador_midia import ProcessadorDeMidia
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
class TratamentoMsg:
#--------------------------------------------------------------------------------------------------------------------#
    def __init__(self):
        self.EVO_URL = evo.get_url()
        self.EVO_INSTANCIA = evo.get_instancia()
        self.EVO_TOKEN = evo.get_token()
        self.Z_URL = z.get_url()
        self.Z_INSTANCIA = z.get_instancia()
        self.Z_TOKEN = z.get_token()
        self.S_Z_TOKEN = z.get_s_token()
#--------------------------------------------------------------------------------------------------------------------#
    async def processar_webhook(self, data: dict, processador_midia: ProcessadorDeMidia):
        
        # Usa o novo método para extrair dados e verificar se é mensagem de saída
        mensagem_mapeada = self._mapear_payload(data)
        
        if mensagem_mapeada is None:
            return {"status": "ok", "message": "Payload malformado ou mensagem de saída ignorada."}
        
        # A partir daqui, o fluxo continua com a estrutura esperada:
        
        # Instancia a mensagem recebida em uma variavel e vefica o tipo de mensagem 
        # NOTE: O ProcessadorDeMidia.verfica_tipo precisa ser adaptado para lidar com as diferenças
        # de chaves da Z-API (ex: 'audioMessage' pode ter outro nome ou estrutura)
        usr_text = processador_midia.verfica_tipo(mensagem_mapeada.get('message', {}))
        
        if usr_text is None:
            logger.info("Mensagem ignorada: não é um texto simples ou formato de mídia não suportado.")
            return {"status": "ok", "message": "Não é uma mensagem de texto/mídia suportada."}
        
        # Capta e formata o numero do remetente
        numero_completo = mensagem_mapeada.get('remoteJid', '')
        f_numero = numero_completo.split('@')[0]
        
        if isinstance(usr_text, str):

            texto_para_log = usr_text[:50]
        elif isinstance(usr_text, list) and usr_text and isinstance(usr_text[0], dict) and 'text' in usr_text[0]:
            # Caso seja uma mídia (ex: imagem/pdf) que retorna a lista de dicts (verfica_tipo)
            # Pega o campo 'text' da primeira entrada (o prompt de interpretação)
            texto_para_log = usr_text[0]['text'][:50]
        else:
            # Caso seja um formato inesperado, use uma string padrão.
            texto_para_log = f"Formato não fatiável ({type(usr_text).__name__})"

        # envia log de confirmação da filtragem dos dados e devolve os dados em um dicionario
        logger.info(f"Mensagem de texto recebida. De: {f_numero}. Texto: '{texto_para_log}...'")
        return {'Mensagem': usr_text, 'Numero': f_numero}
#--------------------------------------------------------------------------------------------------------------------#
    def enviar_resposta(self, numero: str, resposta: str):

        
        if self.EVO_URL and self.EVO_INSTANCIA and self.EVO_TOKEN:
            try:
                logger.info("Tentando enviar via Evolution API.")
                url = f"{self.EVO_URL}/message/sendText/{self.EVO_INSTANCIA}"
                headers = {
                    'Content-Type': 'application/json', 
                    'apikey': self.EVO_TOKEN, 
                }    
                payload = json.dumps({"number": numero, "text": resposta})

                response = requests.post(url, headers=headers, data=payload, timeout=10)
                response.raise_for_status() 
                logger.info(f"Resposta enviada com sucesso pela Evolution API para {numero}. Status: {response.status_code}")
                return True 
                
            except requests.exceptions.RequestException as e:
                logger.error(f"EVOLUTION FALHOU. Erro: {e}. Detalhes: {getattr(response, 'text', 'N/A')}")
                logger.warning("Iniciando fallback para Z-API...")
            except Exception as e:
                logger.error(f"Erro inesperado na Evolution API: {e}")
                logger.warning("Iniciando fallback para Z-API...")

        else:
            logger.info("EVOLUTION API não configurada. Tentando Z-API diretamente.")

        if self.Z_URL and self.Z_INSTANCIA and self.Z_TOKEN:
            try:
                logger.info("Tentando enviar via Z-API.")
                url = f"{self.Z_URL}/instances/{self.Z_INSTANCIA}/token/{self.Z_TOKEN}/send-text/" 
                headers = {
                    'Content-Type': 'application/json', 
                    'Client-Token': self.S_Z_TOKEN,
                }  
                payload = json.dumps({"phone": numero, "message": resposta})

                response = requests.post(url, headers=headers, data=payload, timeout=10)
                response_text = response.text 
                response.raise_for_status() 

                logger.info(f"Resposta enviada com sucesso pela Z-API para {numero}. Status: {response.status_code}")
                logger.info(f"CORPO DA RESPOSTA Z-API: {response_text}") 
                return True 
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Z-API TAMBÉM FALHOU. Erro: {e}. Detalhes: {getattr(response, 'text', 'N/A')}")
                return False 
            except Exception as e:
                logger.error(f"Erro inesperado na Z-API: {e}")
                return False
        
        else:
            logger.error("ERRO CRÍTICO: Evolution e Z-API não configuradas ou falharam no envio.")
            return False

#--------------------------------------------------------------------------------------------------------------------#
    def _mapear_payload(self, data: dict):
        mensagem_data = {}
        mensagem = {}
        is_evolution = False
        remote_jid = ''

        if 'data' in data:
            mensagem_data = data['data']
            mensagem = mensagem_data.get('message', {})
            is_evolution = True

        elif 'chatLid' in data and 'phone' in data:
            is_evolution = False
            mensagem_data = data 
            mensagem = {'conversation': data.get('text')} 
            
        else:
            logger.warning("Payload recebido não corresponde aos formatos Evolution ou Z-API esperados.")
            return None

        if is_evolution:
             from_me = mensagem_data.get('key', {}).get('fromMe', False)
        else:
             from_me = mensagem_data.get('fromMe', False) 
        
        if from_me:
            logger.debug(f"Mensagem {'Evolution' if is_evolution else 'Z-API'} ignorada: enviada pela própria instância (fromMe=True).")
            return None
        
        if is_evolution:
            remote_jid = mensagem_data.get('key', {}).get('remoteJid', '')
        else:
            remote_jid = mensagem_data.get('phone', '')
        return {
            'message': mensagem, 
            'remoteJid': remote_jid,
            }
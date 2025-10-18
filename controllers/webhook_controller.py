import json
import logging
import requests
from config import z
from config import evo
from negocio.media_processor import ProcessadorDeMidia
from typing import Dict, Union, Any, List

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
        
        dados_mapeados = self._mapear_payload(data)
        if dados_mapeados is None:
            return {"status": "ok", "message": "Payload malformado ou mensagem de saída ignorada."}
        
        objeto_mensagem = dados_mapeados.get('message', {})

        # A lógica de verificação de tipo (incluindo áudio, imagem e texto)
        # agora reside exclusivamente em ProcessadorDeMidia.
        texto_usuario = processador_midia.verificar_tipo_e_processar(objeto_mensagem)

        if texto_usuario is None:
            logger.info("Mensagem ignorada: não é um texto simples ou formato de mídia suportado.")
            return {"status": "ok", "message": "Não é uma mensagem de texto/mídia suportada."}

        # --- Finaliza o Processamento ---
        numero_completo = dados_mapeados.get('remoteJid', '')
        numero = numero_completo.split('@')[0]
        
        # Lógica para logar a mensagem, adaptada para strings ou listas de mídia
        if isinstance(texto_usuario, str):
            log_texto = texto_usuario[:50]
        elif isinstance(texto_usuario, list) and texto_usuario and isinstance(texto_usuario[0], dict) and 'text' in texto_usuario[0]:
            log_texto = texto_usuario[0]['text'][:50]
        else:
            log_texto = f"Formato não fatiável ({type(texto_usuario).__name__})"

        logger.info(f"Mensagem recebida. De: {numero}. Texto: '{log_texto}...'")
        return {'Mensagem': texto_usuario, 'Numero': numero}
#--------------------------------------------------------------------------------------------------------------------#
    def enviar_resposta(self, numero: str, resposta: str):
        
        # 1. TENTATIVA COM EVOLUTION API (Prioridade/Fallback)
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
            logger.info("Evolution API não configurada. Tentando Z-API diretamente.")

        # 2. FALLBACK COM Z-API
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
                texto_resposta = response.text 
                response.raise_for_status() 

                logger.info(f"Resposta enviada com sucesso pela Z-API para {numero}. Status: {response.status_code}")
                logger.info(f"CORPO DA RESPOSTA Z-API: {texto_resposta}") 
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
    def _mapear_payload(self, data: dict) -> Union[Dict, None]:
        dados_mensagem: Dict = {}
        objeto_mensagem: Dict = {}
        eh_evolution: bool = False
        jid_remoto: str = ''
        
        # Tenta formato Evolution
        if 'data' in data:
            logger.info(f"Log: Mapeamento Evolution")
            dados_mensagem = data['data']
            objeto_mensagem = dados_mensagem.get('message', {})
            eh_evolution = True

        # Tenta formato Z-API (ou formato alternativo com 'phone' no nível superior)
        elif 'phone' in data:
            logger.info(f"Log: Mapeamento Z-API/Alternativo")
            dados_mensagem = data 
            objeto_mensagem = {'conversation': data.get('text')}
            eh_evolution = False
            
        else:
            logger.warning("Payload recebido não corresponde aos formatos Evolution ou Z-API esperados.")
            return None

        # Verifica se a mensagem foi enviada pelo próprio bot (fromMe=True)
        if eh_evolution:
             eh_saida = dados_mensagem.get('key', {}).get('fromMe', False)
        else:
             eh_saida = dados_mensagem.get('fromMe', False) 
        
        if eh_saida:
            logger.debug(f"Mensagem de saída ignorada.")
            return None
        
        # Extrai o JID (número completo)
        if eh_evolution:
            jid_remoto = dados_mensagem.get('key', {}).get('remoteJid', '')
        else:
            jid_remoto = dados_mensagem.get('phone', '')
            
        return {
            'message': objeto_mensagem, 
            'remoteJid': jid_remoto,
        }
import logging
import os
import mimetypes 
import requests
from openai import OpenAI
from typing import List, Dict, Union, Any, Optional
logger = logging.getLogger(__name__)


#--------------------------------------------------------------------------------------------------------------------#
class Agente:
#--------------------------------------------------------------------------------------------------------------------#


  def __init__(self, chave: str):
    self.openai_api_key = chave
    self.client =  OpenAI(api_key=chave)


#--------------------------------------------------------------------------------------------------------------------#


  def gerar_payload(self, input_usuario: Union[str, List[Dict[str, Any]]], instrucoes: str, contexto: List[Dict]) -> str|None:
    corpo_mensagem: List[Dict[str, Any]] = []
    if isinstance(input_usuario, str):
        corpo_mensagem.append({"type": "input_text", "text": input_usuario})
        logger.info(f"Input do Usuário para o Agente (Texto): '{input_usuario}'")
    elif isinstance(input_usuario, list):
        for item in input_usuario:
            if item.get("type") == "input_text":
                corpo_mensagem.append({"type": "input_text", "text": item.get("text")})
            elif item.get("type") == "input_file":
                file_path = item.get("file_path")
                corpo_mensagem.append({
                    "type": "input_file",
                    "file_path": file_path
                })
    else:
        logger.warning(f"Tipo de input_usuario não suportado: {type(input_usuario)}")
        return "Desculpe, não consegui entender o formato da sua mensagem."
        
    return self.call_agent(contexto, instrucoes, corpo_mensagem)

#--------------------------------------------------------------------------------------------------------------------#
  
  def _manual_file_upload(self, file_path: str) -> Optional[str]:
      """Faz upload manual do arquivo para a API /v1/files usando requests."""
      file_name_with_ext = os.path.basename(file_path)
      mime_type, _ = mimetypes.guess_type(file_path)
      if not mime_type:
          mime_type = 'image/jpeg'

      logger.info(f"LOG: Iniciando upload MANUAL. Filename: {file_name_with_ext}, MIME: {mime_type}")
      
      url = "https://api.openai.com/v1/files"
      headers = {
          "Authorization": f"Bearer {self.openai_api_key}"
      }
      files = {
          'purpose': (None, 'vision'),
          'file': (file_name_with_ext, open(file_path, 'rb'), mime_type) 
      }
      
      try:
          response = requests.post(url, headers=headers, files=files, timeout=30)
          response.raise_for_status() 
          
          response_data = response.json()
          file_id = response_data.get("id")
          
          if file_id:
              logger.info(f"LOG 1 (UPLOAD MANUAL SUCESSO): Arquivo enviado. ID: {file_id}")
              return file_id
          else:
              logger.error(f"Erro no upload manual: ID do arquivo não encontrado na resposta. Resposta: {response_data}")
              return None
              
      except requests.exceptions.RequestException as e:
          logger.error(f"Erro na requisição de upload manual: {e}")
          if e.response is not None:
               logger.error(f"Detalhes do erro HTTP: {e.response.status_code} - {e.response.text}")
          return None
      except Exception as e:
           logger.error(f"Erro inesperado no upload manual: {e}", exc_info=True)
           return None
      finally:
            if 'file' in files and hasattr(files['file'][1], 'close'):
                files['file'][1].close()

#--------------------------------------------------------------------------------------------------------------------#


  def call_agent(self, contexto: List[Dict[str,Any]], instrucoes: str, corpo_mensagem: list[dict[str,Any]]) -> str|None:
      file_path: Optional[str] = None 
      uploaded_file_id: Optional[str] = None 
      
      try:
        mensagens = [{"role": "system", "content": instrucoes}]
        mensagens.extend(contexto)

        user_content_list: List[Dict[str, Any]] = []
        file_part = next((item for item in corpo_mensagem if item.get("type") == "input_file"), None)
        text_prompt = next((item.get("text") for item in corpo_mensagem if item.get("type") == "input_text"), None)

        if text_prompt:
            user_content_list.append({"type": "text", "text": text_prompt})

        if file_part:
            file_path = file_part["file_path"]

            uploaded_file_id = self._manual_file_upload(file_path)
            
            if not uploaded_file_id:
                 raise Exception("Falha no upload manual do arquivo para OpenAI.")
            user_content_list.append({
                 "type": "image_url",
                 "image_url": {
                      "url": f"openai_file_id://{uploaded_file_id}" 
                 }
             })

        if user_content_list: 
             mensagens.append({"role": "user", "content": user_content_list})
        else:
             logger.warning("Nenhum conteúdo de usuário (texto ou arquivo) encontrado para enviar.")
             return "Não recebi sua mensagem ou arquivo para processar."

        logger.info(f"LOG 2 (CHAT PAYLOAD): Conteúdo do usuário formatado: {user_content_list}")
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens,
            temperature=0.5,
            max_tokens=2048,      
            top_p=1,
            timeout=60
          )
        resposta_agente = response.choices[0].message.content
        logger.info("Resposta da OpenAI recebida com sucesso.")
        return resposta_agente

      except Exception as e:
          logger.error(f"Erro ao chamar o Agente OpenAI: {e}", exc_info=True)
          if hasattr(e, 'response') and e.response is not None:
               try:
                   error_details = e.response.json()
                   logger.error(f"Detalhes do Erro OpenAI (JSON): {error_details}")
               except Exception:
                    logger.error(f"Detalhes do Erro OpenAI (Texto): {e.response.text}")
          return "Estou ocupado no momento, me chame novamente mais tarde."
      finally:
          if file_path and os.path.exists(file_path):
              os.remove(file_path)
          if uploaded_file_id:
               try:
                   self.client.files.delete(uploaded_file_id)
               except Exception as del_err:
                    logger.warning(f"Falha ao deletar arquivo da OpenAI {uploaded_file_id}: {del_err}")
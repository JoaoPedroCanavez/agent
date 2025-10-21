import logging
from openai import OpenAI
from typing import List, Dict, Union, Any
logger = logging.getLogger(__name__)


#--------------------------------------------------------------------------------------------------------------------#
class Agente:
#--------------------------------------------------------------------------------------------------------------------#


  def __init__(self, chave: str):
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
            elif item.get("type") == "input_image":
                url = item.get("image_url")
                corpo_mensagem.append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })
    else:
        logger.warning(f"Tipo de input_usuario não suportado: {type(input_usuario)}")
        return "Desculpe, não consegui entender o formato da sua mensagem."
    return self.call_agent(contexto, instrucoes, corpo_mensagem)


#--------------------------------------------------------------------------------------------------------------------#


  def call_agent(self, contexto: List[Dict[str,Any]], instrucoes: str, corpo_mensagem: list[dict[str,Any]]) -> str|None:
      try:
        mensagens = self.cntx_contructor(contexto, instrucoes, corpo_mensagem)
      # Chamada da API para gerar resposta
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens,
            temperature=0.5,
            max_tokens=2048,      
            top_p=1
          )
        
        # Retorna a mensagem gerada
        resposta_agente = response.choices[0].message.content
        logger.info("Resposta da OpenAI recebida com sucesso.")
        return resposta_agente

      except Exception as e:
          logger.error(f"Erro ao chamar o Agente OpenAI: {e}", exc_info=True)
          return "Estou ocupado no momento, me chame novamente mais tarde."
    

#--------------------------------------------------------------------------------------------------------------------#


  def cntx_contructor(self, contexto: List[Dict[str,Any]], instrucoes: str, corpo_mensagem: list[dict[str,Any]]) -> List[Dict[str, Any]]:
      try:
        mensagens = [{"role": "system", "content": instrucoes}]
        mensagens.extend(contexto)
        if (len(corpo_mensagem) == 1 and 
            corpo_mensagem[0].get("type") == "input_text"):
            user_content = corpo_mensagem[0]["text"]
        else:
            user_content = []
            for item in corpo_mensagem:
                if item.get("type") == "input_text":
                    user_content.append({"type": "text", "text": item.get("text")})
                elif item.get("type") == "image_url":
                    user_content.append(item)
        mensagens.append({"role": "user", "content": user_content})
        logger.info(mensagens) 
        return mensagens
      except Exception as e:
          logger.error(f'Erro: {e}')
import logging
from openai import OpenAI
from typing import List, Dict
logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
class Agente:
#--------------------------------------------------------------------------------------------------------------------#
  def __init__(self, chave: str):
    self.client =  OpenAI(api_key=chave)
#--------------------------------------------------------------------------------------------------------------------#
  def processar_input(self, texto_usuario: str, instrucoes: str, contexto: List[Dict]) -> str:

    logger.info(f"Input do Usuário para o Agente: '{texto_usuario}'")
    
    try:
      # Constrói a janela de contexto
      mensagens = [{"role": "system", "content": instrucoes},]
      mensagens.extend(contexto)
      mensagens.append({"role": "user", "content": texto_usuario}) 
      
      # Chamada da API para gerar resposta
      logger.debug(f"Enviando para GPT-4o-mini com {len(mensagens)} mensagens no contexto.")
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

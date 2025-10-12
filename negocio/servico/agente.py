import logging
from openai import OpenAI
from typing import List, Dict # Importação para melhor tipagem

logger = logging.getLogger(__name__)

class Agente:

  def __init__(self, key: str):
    self.client =  OpenAI(api_key=key)
  
  # Adicionada tipagem para clareza
  def processar_input(self, usr_text: str, instrucoes: str, contexto: List[Dict]) -> str:
    
    logger.info(f"Input do Usuário para o Agente: '{usr_text}'")
    try:
      # CORREÇÃO: Concatena as listas usando o operador '+'
      # A ordem é importante: SYSTEM + HISTÓRICO + MENSAGEM ATUAL
      messages = [
          {"role": "system", "content": instrucoes},
      ]
      
      # Adiciona o histórico do DB (lista de dicionários)
      messages += contexto 
      
      # Adiciona a mensagem atual do usuário
      messages.append({"role": "user", "content": usr_text}) 
      
      logger.debug(f"Enviando para GPT-4o-mini com {len(messages)} mensagens no contexto.")
      
      response = self.client.chat.completions.create(
          model="gpt-4o-mini", 
          messages=messages,  
          temperature=0.5,
          max_tokens=2048,      
          top_p=1
        )
      
      resposta_do_agente = response.choices[0].message.content
      logger.info("Resposta da OpenAI recebida com sucesso.")
      return resposta_do_agente

    except Exception as e:
      logger.error(f"Erro ao chamar o Agente OpenAI: {e}", exc_info=True)
      return "Desculpe, Marcelo, tive um problema para processar sua solicitação agora. Por favor, tente novamente mais tarde."
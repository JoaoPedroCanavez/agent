import logging
from openai import OpenAI
from typing import List, Dict
logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
class Agente:
#--------------------------------------------------------------------------------------------------------------------#
  #instanciando somente a APIKEY na chamada da classe
  def __init__(self, key: str):
    self.client =  OpenAI(api_key=key)
#--------------------------------------------------------------------------------------------------------------------#
  def processar_input(self, usr_text: str, instrucoes: str, contexto: List[Dict]) -> str:

    #Log informando a mensagem recebida
    logger.info(f"Input do Usuário para o Agente: '{usr_text}'")
    
    #Fax o tratamento da chamada da API para gerar resposta
    try:

      #Instanciado a varivel mensagem com o prompt(intrucoes), 
      #a janela de contexto(contexto), e a mensagem a ser respondida
      messages = [{"role": "system", "content": instrucoes},]
      messages.extend(contexto)
      messages.append({"role": "user", "content": usr_text}) 
      
      #Fazendo a chamada de processamento da mensagem pela IA
      logger.debug(f"Enviando para GPT-4o-mini com {len(messages)} mensagens no contexto.")
      response = self.client.chat.completions.create(
          model="gpt-4o-mini", 
          messages=messages,  
          temperature=0.5,
          max_tokens=2048,      
          top_p=1
        )
      
      #Em caso de sucesso retorna a mensagem gerada pelo agente
      resposta_do_agente = response.choices[0].message.content
      logger.info("Resposta da OpenAI recebida com sucesso.")
      return resposta_do_agente

    #faz o tratamento de erro generico
    except Exception as e:
        #Log para informar o erro especifico
        logger.error(f"Erro ao chamar o Agente OpenAI: {e}", exc_info=True)
        return "Estou ocupado no momento, me chame novamente mais tarde."
#--------------------------------------------------------------------------------------------------------------------#
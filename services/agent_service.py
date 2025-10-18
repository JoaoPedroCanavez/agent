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
  def processar_input(self, input_usuario: Union[str, List[Dict[str, Any]]], instrucoes: str, contexto: List[Dict]) -> str:
    if isinstance(input_usuario, str):
        #texto simples
        corpo_mensagem = [{"type": "text", "text": input_usuario}]
        logger.info(f"Input do Usuário para o Agente (Texto): '{input_usuario}'")
    
    elif isinstance(input_usuario, list):
        #Imagem/PDF
        corpo_mensagem = []
        prompt_de_interpretacao = "Mídia enviada para análise."

        for item in input_usuario:
            if item.get("type") == "input_text":
                corpo_mensagem.append({"type": "text", "text": item.get("text")})
                prompt_de_interpretacao = item.get("text")
            elif item.get("type") == "input_image":
                url = item.get("image_url")
                # A URL da imagem/PDF é formatada para o modelo GPT-4o-mini
                corpo_mensagem.append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })
        
        logger.info(f"Input do Usuário para o Agente (Mídia): '{prompt_de_interpretacao}'")
    
    else:
        logger.warning(f"Tipo de input_usuario não suportado: {type(input_usuario)}")
        return "Desculpe, não consegui entender o formato da sua mensagem."

    try:
      # 2. Constrói a janela de contexto completa
      mensagens = [{"role": "system", "content": instrucoes},]
      mensagens.extend(contexto)
      
      # Adiciona a mensagem do usuário (corpo_mensagem formatado)
      mensagens.append({"role": "user", "content": corpo_mensagem}) 
      
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

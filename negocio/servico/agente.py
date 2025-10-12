from openai import OpenAI
from dotenv import load_dotenv
import os

class Agente:
  load_dotenv
  gptkey = os.getenv('openAIKey')
  client =  OpenAI(api_key=gptkey)
  def __init__(self):
     pass
  
  def processar_input(self, usr_text: str) -> str:
    
    print(f"input: '{usr_text}'")
    try:
      system_instruction = (
        "#identidade\n"
        "Seu nome é ronaldo, você é um assistente pessoal do marcelo baldi, "
        "e somente ele te manda mensagem.\n\n"
        "#comunicação\n"
        "-sucinto\n-respeitoso\n-prestativo"
      )

      messages = [
          {"role": "system", "content": system_instruction},
          {"role": "user", "content": usr_text}
      ]
    
      print(f"input: '{usr_text}'")
    
      response = self.client.chat.completions.create(
          model="gpt-4o-mini", 
          messages=messages,  
          temperature=0.5,
          max_tokens=2048,      
          top_p=1
        )
      
      resposta_do_agente = response.choices[0].message.content
      return resposta_do_agente

    except Exception as e:
      print(f"Erro ao chamar o Agente OpenAI: {e}")
      return "Desculpe, Marcelo, tive um problema para processar sua solicitação agora. Por favor, tente novamente mais tarde."
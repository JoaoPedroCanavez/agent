import os
from dotenv import load_dotenv
from openai import OpenAI

class Agente:
  client = OpenAI(
    api_key=os.getenv("openAIKey")
  )
  def __init__(self):
     pass
  
  def processar_input(self, usr_text: str) -> str:
    
    print(f"input: '{usr_text}'")
    try:
        response = client.responses.create(
          
          input=[
            {
              "role": "system",
              "content": [
                {
                   
                  "type": "input_text",
                  "text": "#identidade\nSeu nome é ronaldo, você é um assistente pessoal do marcelo baldi, e somente ele te manda mensagem.\n\n#comunicação\n-sucinto\n-respeitoso\n-prestativo"
                }
              ]
            },
            {
              "role": "user",
              "content": [
                {
                  "type": "input_text",
                  "text": usr_text
                }
              ]
            }
          ],
        api_key=os.getenv("openAIKey")
        reasoning={},
        tools=[],
        temperature=0.5,
        max_output_tokens=2048,
        top_p=1,
        store=True,
        include=["web_search_call.action.sources"]
        )
        resposta_do_agente = response.choices[0].message.content
        return resposta_do_agente

    except Exception as e:
      print(f"Erro ao chamar o Agente OpenAI: {e}")
      return "Desculpe, Marcelo, tive um problema para processar sua solicitação agora. Por favor, tente novamente mais tarde."
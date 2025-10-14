#5511940804809
#5511940804809
import json
import uvicorn
import logging
from data.apis import ope
from negocio.servico.db import Banco
from negocio.servico import a_instrucoes
from negocio.servico.agente import Agente
from negocio.servico.evolution import EvoConnection 
from negocio.servico.processador_midia import ProcessadorDeMidia
from fastapi import FastAPI, Request, HTTPException
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
#Fazendo a chamada das classes criadas para aplicação
try:
    agent = Agente(ope.get_key())
except Exception as e:
    logger.error(f"Erro ao inicializar Agente (OpenAI): {e}")
    exit()
try:
    db = Banco()
except Exception as e:
    logger.error(f"Erro ao inicializar Banco (Supabase): {e}")
    exit()
try:
    evo_connector = EvoConnection()
except Exception as e:
    logger.error(f"Erro ao inicializar EvoConnection: {e}")
    exit()
try:
    processador_midia = ProcessadorDeMidia(ope.get_key()) 
except Exception as e:
    logger.error(f"Erro ao inicializar ProcessadorDeMidia: {e}")
    exit()
#--------------------------------------------------------------------------------------------------------------------#
app = FastAPI()
#Faz o tratamento dos dados recebidos pelo webhook usando FastAPI
@app.post("/webhook/message-upsert/messages-upsert")
async def evolution_webhook(request: Request):
    try:
        #Pega e aloca os dados enviados pelo webhook
        data = await request.json()
        process_data = await evo_connector.processar_webhook(data,processador_midia)
        
        #Encerra forçadamente a função caso os dados não sejam validos
        if process_data.get('status') == 'ok':
            logger.info(process_data.get('message'))
            return process_data
        
        #Faz tratamento de dados de um diconario para variavel,
        #e define o tipo de prompt que será usado a partir do numero de whatsapp
        mensagem = process_data.get('Mensagem')
        numero = process_data.get('Numero')
        prompt = a_instrucoes.escolhe_prompt(numero)
        
        #Pega o id do usario e verifica se foi possivel criar um, caso não exista
        id_usuario = db.busca_id_por_numero(numero)
        if id_usuario is None:
             raise Exception("Falha ao obter ou criar ID do usuário no Supabase.")

        #Define a janela de contexo, chama a IA para responder
        #e após a resposta adiciona as novas mensagens na janela de contexto
        contexto = db.get_messages(id_usuario)
        logger.info(f"Contexto do DB obtido (mensagens): {len(contexto)}")
        resposta = agent.processar_input(mensagem, prompt, contexto)
        db.adiciona_mensagem(id_usuario, 'user', mensagem)
        db.adiciona_mensagem(id_usuario, 'assistant', resposta)        

        #Faz o envio da mensagem e manda log de confirmação
        evo_connector.enviar_resposta(numero, resposta)  
        logger.info("Ciclo de webhook completo. Mensagens salvas e resposta enviada.")
        return {"status": "ok", "message": "Resposta enviada."}
    except json.JSONDecodeError:
        logger.warning("Corpo da requisição inválido (JSON esperado).")
        raise HTTPException(status_code=400, detail="Corpo da requisição inválido (JSON esperado).")
    except Exception as e:
        logger.error(f"Erro na camada principal do Webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")
#--------------------------------------------------------------------------------------------------------------------#
#Difine os paramentros para o uso do uvicorn
if __name__ == "__main__":
    logger.info("Iniciando o servidor Uvicorn...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
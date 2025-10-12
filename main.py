#5511940804809
import json
import uvicorn
import logging
from data.apis import ope
from negocio.servico import a_instrucoes
from negocio.servico.agente import Agente
from negocio.servico.evolution import EvoConnection 
from fastapi import FastAPI, Request, HTTPException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

agente_ronaldo = Agente(ope.get_key())

try:
    evo_connector = EvoConnection()
except Exception as e:
    logger.error(f"Erro ao inicializar EvoConnection: {e}")
    exit()

app = FastAPI()
@app.get("/conf")
def read_root():
    return {"status": "ok", "message": "requisição recebida"}

@app.post("/webhook/message-upsert/messages-upsert")
async def evolution_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(data)
        
        process_data = await evo_connector.processar_webhook(data)
        
        if process_data.get('status') == 'ok':
            logger.info(process_data.get('Numero'))
            return process_data
        
        prompt = a_instrucoes.escolhe_prompt(process_data.get('Numero'))
        resposta = agente_ronaldo.processar_input(process_data.get('Mensagem'),prompt)
        evo_connector.enviar_resposta(process_data.get('Numero'),resposta)  
        
        return {"status": "ok", "message": "Resposta enviada."}
    except json.JSONDecodeError:
        logger.warning("Corpo da requisição inválido (JSON esperado).")
        raise HTTPException(status_code=400, detail="Corpo da requisição inválido (JSON esperado).")
    except Exception as e:
        logger.error(f"Erro na camada principal do Webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")


if __name__ == "__main__":
    logger.info("Iniciando o servidor Uvicorn...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
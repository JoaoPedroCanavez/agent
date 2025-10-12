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
from fastapi import FastAPI, Request, HTTPException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

agente_ronaldo = Agente(ope.get_key())
db = Banco()

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
        process_data = await evo_connector.processar_webhook(data)
        
        if process_data.get('status') == 'ok':
            logger.info(process_data.get('message'))
            return process_data
        
        mensagem = process_data.get('Mensagem')
        numero = process_data.get('Numero')
        prompt = a_instrucoes.escolhe_prompt(numero)
        
        # 1. Busca/Cria o ID do usuário (base para o contexto)
        id_usuario = db.busca_id_por_numero(numero)
        if id_usuario is None:
             raise Exception("Falha ao obter ou criar ID do usuário no Supabase.")

        # 2. Obtém o contexto de mensagens para o ID
        contexto = db.get_messages(id_usuario)
        logger.info(f"Contexto do DB obtido (mensagens): {len(contexto)}")

        # 3. Processa a resposta da IA (passando o contexto corrigido)
        resposta = agente_ronaldo.processar_input(mensagem, prompt, contexto)
        
        # 4. Salva as novas mensagens no DB (ordem importa: USER, depois ASSISTANT)
        db.adiciona_mensagem(id_usuario, 'user', mensagem)
        db.adiciona_mensagem(id_usuario, 'assistant', resposta)        
        
        # 5. Envia a resposta final
        evo_connector.enviar_resposta(numero, resposta)  

        logger.info("Ciclo de webhook completo. Mensagens salvas e resposta enviada.")
        
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
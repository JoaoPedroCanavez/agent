#5511940804809
import os
import json
import uvicorn
from dotenv import load_dotenv
from negocio.servico.agente import Agente
from negocio.servico.evolution import EvoConnection 
from fastapi import FastAPI, Request, HTTPException

agente_ronaldo = Agente()

try:
    evo_connector = EvoConnection()
except Exception as e:
    print(f"Erro ao inicializar EvoConnection: {e}")
    exit()

app = FastAPI()
@app.get("/conf")
def read_root():
    return {"status": "ok", "message": "requisição recebida"}

@app.post("/webhook")
async def evolution_webhook(request: Request):
    try:
        data = await request.json()
        data = await evo_connector.processar_webhook(data)
        resposta = agente_ronaldo.processar_input(data.get('Mensagem'))
        evo_connector.enviar_resposta(data.get('Numero'),resposta)  
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Corpo da requisição inválido (JSON esperado).")
    except Exception as e:
        print(f"Erro na camada principal do Webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
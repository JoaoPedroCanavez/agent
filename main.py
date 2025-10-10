#5511940804809
import os
import json
import uvicorn
from dotenv import load_dotenv
from negocio.servico.agente import Agente
from data.apis.evolution import EvoConnection 
from fastapi import FastAPI, Request, HTTPException

load_dotenv()

EVO_URL = os.getenv("evoURL")
EVO_INSTANCIA = os.getenv("evoIns")
EVO_TOKEN = os.getenv("evoToken")

agente_ronaldo = Agente()

try:
    evo_connector = EvoConnection(
        evoURL=EVO_URL,
        evoIns=EVO_INSTANCIA,
        evoToken=EVO_TOKEN,
        agente_instancia=agente_ronaldo
    )
except Exception as e:
    print(f"Erro ao inicializar EvoConnection: {e}")
    exit()

app = FastAPI()
@app.get("/conf")
def read_root():
    return {"status": "ok", "message": "Agente Evolution está no ar."}

@app.post("/webhook")
async def evolution_webhook(request: Request):
    try:
        data = await request.json()
        
        # Chama o método de processamento que você criou na classe EvoConnection
        return await evo_connector.processar_webhook(data)
    
    except json.JSONDecodeError:
        # Erro se o corpo da requisição não for um JSON válido
        raise HTTPException(status_code=400, detail="Corpo da requisição inválido (JSON esperado).")
    except Exception as e:
        # Erro genérico
        print(f"Erro na camada principal do Webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")


if __name__ == "__main__":
    # Comando padrão para rodar o FastAPI na porta 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
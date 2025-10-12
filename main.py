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

try:
    agente_ronaldo = Agente(ope.get_key())
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
        
        mensagem_tipo = process_data.get('Tipo')
        mensagem_conteudo = process_data.get('Conteudo')
        numero = process_data.get('Numero')
        prompt = a_instrucoes.escolhe_prompt(numero)

        id_usuario = db.busca_id_por_numero(numero)
        if id_usuario is None:
             logger.error("Falha ao obter ou criar ID do usuário no Supabase.")
             return {"status": "error", "message": "Falha na base de dados."}
        
        if mensagem_tipo == 'text':
            usr_input_para_ia = mensagem_conteudo
            
        elif mensagem_tipo == 'audio':
            instrucao = mensagem_conteudo.get('instrucao')
            usr_input_para_ia = f"Áudio recebido (URL: {mensagem_conteudo.get('url')}). Usuário disse: [TRANSCRIÇÃO DO WHISPER]. Responda com base na transcrição."

        elif mensagem_tipo in ('image', 'document'):
            legenda_instrucao = mensagem_conteudo.get('caption')
            
            if mensagem_tipo == 'image':
                usr_input_para_ia = f"IMAGEM recebida (URL: {mensagem_conteudo.get('url')}). INSTRUÇÃO: {legenda_instrucao}"
            elif mensagem_tipo == 'document':
                usr_input_para_ia = f"DOCUMENTO recebido ({mensagem_conteudo.get('fileName')}, URL: {mensagem_conteudo.get('url')}). INSTRUÇÃO: {legenda_instrucao}"        
        else:
            logger.warning(f"Tipo de mensagem desconhecido: {mensagem_tipo}")
            return {"status": "ok", "message": "Tipo de mensagem não processável."}

        contexto = db.get_messages(id_usuario)
        resposta = agente_ronaldo.processar_input(usr_input_para_ia, prompt, contexto) 
        db.adiciona_mensagem(id_usuario, 'user', usr_input_para_ia) 
        db.adiciona_mensagem(id_usuario, 'assistant', resposta)         
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
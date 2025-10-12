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

try:
    processador_midia = ProcessadorDeMidia(agente_ronaldo.client) 
except Exception as e:
    logger.error(f"Erro ao inicializar ProcessadorDeMidia: {e}")
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

        # 1. Lógica de Processamento de Mídia
        if mensagem_tipo == 'text':
            usr_input_para_ia = mensagem_conteudo
            
        elif mensagem_tipo == 'audio':
            instrucao = mensagem_conteudo.get('instrucao') # 'transcreva este áudio'
            url = mensagem_conteudo.get('url')
            # CHAMA O PROCESSADOR DE MÍDIA
            usr_input_para_ia = processador_midia.processar_audio(url)
            
        elif mensagem_tipo == 'image':
            instrucao = mensagem_conteudo.get('caption')
            url = mensagem_conteudo.get('url')
            # CHAMA O PROCESSADOR DE MÍDIA (Simulação Vision)
            usr_input_para_ia = processador_midia.processar_imagem(url, instrucao)
            
        elif mensagem_tipo == 'document':
            instrucao = mensagem_conteudo.get('caption')
            url = mensagem_conteudo.get('url')
            nome = mensagem_conteudo.get('fileName')
            usr_input_para_ia = processador_midia.processar_documento(url, nome, instrucao)
        
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
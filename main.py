import json
import uvicorn
import logging
import sys # Import adicionado para direcionar logs
from data.apis import ope
from negocio.servico.db import Banco
from negocio.servico import a_instrucoes
from negocio.servico.agente import Agente
from negocio.servico.tratamento_mensagens import TratamentoMsg 
from negocio.servico.processador_midia import ProcessadorDeMidia
from fastapi import FastAPI, Request, HTTPException
#--------------------------------------------------------------------------------------------------------------------#
# CONFIGURAÇÃO DE LOGGING: Direciona explicitamente para a saída padrão
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout # Garante que os logs da aplicação sejam exibidos
)
logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
# Fazendo a chamada das classes criadas para aplicação
try:
    logger.info("Inicializando Agente (OpenAI)...")
    agent = Agente(ope.get_key())
except Exception as e:
    logger.error(f"Erro ao inicializar Agente (OpenAI): {e}")
    exit()
try:
    logger.info("Inicializando Banco de Dados (Supabase)...")
    db = Banco()
except Exception as e:
    logger.error(f"Erro ao inicializar Banco (Supabase): {e}")
    exit()
try:
    logger.info("Inicializando Conector de Mensagens (TratamentoMsg)...")
    connector = TratamentoMsg()
except Exception as e:
    logger.error(f"Erro ao inicializar Conector de Mensagens: {e}")
    exit()
try:
    logger.info("Inicializando Processador de Mídia...")
    processador_midia = ProcessadorDeMidia(ope.get_key()) 
except Exception as e:
    logger.error(f"Erro ao inicializar Processador de Mídia: {e}")
    exit()
logger.info("Inicialização de serviços concluída.")
#--------------------------------------------------------------------------------------------------------------------#
app = FastAPI()
@app.post("/messages-upsert")
async def msg_recebida_webhook(request: Request):
    try:
        logger.info("Webhook recebido no /messages-upsert. Processando...")
        data = await request.json()
        process_data = await connector.processar_webhook(data, processador_midia)

        if process_data.get('status') == 'ok':
            logger.info(process_data.get('message'))
            return process_data

        mensagem = process_data.get('Mensagem') 
        numero = process_data.get('Numero')
        prompt = a_instrucoes.escolhe_prompt(numero)

        if isinstance(mensagem, dict) and 'message' in mensagem:
            mensagem_para_agente = mensagem.get('message', 'Mensagem vazia')
        else:
            mensagem_para_agente = mensagem

        id_usuario = db.busca_id_por_numero(numero)

        contexto = db.get_messages(id_usuario)
        logger.info(f"Contexto do DB obtido (mensagens): {len(contexto)}")
        
        resposta = agent.processar_input(mensagem_para_agente, prompt, contexto)
        
        if isinstance(mensagem_para_agente, str):
            db.adiciona_mensagem(id_usuario, 'user', mensagem_para_agente)
        else:
            prompt_de_interpretacao = mensagem_para_agente[0]['text']if isinstance(mensagem_para_agente, list) and mensagem_para_agente else "Mídia enviada"
            db.adiciona_mensagem(id_usuario, 'user', prompt_de_interpretacao)
        
        db.adiciona_mensagem(id_usuario, 'assistant', resposta)         

        connector.enviar_resposta(numero, resposta)  
        logger.info("Ciclo de webhook completo. Mensagens salvas e resposta enviada.")
        return {"status": "ok", "message": "Resposta enviada."}
    except json.JSONDecodeError:
        logger.warning("Corpo da requisição inválido (JSON esperado).")
        raise HTTPException(status_code=400, detail="Corpo da requisição inválido (JSON esperado).")
    except Exception as e:
        logger.error(f"Erro na camada principal do Webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")
#--------------------------------------------------------------------------------------------------------------------#
if __name__ == "__main__":
    logger.info("Iniciando o servidor Uvicorn...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

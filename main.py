import json
import uvicorn
import logging
import sys # Import adicionado para direcionar logs
from config import ope
from data.repository.db import Banco
from services.instructions_prompts import a_instrucoes
from services.agent_service import Agente
from controllers.webhook_controller import TratamentoMsg 
from services.media_processor import ProcessadorDeMidia
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

        # A variável 'mensagem' já está formatada corretamente pelo processador_midia
        # (string para texto, list para multimodal). Não é mais necessário o if/else
        # complexo aqui.
        mensagem_para_agente = mensagem
        
        id_usuario = db.busca_id_por_numero(numero)

        contexto = db.get_messages(id_usuario)
        logger.info(f"Contexto do DB obtido (mensagens): {len(contexto)}")
        
        # O agente processa a string ou a lista multimodal
        resposta = agent.processar_input(mensagem_para_agente, prompt, contexto)
        
        # Lógica de salvar no DB
        if isinstance(mensagem_para_agente, str):
            db.adiciona_mensagem(id_usuario, 'user', mensagem_para_agente)
        else:
            # Para mídia (lista), salva apenas o prompt de interpretação no DB
            prompt_de_interpretacao = mensagem_para_agente[0]['text'] if isinstance(mensagem_para_agente, list) and mensagem_para_agente else "Mídia enviada para interpretação"
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
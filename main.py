import json
import uvicorn
import logging
import sys
from config import ope
from data.repository.context_repository import Banco
from services.sys_prompts import escolhe_prompt
from services.agent_service import Agente
from controllers.webhook_controller import TratamentoMsg 
from services.media_processor import ProcessadorDeMidia
from fastapi import FastAPI, Request, HTTPException
from typing import Dict, Union, Any, List

#------------------- configurando logs -------------------#


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
app = FastAPI()

#------------------- Inicializando a classe main -------------------#
class Main:
#------------------- Instanciando as classes com as regras do negocio -------------------#
    
    
    _agent = Agente
    _db = Banco
    _connector = TratamentoMsg
    _processador_midia = ProcessadorDeMidia
    


#--------------------------------------------------------------------------------------------------------------------#


    def __init__(self):
        try:
            logger.info("Inicializando Agente (OpenAI)...")
            self._agent = Agente(ope.get_key())
        except Exception as e:
            logger.error(f"Erro ao inicializar Agente (OpenAI): {e}")
            exit()
        try:
            logger.info("Inicializando Banco de Dados (Supabase)...")
            self._db = Banco()
        except Exception as e:
            logger.error(f"Erro ao inicializar Banco (Supabase): {e}")
            exit()
        try:
            logger.info("Inicializando Conector de Mensagens (TratamentoMsg)...")
            self._connector = TratamentoMsg()
        except Exception as e:
            logger.error(f"Erro ao inicializar Conector de Mensagens: {e}")
            exit()
        try:
            logger.info("Inicializando Processador de Mídia...")
            self._processador_midia = ProcessadorDeMidia(ope.get_key()) 
        except Exception as e:
            logger.error(f"Erro ao inicializar Processador de Mídia: {e}")
            exit()
        logger.info("Inicialização de serviços concluída.")      


#--------------------------------------------------------------------------------------------------------------------#


    def output_gen(self,gen_payload: list[dict[str]]) -> list[dict[str]]:
        prompt = escolhe_prompt(gen_payload.get('Numero',{}))
        id_usuario = self._db.busca_id_por_numero(gen_payload.get('Numero',{}))
        contexto = self._db.get_messages(id_usuario)
        logger.info(f"Contexto do DB obtido (mensagens): {len(contexto)}")
        gen_payload.update({'output_mensagem':(self._agent.gerar_payload(gen_payload.get('Mensagem',{}), prompt, contexto))})
        gen_payload.update({'id_usuario':id_usuario}) 
        return gen_payload


#--------------------------------------------------------------------------------------------------------------------#


    def cntx_save(self,gen_payload: List[dict[str]]):
        self._db.adiciona_mensagem(gen_payload.get('id_usuario'), 
                             'user', 
                             gen_payload.get('Mensagem'))
        self._db.adiciona_mensagem(gen_payload.get('id_usuario'), 
                             'assistant', 
                             gen_payload.get('output_mensagem'))        
        

#------------------- Endpoint que faz a recepção dos dados enviados do whatsapp -------------------#

    
        


#--------------------------------------------------------------------------------------------------------------------#


    def main():
        logger.info("Iniciando o servidor Uvicorn...")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
        
    

#--------------------------------------------------------------------------------------------------------------------#


cm = Main()

@app.post("/messages-upsert")
async def msg_recebida_webhook(request: Request):
    logger.info("Webhook recebido no /messages-upsert. Processando...")
    data = await request.json()
    try:
        process_data = await cm._connector.processar_webhook(data, cm._processador_midia)
        if process_data.get('status',{}) == 'ok':
            logger.info(process_data.get('message'))
        
    except json.JSONDecodeError:
        logger.warning("Corpo da requisição inválido (JSON esperado).")
        raise HTTPException(status_code=400, detail="Corpo da requisição inválido (JSON esperado).") 
    except Exception as e:
        logger.error(f"Erro na camada principal do Webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")
    
    verified_payload = cm.output_gen(process_data)
    cm.cntx_save(verified_payload)
    cm._connector.enviar_resposta(verified_payload.get('Numero'), 
                                        verified_payload.get('output_mensagem'))  
    logger.info("Ciclo de webhook completo. Mensagens salvas e resposta enviada.")
    return {"status": "ok", "message": "Resposta enviada."}

if __name__ == "__main__":
    cm.main()
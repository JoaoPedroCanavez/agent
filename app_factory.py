import logging
import tempfile
import json
import os
import asyncio
from fastapi import FastAPI
from data.repository.context_repository import Banco
from services.sys_prompts import escolhe_prompt
from services.agent_service import Agente
from controllers.webhook_controller import TratamentoMsg 
from services.media_processor import ProcessadorDeMidia
from services.temp_media_manager import GerenciadorDeMidiaTemporaria
from config import ope
from typing import Dict, Any, List, Tuple 

logger = logging.getLogger(__name__)


class ApplicationCore:
    """Núcleo da Aplicação: Gerencia a inicialização e orquestra as regras de negócio."""
    
    _agent: Agente
    _db: Banco
    _connector: TratamentoMsg
    _processador_midia: ProcessadorDeMidia
    _midia_temp_gerenciador: GerenciadorDeMidiaTemporaria
    
    TEMP_MEDIA_DIR: str

    def __init__(self):
        self.TEMP_MEDIA_DIR = tempfile.mkdtemp(prefix='whatsapp_media_')
        logger.info(f"Diretório temporário de mídia criado: {self.TEMP_MEDIA_DIR}")
        
        try:
            self._agent = Agente(ope.get_key())
            self._db = Banco()
            self._connector = TratamentoMsg()
            self._processador_midia = ProcessadorDeMidia(ope.get_key(), self.TEMP_MEDIA_DIR) 
            self._midia_temp_gerenciador = GerenciadorDeMidiaTemporaria(self.TEMP_MEDIA_DIR)
            logger.info("Inicialização de serviços concluída.")  
        except Exception as e:
            logger.error(f"Erro Crítico na Inicialização do Core: {e}")
            raise RuntimeError("Falha ao iniciar os serviços essenciais.") from e

    async def process_and_respond(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orquestra o ciclo completo: processamento, geração de resposta, salvamento 
        de contexto e envio da resposta.
        """

        process_data = await self._connector.processar_webhook(data, self._processador_midia)

        if process_data.get('status', {}) == 'ok': 
            return process_data 

        verified_payload = await self._generate_agent_output(process_data)
        
        await self._save_context(verified_payload)
        
        await asyncio.to_thread(
            self._connector.enviar_resposta,
            verified_payload.get('Numero'), 
            verified_payload.get('output_mensagem')
        )
        
        return {"status": "ok", "message": "Resposta enviada com sucesso."}

    async def _generate_agent_output(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Lógica para gerar a resposta do Agente de IA. (Agora assíncrona)"""
        numero = process_data.get('Numero')

        texto_usuario = process_data.get('Mensagem') 
        
        user_id = await asyncio.to_thread(self._db.busca_id_por_numero, numero)
        instrucoes = escolhe_prompt(numero)
        contexto = await asyncio.to_thread(self._db.get_messages, user_id) 

        output_mensagem = await asyncio.to_thread(
            self._agent.gerar_payload,
            input_usuario=texto_usuario,
            instrucoes=instrucoes,
            contexto=contexto
        )
        
        process_data['output_mensagem'] = output_mensagem
        process_data['user_id'] = user_id
        
        return process_data

    async def _save_context(self, verified_payload: Dict[str, Any]):
        """Salva a mensagem do usuário e a resposta do Agente. (Agora assíncrona)"""
        user_id = verified_payload.get('user_id')
        user_msg_content = verified_payload.get('Mensagem')
        agent_msg = verified_payload.get('output_mensagem')

        if isinstance(user_msg_content, list):
            user_msg_str = " ".join([
                item.get('text', '') or item.get('url', 'MÍDIA') 
                for item in user_msg_content
            ])
        else:
            user_msg_str = user_msg_content

        await asyncio.to_thread(self._db.adiciona_mensagem, user_id, 'user', user_msg_str)
        await asyncio.to_thread(self._db.adiciona_mensagem, user_id, 'assistant', agent_msg)
    
    def handle_media_serve(self, filename: str):
        """Expõe a função do gerenciador de mídia temporária."""
        return self._midia_temp_gerenciador.serve_file(filename)

def create_app() -> Tuple[FastAPI, ApplicationCore]: 
    """Cria a instância FastAPI e o núcleo da aplicação."""
    core = ApplicationCore()
    app = FastAPI()

    from api_router import APIRouter 
    APIRouter(app, core)
    
    return app, core

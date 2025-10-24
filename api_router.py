import json
import logging
from fastapi import FastAPI, Request, HTTPException
from app_factory import ApplicationCore

logger = logging.getLogger(__name__)

class APIRouter:
    
    def __init__(self, app_instance: FastAPI, core_instance: ApplicationCore):
        self.app = app_instance
        self.core = core_instance
        self._register_routes()

    def _register_routes(self):
        @self.app.post("/messages-upsert")
        async def msg_recebida_webhook_route(request: Request):
            try:
                data = await request.json()
            except json.JSONDecodeError:
                logger.warning("Corpo da requisição inválido (JSON esperado).")
                raise HTTPException(status_code=400, detail="Corpo da requisição inválido.") 
            
            try:
                return await self.core.process_and_respond(data) 
            
            except Exception as e:
                logger.error(f"Erro na camada de Orquestração: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Erro interno do servidor.")

        @self.app.get("/media-serve/{filename}")
        async def serve_temp_media_route(filename: str):
            """Endpoint para servir arquivos de mídia temporários descriptografados."""
            return self.core.handle_media_serve(filename) 

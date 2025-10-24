# services/temp_media_manager.py

import os
import logging
from fastapi.responses import FileResponse
from fastapi import HTTPException
from starlette.background import BackgroundTask # NOVO IMPORT

logger = logging.getLogger(__name__)

# Função auxiliar para deletar o arquivo no background
def _cleanup_file(file_path: str):
    """Função síncrona que deleta o arquivo após a resposta ser enviada."""
    try:
        os.remove(file_path)
        logger.info(f"Arquivo temporário deletado com sucesso: {file_path}")
    except Exception as e:
        logger.error(f"Erro ao deletar arquivo temporário {file_path}: {e}")


class GerenciadorDeMidiaTemporaria:
    """Gerencia o serviço e a limpeza dos arquivos de mídia temporários."""
    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        
    def serve_file(self, filename: str):
        """Serve o arquivo temporário e agenda sua exclusão."""
        file_path = os.path.join(self.temp_dir, filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"Tentativa de acesso a arquivo não encontrado: {filename}")
            raise HTTPException(status_code=404, detail="Mídia temporária não encontrada ou expirada.")

        # Determina o tipo MIME
        mime_type = 'application/octet-stream'
        if filename.endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        elif filename.endswith('.png'):
            mime_type = 'image/png'
        elif filename.endswith('.pdf'):
            mime_type = 'application/pdf'
        
        # 1. Cria a tarefa de background com a função de limpeza
        cleanup_task = BackgroundTask(_cleanup_file, file_path)
        
        # 2. Retorna o FileResponse, anexando a tarefa de background
        response = FileResponse(
            path=file_path, 
            media_type=mime_type, 
            filename=filename,
            background=cleanup_task # ATRIBUI A TAREFA AQUI
        )
        logger.info(f"Servindo arquivo temporário: {filename}")
        
        return response

import requests
import logging
import io 
from openai import OpenAI
import PyPDF2

logger = logging.getLogger(__name__)

class ProcessadorDeMidia:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client

    def baixar_midia(self, url: str) -> bytes | None:
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            logger.info(f"Download da mídia iniciado: {url}")
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Falha ao baixar mídia da URL {url}: {e}")
            return None

    def processar_audio(self, media_url: str) -> str:     
        audio_content = self.baixar_midia(media_url)
        if not audio_content:
            return "Falha na transcrição: não foi possível baixar o arquivo de áudio."

        try:
            audio_file = io.BytesIO(audio_content)
            audio_file.name = "audio_temp.mp3" 
            
            transcricao = self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            
            texto_transcrito = transcricao.text
            logger.info("Transcrição do áudio bem-sucedida.")
            return f"TRANSCRIÇÃO DO ÁUDIO: {texto_transcrito}"
            
        except Exception as e:
            logger.error(f"Falha na API Whisper: {e}")
            return "Falha na transcrição: erro ao processar áudio com a IA."


    def processar_imagem(self, media_url: str, instrucao: str) -> str:
        try:
            logger.info(f"Imagem enviada para análise Vision. URL: {media_url}")
            return f"IMAGEM RECEBIDA (URL: {media_url}). TAREFA: {instrucao}"

        except Exception as e:
            logger.error(f"Falha na API Vision (simulada): {e}")
            return "Falha na análise da imagem: erro na comunicação com a IA."


    def processar_documento(self, media_url: str, nome_arquivo: str, instrucao: str) -> str:        
        document_content = self.baixar_midia(media_url)
        if not document_content:
            return f"Falha na extração de texto: não foi possível baixar o documento '{nome_arquivo}'."
        
        if nome_arquivo.lower().endswith('.pdf'):
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(document_content))  
                texto_completo = ""
                for page in reader.pages:
                    texto_completo += page.extract_text() or ""
                texto_limitado = texto_completo[:1500] 
                logger.info(f"Texto extraído do documento (limite de 1500 caracteres).")
                
                return f"DOCUMENTO TEXTO: '{texto_limitado}'. INSTRUÇÃO: {instrucao}"
                
            except Exception as e:
                logger.error(f"Falha na extração de texto do PDF: {e}")
                return "Falha na extração de texto: erro ao ler o PDF."
        
        else:
            return "Falha na extração: Formato de documento não suportado (apenas PDF é implementado)."
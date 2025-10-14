import requests
import logging
import io 
from openai import OpenAI
import PyPDF2
from pydub import AudioSegment
from typing import List, Dict, Union

logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
class ProcessadorDeMidia:
#--------------------------------------------------------------------------------------------------------------------#
    def __init__(self, key: str): # Corrigida a tipagem da chave, se ainda estiver 'key=str'
        self.client =  OpenAI(api_key=key)
        self.conversor = ConversorDeFormatos()
#--------------------------------------------------------------------------------------------------------------------#
    def _baixar_midia(self, media_url: str, file_extension: str) -> io.BytesIO | None:
        try:
            response = requests.get(media_url, stream=True, timeout=30)
            response.raise_for_status()
            media_buffer = io.BytesIO(response.content)
            media_buffer.name = f"arquivo_temp.{file_extension}"  
            logger.info(f"Download da mídia concluído. Tipo: {file_extension}. Tamanho: {len(response.content)} bytes.")
            return media_buffer
        except requests.exceptions.RequestException as e:
            logger.error(f"Falha ao baixar mídia da URL {media_url}: {e}")
            return None
#--------------------------------------------------------------------------------------------------------------------#
    def verfica_tipo(self, mensagem: dict) -> str | None:
        try:
            texto_simples = mensagem.get('conversation') or \
                mensagem.get('extendedTextMessage', {}).get('text')
            if texto_simples:
                return texto_simples
            elif mensagem.get('audioMessage'):
                url_audio = mensagem.get('audioMessage').get('url')
                return self.transcricao_audio(url_audio)
            return None 
        except Exception as e:
            logger.error(f"Erro no Processamento de midia: {e}")
            return None
#--------------------------------------------------------------------------------------------------------------------#
    def transcricao_audio(self, audio_url: str) -> str:
        arq_audio_buffer_ogg = self._baixar_midia(audio_url, "ogg") 
        if arq_audio_buffer_ogg is None:
            return "Erro: Não foi possível baixar o arquivo de áudio."
        mp3_buffer = self.conversor.converter_audio_para_mp3(arq_audio_buffer_ogg, "ogg")    
        if mp3_buffer is None:
             return "Erro: Falha ao converter áudio para o formato MP3."
        try:
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=mp3_buffer, 
                response_format="text"
            )
            logger.info("Áudio transcrito com sucesso.")
            return transcription.text
            
        except Exception as e:
            logger.error(f"Erro na API de transcrição Whisper: {e}", exc_info=True)
            return "Erro: Falha na comunicação com a API de Transcrição."
#-----------------/-------------------------/-----------------------/-----------------------------/------------------#        






#-----------------/-------------------------/-----------------------/-----------------------------/------------------# 
class ConversorDeFormatos:
#--------------------------------------------------------------------------------------------------------------------#
    def converter_audio_para_mp3(self, audio_buffer: io.BytesIO, input_format: str) -> io.BytesIO | None:
        try:
            audio_buffer.seek(0)
            audio = AudioSegment.from_file(audio_buffer, format=input_format)
            mp3_buffer = io.BytesIO()
            audio.export(mp3_buffer, format="mp3") 
            mp3_buffer.seek(0)
            mp3_buffer.name = "audio_transcodificado.mp3"
            logger.info(f"Conversão de {input_format} para MP3 concluída.")
            return mp3_buffer
        except Exception as e:
            logger.error(f"Falha na transcodificação (pydub/FFmpeg): {e}", exc_info=True)
            return None
#--------------------------------------------------------------------------------------------------------------------#
    def converter_arquivo_para_pdf(self, text_content: str) -> io.BytesIO:
        pass
import io
import ffmpeg
import PyPDF2
import logging 
import requests
from openai import OpenAI
from typing import List, Dict, Union
logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
class ProcessadorDeMidia:
#--------------------------------------------------------------------------------------------------------------------#
    def __init__(self, key: str):
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
    def verfica_tipo(self, mensagem: dict):
        try:
            texto_simples = mensagem.get('conversation') or \
                mensagem.get('extendedTextMessage', {}).get('text')
            if texto_simples:
                return texto_simples
            elif mensagem.get('audioMessage'):
                    url_audio = mensagem.get('audioMessage').get('url')
                    return self.transcricao_audio(url_audio)
            else:
                #no momento do desenvolvimento evolution não funciona
                #ver qual é o data que vem com imagem sem mensage 
                # e com mensagem e fazer logica para tratar
                if mensagem.get('imageMessage'):
                    url_image = mensagem.get('imageMessage').get('url')
                    return [{"type": "input_text","text": "interprete a imagem enviada"},
                            {"type": "input_image","image_url": url_image}]
                elif mensagem.get('pdfMessage'):
                    url_pdf = mensagem.get('pdfMessage').get('url')
                    return [{"type": "input_text","text": "leia e faça um resumo do pdf enviado"},
                            {"type": "input_image","image_url": url_pdf}]
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
            mp3_buffer = io.BytesIO()
            (
                ffmpeg
                .input('pipe:0', format=input_format)
                .output('pipe:1', format='mp3', acodec='libmp3lame', loglevel="quiet") 
                .run(input=audio_buffer.read(), 
                     capture_stdout=True, 
                     capture_stderr=True, 
                     pipe_stdout=True, 
                     pipe_stderr=True,
                     overwrite_output=True) 
            ) 
            stream = ffmpeg.input('pipe:0', format=input_format)
            out_stream = stream.output('pipe:1', format='mp3', acodec='libmp3lame')
            stdout_data, stderr_data = (
                out_stream
                .run(input=audio_buffer.getvalue(), capture_stdout=True, capture_stderr=True)
            )
            mp3_buffer.write(stdout_data)
            mp3_buffer.seek(0)
            mp3_buffer.name = "audio.mp3"
            logger.info(f"Conversão de {input_format} para MP3 concluída usando ffmpeg-python.")
            return mp3_buffer
        except ffmpeg.Error as e:
            error_details = e.stderr.decode('utf8')
            logger.error(f"Falha na transcodificação (ffmpeg-python): {error_details}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Falha na transcodificação (Erro Genérico): {e}", exc_info=True)
            return None
#--------------------------------------------------------------------------------------------------------------------#
    def converter_arquivo_para_pdf(self, text_content: str) -> io.BytesIO:
        pass
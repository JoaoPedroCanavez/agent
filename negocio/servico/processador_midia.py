import io
import logging 
import requests
from openai import OpenAI, BadRequestError 
from typing import List, Dict, Union, Any
import tempfile 
import os       
import ffmpeg   
# Importa a biblioteca Whisper local
import whisper 
from negocio.servico.decodificador import DecodificadorDeMidiaWhatsApp

logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------------#
class ProcessadorDeMidia:
#--------------------------------------------------------------------------------------------------------------------#
    def __init__(self, key: str):
        # A chave da OpenAI ainda é necessária para o Agente, mas não para a transcrição
        self.client =  OpenAI(api_key=key) 
        self.decodificador = DecodificadorDeMidiaWhatsApp()
        
        # Carrega o modelo Whisper localmente apenas uma vez na inicialização
        logger.info("Carregando modelo Whisper local ('base')...")
        # Você pode alterar 'base' para 'small', 'medium', etc., dependendo da sua GPU/CPU
        self.modelo_whisper_local = whisper.load_model("base") 
        logger.info("Modelo Whisper local carregado com sucesso.")
#--------------------------------------------------------------------------------------------------------------------#
    def _baixar_midia(self, url_midia: str, extensao_arquivo: str) -> io.BytesIO | None:
        try:
            resposta = requests.get(url_midia, stream=True, timeout=30)
            resposta.raise_for_status()
            buffer_midia = io.BytesIO(resposta.content)
            logger.info(f"Download da mídia concluído. Tipo: {extensao_arquivo}. Tamanho: {len(resposta.content)} bytes.")
            return buffer_midia
        except requests.exceptions.RequestException as e:
            logger.error(f"Falha ao baixar mídia da URL {url_midia}: {e}")
            return None
#--------------------------------------------------------------------------------------------------------------------#
    def verificar_tipo_e_processar(self, mensagem: dict) -> Union[str, List[Dict[str, Any]], None]:     
        try:  
            # grava varivel de texto simples
            texto_simples = mensagem.get('conversation') or \
                mensagem.get('extendedTextMessage', {}).get('text')
            #verifica se foi enviado somente texto simples ou acompanha outro tipo de arquivo
            if texto_simples:
                logger.info("Mensagem identificada como TEXTO.")
                return texto_simples
            elif mensagem.get('audioMessage', {}):
                info_audio = mensagem.get('audioMessage', {})
                logger.info("Mensagem identificada como ÁUDIO. Iniciando transcrição.")
                chave_midia = info_audio.get('mediaKey')
                mime_type = info_audio.get('mimetype')
                url_audio = info_audio.get('url')
                return self.transcricao_audio(url_audio, chave_midia, mime_type)
            # 3. Tenta Imagem
            elif mensagem.get('imageMessage'):
                url_image = mensagem.get('imageMessage').get('url')
                logger.info(f"Mensagem identificada como IMAGEM. URL: {url_image[:30]}...")
                return [{"type": "input_text","text": "interprete a imagem enviada"},
                        {"type": "input_image","image_url": url_image}]

            # 4. Tenta PDF (documento)
            elif mensagem.get('pdfMessage'):
                url_pdf = mensagem.get('pdfMessage').get('url')
                logger.info(f"Mensagem identificada como PDF. URL: {url_pdf[:30]}...")
                return [{"type": "input_text","text": "leia e faça um resumo do pdf enviado"},
                        {"type": "input_image","image_url": url_pdf}]
                        
            # 5. Outros tipos de mídia ou não suportado
            logger.info("Mensagem não é texto ou mídia suportada (áudio, imagem, pdf).")
            return None 
            
        except Exception as e:
            logger.error(f"Erro ao verificar e processar o tipo de mensagem: {e}", exc_info=True)
            return None
#--------------------------------------------------------------------------------------------------------------------#
    def transcricao_audio(self, url_audio: str, chave_midia: str, mime_type: str) -> str | None:
        
        extensao_download = "midia_bruta" 
        buffer_criptografado = self._baixar_midia(url_audio, extensao_download) 
        if buffer_criptografado is None:
            return None
        
        temp_caminho_entrada = None
        
        try:
            logger.info("Iniciando descriptografia da mídia (AES/HKDF)...")
            buffer_decodificado = self.decodificador.decodificar_buffer(
                buffer_criptografado=buffer_criptografado,
                chave_midia_base64=chave_midia, 
                mime_type=mime_type
            )
            logger.info("Descriptografia concluída. Conteúdo decodificado em buffer.")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp_ogg:
                buffer_decodificado.seek(0)
                ogg_content = buffer_decodificado.getvalue()
                
                logger.info(f"Salvando OGG decodificado para transcrição local: {len(ogg_content)} bytes.") 
                tmp_ogg.write(ogg_content)
                temp_caminho_entrada = tmp_ogg.name
                tmp_ogg.flush()
            logger.info("Iniciando transcrição local com modelo Whisper...")
            resultado = self.modelo_whisper_local.transcribe(
                temp_caminho_entrada,
                language="pt" 
            )
            
            transcricao = resultado["text"]
            logger.info("Transcrição local bem-sucedida (via Whisper local).")
            return transcricao

        except Exception as e:
            logger.error(f"Erro na transcrição com Whisper local: {e}", exc_info=True)
            return None
            
        finally:
            if temp_caminho_entrada and os.path.exists(temp_caminho_entrada):
                os.remove(temp_caminho_entrada)
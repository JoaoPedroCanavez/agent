import io
import logging 
import requests
from openai import OpenAI
from typing import List, Dict, Union, Any
import tempfile 
import os       
import whisper
import base64
# PIL não é mais estritamente necessária aqui, mas pode ser útil para futuras verificações
from PIL import Image, UnidentifiedImageError 
from services.crypto.whatsapp_decoder import DecodificadorDeMidiaWhatsApp
logger = logging.getLogger(__name__)


#--------------------------------------------------------------------------------------------------------------------#
class ProcessadorDeMidia:
#--------------------------------------------------------------------------------------------------------------------#


    def __init__(self, key: str, temp_media_dir: str):
        self.client =  OpenAI(api_key=key) 
        self.decodificador = DecodificadorDeMidiaWhatsApp()
        self.modelo_whisper_local = whisper.load_model("base") 
        self.TEMP_MEDIA_DIR = temp_media_dir


#--------------------------------------------------------------------------------------------------------------------#


    def _baixar_midia(self, url_midia: str, extensao_arquivo: str) -> io.BytesIO | None:
        try:
            resposta = requests.get(url_midia, stream=True, timeout=15) 
            resposta.raise_for_status()
            buffer_midia = io.BytesIO(resposta.content)
            logger.info(f"Download da mídia concluído. Tipo: {extensao_arquivo}. Tamanho: {len(resposta.content)} bytes.")
            return buffer_midia
        except requests.exceptions.RequestException as e:
            logger.error(f"Falha ao baixar mídia da URL {url_midia}: {e}")
            return None
        

#--------------------------------------------------------------------------------------------------------------------#


    def transcricao_audio(self, url_audio: str, chave_midia: str, mime_type: str) -> str | None:
        extensao_download = "midia_bruta" 
        buffer_criptografado = self._baixar_midia(url_audio, extensao_download)
        if buffer_criptografado is None:
            return None
        
        temp_caminho_entrada = None
        try:
            logger.info("Iniciando descriptografia do áudio (AES/HKDF)...")
            buffer_decodificado = self.decodificador.decodificar_buffer(
                buffer_criptografado=buffer_criptografado,
                chave_midia_base64=chave_midia, 
                mime_type=mime_type
            )
            logger.info("Descriptografia do áudio concluída.")
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


#--------------------------------------------------------------------------------------------------------------------#


    def _processar_criptografia(self, url: str, chave_midia: str, mime_type: str, prompt_text: str | None, tipo: str, conteudo: str) -> List[Dict[str, Any]] | None:
        extensao_download = "midia_bruta" 
        buffer_criptografado = self._baixar_midia(url, extensao_download)
        if buffer_criptografado is None:
            return None
        
        temp_caminho_midia = None

        try:
            logger.info("Iniciando descriptografia da mídia (AES/HKDF)...")
            buffer_decodificado = self.decodificador.decodificar_buffer(
                buffer_criptografado=buffer_criptografado,
                chave_midia_base64=chave_midia, 
                mime_type=mime_type
            )
            logger.info("Descriptografia concluída. Conteúdo decodificado em buffer.")
            buffer_decodificado.seek(0)
            extensao = self.decodificador._EXTENSAO.get(mime_type.split("/")[0], mime_type.split("/")[-1])
            if mime_type == 'application/pdf':
               extensao = 'pdf'
            elif 'image' in mime_type:
                if extensao == 'bin': 
                    extensao = 'jpg' 
            
            nome_arquivo = f"{os.urandom(16).hex()}.{extensao}"
            temp_caminho_midia = os.path.join(self.TEMP_MEDIA_DIR, nome_arquivo)
            
            logger.info(f"Salvando binário descriptografado diretamente como .{extensao}...")

            with open(temp_caminho_midia, 'wb') as f:
                f.write(buffer_decodificado.getvalue())
                 
            logger.info(f"Mídia salva localmente para ser enviada via path: {temp_caminho_midia}")

            payload_final = []
            if prompt_text:
                 payload_final.append({"type": "input_text", "text": prompt_text})
            payload_final.append({"type": "input_file", "file_path" : temp_caminho_midia})
            
            return payload_final

        except Exception as e:
            logger.error(f"Erro ao processar mídia criptografada para arquivo local: {e}", exc_info=True)
            # Limpeza em caso de erro
            if temp_caminho_midia and os.path.exists(temp_caminho_midia):
                os.remove(temp_caminho_midia)
            return None
        

#--------------------------------------------------------------------------------------------------------------------#


    def verificar_tipo_e_processar(self, mensagem: dict) -> Union[str, List[Dict[str, Any]], None]:     
        try:  
            texto_simples = mensagem.get('conversation') or \
                mensagem.get('extendedTextMessage', {}).get('text')
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
            
            elif mensagem.get('imageMessage'):
                tipo = "input_file" 
                conteudo = "file_path" 
                info_img = mensagem.get('imageMessage')
                url_img = info_img.get('url')
                chave_midia = info_img.get('mediaKey')
                mime_type = info_img.get('mimetype')

                texto_acompanhante = info_img.get('caption') 

                if texto_acompanhante:
                    prompt_text = texto_acompanhante
                    logger.info(f"Imagem com caption detectado: '{texto_acompanhante[:50]}...'")
                else:
                    prompt_text = "interprete a imagem enviada"
                    logger.info("Imagem sem caption. Usando prompt padrão.")
                
                logger.info(f"Mensagem identificada como IMAGEM. URL (criptografada): {url_img[:30]}...")

                return self._processar_criptografia(url_img, chave_midia, mime_type, prompt_text, tipo, conteudo)
            elif mensagem.get('documentMessage') and mensagem.get('documentMessage').get('mimetype') == 'application/pdf':
                tipo = "input_file" 
                conteudo = "file_path"
                info_doc = mensagem.get('documentMessage')
                url_doc = info_doc.get('url')
                chave_midia = info_doc.get('mediaKey')
                mime_type = info_doc.get('mimetype')

                texto_acompanhante = info_doc.get('caption')

                if texto_acompanhante:
                    prompt_text = texto_acompanhante
                    logger.info(f"PDF com caption detectado: '{texto_acompanhante[:50]}...'")
                else:
                    prompt_text = "leia e faça um resumo do pdf enviado"
                    logger.info("PDF sem caption. Usando prompt padrão.")
                
                logger.info(f"Mensagem identificada como PDF. URL (criptografada): {url_doc[:30]}...")
                return self._processar_criptografia(url_doc, chave_midia, mime_type, prompt_text, tipo, conteudo)

            else:            

                logger.info("Mensagem não é texto ou mídia suportada (áudio, imagem, pdf).")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao verificar e processar o tipo de mensagem: {e}", exc_info=True)
            return None
        

#--------------------------------------------------------------------------------------------------------------------#

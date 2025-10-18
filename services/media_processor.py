import io
import logging 
import requests
from openai import OpenAI
from typing import List, Dict, Union, Any
import tempfile 
import os       
import whisper # Importa a biblioteca Whisper local
import base64 # Importado para codificação de imagem
from PIL import Image, UnidentifiedImageError # Importado UnidentifiedImageError
from services.crypto.whatsapp_decoder import DecodificadorDeMidiaWhatsApp

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
    def _processar_criptografia(self, url: str, chave_midia: str, mime_type: str, prompt_text: str) -> List[Dict[str, Any]] | None:
        """Baixa, descriptografa e converte mídia (Imagem/PDF) para Base64 (Data URI)."""
        extensao_download = "midia_bruta" 
        buffer_criptografado = self._baixar_midia(url, extensao_download) 
        if buffer_criptografado is None:
            return None
        try:
            logger.info("Iniciando descriptografia da mídia (AES/HKDF)...")
            buffer_decodificado = self.decodificador.decodificar_buffer(
                buffer_criptografado=buffer_criptografado,
                chave_midia_base64=chave_midia, 
                mime_type=mime_type
            )
            logger.info("Descriptografia concluída. Conteúdo decodificado em buffer.")
            buffer_decodificado.seek(0)
            dados_decodificados = buffer_decodificado.getvalue()
            if 'image' in mime_type:
                logger.info(f"Convertendo imagem decodificada (MIME: {mime_type}) para 'image/jpeg' válido.")
                JPEG_START_MARKER = b'\xff\xd8\xff'
                start_index = dados_decodificados.find(JPEG_START_MARKER)
                if start_index == -1:                   
                    start_index = 64
                    logger.warning("Marcador JPEG não encontrado. Assumindo header de 64 bytes (para compatibilidade).")
                else:
                    logger.info(f"Marcador JPEG encontrado no índice: {start_index}. Cortando o header.")
                input_buffer_img = io.BytesIO(dados_decodificados[start_index:])
                try:
                    img = Image.open(input_buffer_img)
                    output_buffer = io.BytesIO()
                    img.save(output_buffer, format="JPEG")
                    dados_para_base64 = output_buffer.getvalue()
                    mime_type = "image/jpeg"
                except UnidentifiedImageError as e:
                    logger.error(f"Falha crítica ao identificar imagem mesmo após busca por header: {e}.", exc_info=True)
                    return None
            else:
                dados_para_base64 = dados_decodificados
            base64_dados = base64.b64encode(dados_para_base64).decode('utf-8')
            data_uri = f"data:{mime_type};base64,{base64_dados}"
            
            logger.info(f"Mídia ({mime_type}) convertida para Base64 (Data URI) para o Agente.")
            return [
                {"type": "input_text", "text": prompt_text},
                {"type": "input_image", "image_url": data_uri} 
            ]

        except Exception as e:
            logger.error(f"Erro ao processar mídia criptografada para Base64: {e}", exc_info=True)
            return None
#--------------------------------------------------------------------------------------------------------------------#
    def verificar_tipo_e_processar(self, mensagem: dict) -> Union[str, List[Dict[str, Any]], None]:     
        try:  
            # 1. Tenta Texto Simples
            texto_simples = mensagem.get('conversation') or \
                mensagem.get('extendedTextMessage', {}).get('text')
            if texto_simples:
                logger.info("Mensagem identificada como TEXTO.")
                return texto_simples
            
            # 2. Tenta Áudio
            elif mensagem.get('audioMessage', {}):
                info_audio = mensagem.get('audioMessage', {})
                logger.info("Mensagem identificada como ÁUDIO. Iniciando transcrição.")
                chave_midia = info_audio.get('mediaKey')
                mime_type = info_audio.get('mimetype')
                url_audio = info_audio.get('url')
                return self.transcricao_audio(url_audio, chave_midia, mime_type)
            
            # 3. Tenta Imagem (Multimodal)
            elif mensagem.get('imageMessage'):
                info_img = mensagem.get('imageMessage')
                url_img = info_img.get('url')
                chave_midia = info_img.get('mediaKey')
                mime_type = info_img.get('mimetype')
                prompt_text = "interprete a imagem enviada"
                
                logger.info(f"Mensagem identificada como IMAGEM. URL (criptografada): {url_img[:30]}...")
                return self._processar_criptografia(url_img, chave_midia, mime_type, prompt_text)

            # 4. Tenta PDF (documentMessage com mimetype PDF)
            elif mensagem.get('documentMessage') and mensagem.get('documentMessage').get('mimetype') == 'application/pdf':
                info_doc = mensagem.get('documentMessage')
                url_doc = info_doc.get('url')
                chave_midia = info_doc.get('mediaKey')
                mime_type = info_doc.get('mimetype')
                prompt_text = "leia e faça um resumo do pdf enviado"
                
                logger.info(f"Mensagem identificada como PDF. URL (criptografada): {url_doc[:30]}...")
                return self._processar_criptografia(url_doc, chave_midia, mime_type, prompt_text)
                        
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

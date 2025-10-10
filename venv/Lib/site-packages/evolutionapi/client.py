import requests
import json
import logging
from typing import Dict, Any, Optional, cast, Union, Tuple
from requests_toolbelt import MultipartEncoder
from .exceptions import EvolutionAuthenticationError, EvolutionNotFoundError, EvolutionAPIError
from .services.instance import InstanceService
from .services.instance_operations import InstanceOperationsService
from .services.message import MessageService
from .services.call import CallService
from .services.chat import ChatService
from .services.label import LabelService
from .services.profile import ProfileService
from .services.group import GroupService
from .services.websocket import WebSocketService, WebSocketManager
from evolutionapi.typing.message_types import (
    MessageData, 
    WebhookEvent,
    EVENT_MESSAGE_UPSERT,
    EVENT_MESSAGE_UPDATE,
    EVENT_MESSAGE_DELETE,
    EVENT_QRCODE_UPDATED,
    EVENT_CONNECTION_UPDATE
)
from evolutionapi.typing.message_handlers import (
    AttributeDict, 
    TypedAttributeDict,
    MessageEventDict,
    MessageWrapper,
    wrap_event_data, 
    wrap_message_data
)

try:
    # Tenta importar os tipos, mas não falha se não estiverem disponíveis
    from .typing import MessageData, MessageUpsertEvent
    HAS_TYPING = True
except ImportError:
    HAS_TYPING = False

logger = logging.getLogger(__name__)

class EvolutionClient:
    """
    Cliente para interagir com a API Evolution.

    Args:
        base_url (str): A URL base do servidor da API Evolution.
        api_token (str): O token de autenticação para acessar a API.
    """

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.instances = InstanceService(self)
        self.instance_operations = InstanceOperationsService(self)
        self.messages = MessageService(self)
        self.calls = CallService(self)
        self.chat = ChatService(self)
        self.label = LabelService(self)
        self.profile = ProfileService(self)
        self.group = GroupService(self)
        self.websocket = WebSocketService(self)
        
    def _get_headers(self, instance_token: str = None):
        return {
            'apikey': instance_token or self.api_token,
            'Content-Type': 'application/json'
        }

    def _get_full_url(self, endpoint):
        return f'{self.base_url}/{endpoint}'

    def _handle_response(self, response):
        if response.status_code == 401:
            raise EvolutionAuthenticationError('Falha na autenticação.')
        elif response.status_code == 404:
            raise EvolutionNotFoundError('Recurso não encontrado.')
        elif response.ok:
            try:
                return response.json()
            except ValueError:
                return response.content
        else:
            error_detail = ''
            try:
                error_detail = f' - {response.json()}'
            except:
                error_detail = f' - {response.text}'
            raise EvolutionAPIError(f'Erro na requisição: {response.status_code}{error_detail}')

    def get(self, endpoint: str, instance_token: str = None):
        """Faz uma requisição GET."""
        url = self._get_full_url(endpoint)
        response = requests.get(url, headers=self._get_headers(instance_token))
        return self._handle_response(response)

    def post(self, endpoint: str, data: dict = None, instance_token: str = None, files: dict = None):
        url = f'{self.base_url}/{endpoint}'
        headers = self._get_headers(instance_token)
        
        if files:
            # Remove o Content-Type do header quando enviando arquivos
            if 'Content-Type' in headers:
                del headers['Content-Type']
            
            # Prepara os campos do multipart
            fields = {}
            
            # Adiciona os campos do data
            for key, value in data.items():
                fields[key] = str(value) if not isinstance(value, (int, float)) else (None, str(value), 'text/plain')
            
            # Adiciona o arquivo
            file_tuple = files['file']
            fields['file'] = (file_tuple[0], file_tuple[1], file_tuple[2])
            
            # Cria o multipart encoder
            multipart = MultipartEncoder(fields=fields)
            headers['Content-Type'] = multipart.content_type
            
            response = requests.post(
                url, 
                headers=headers,
                data=multipart
            )
        else:
            response = requests.post(
                url, 
                headers=headers, 
                json=data
            )
        
        return response.json()

    def put(self, endpoint, data=None):
        """Faz uma requisição PUT."""
        url = self._get_full_url(endpoint)
        response = requests.put(url, headers=self.headers, json=data)
        return self._handle_response(response)

    def delete(self, endpoint: str, instance_token: str = None):
        """Faz uma requisição DELETE."""
        url = self._get_full_url(endpoint)
        response = requests.delete(url, headers=self._get_headers(instance_token))
        return self._handle_response(response)

    def create_websocket(self, instance_id: str, api_token: str, max_retries: int = 5, retry_delay: float = 1.0) -> WebSocketManager:
        """
        Create a WebSocket manager for the specified instance.
        
        Args:
            instance_id (str): The instance ID
            api_token (str): The API token
            max_retries (int): Maximum number of reconnection attempts
            retry_delay (float): Initial delay between attempts in seconds
            
        Returns:
            WebSocketManager: The WebSocket manager instance
        """
        return WebSocketManager(
            base_url=self.base_url,
            instance_id=instance_id,
            api_token=api_token,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

    def convert_message(self, data: Union[Dict[str, Any], MessageData, str]) -> Optional[MessageWrapper]:
        """
        Converte os dados de uma mensagem em um objeto MessageWrapper
        
        Args:
            data: Dados da mensagem (dict, MessageData ou JSON string)
            
        Returns:
            MessageWrapper ou None se não for possível converter
        """
        try:
            # Se for string JSON, converte para dict
            if isinstance(data, str):
                data = json.loads(data)
            
            # Se for um evento completo de webhook, extrai os dados da mensagem
            if isinstance(data, dict) and "event" in data and "data" in data:
                data = data["data"]
            
            # Converte para MessageWrapper para acesso via atributos
            return wrap_message_data(cast(MessageData, data))
        except Exception as e:
            logger.error(f"Erro ao converter mensagem: {e}")
            return None

    def convert_webhook_event(self, data: Union[Dict[str, Any], str]) -> Optional[TypedAttributeDict]:
        """
        Converte os dados de um evento webhook em um objeto TypedAttributeDict
        
        Args:
            data: Dados do evento (dict ou JSON string)
            
        Returns:
            TypedAttributeDict ou None se não for possível converter
        """
        try:
            # Se for string JSON, converte para dict
            if isinstance(data, str):
                data = json.loads(data)
            
            # Converte para TypedAttributeDict para acesso via atributos
            return wrap_event_data(data)
        except Exception as e:
            logger.error(f"Erro ao converter evento webhook: {e}")
            return None

    def get_message_content(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Extrai o conteúdo da mensagem com base no tipo
        
        Args:
            message_data: Dados da mensagem
            
        Returns:
            Conteúdo da mensagem ou None se não for possível extrair
        """
        try:
            if 'message' not in message_data:
                return None
                
            message = message_data['message']
            message_type = message_data.get('messageType', '')
            
            # Texto simples
            if 'conversation' in message:
                return message['conversation']
                
            # Texto estendido
            elif 'extendedTextMessage' in message:
                return message['extendedTextMessage'].get('text', '')
                
            # Imagem
            elif 'imageMessage' in message:
                caption = message['imageMessage'].get('caption', '')
                return f"[Imagem] {caption}"
                
            # Vídeo
            elif 'videoMessage' in message:
                caption = message['videoMessage'].get('caption', '')
                return f"[Vídeo] {caption}"
                
            # Áudio
            elif 'audioMessage' in message:
                seconds = message['audioMessage'].get('seconds', 0)
                return f"[Áudio] {seconds} segundos"
                
            # Sticker
            elif 'stickerMessage' in message:
                return "[Sticker]"
                
            # Documento
            elif 'documentMessage' in message:
                file_name = message['documentMessage'].get('fileName', 'Documento')
                return f"[Documento] {file_name}"
                
            # Localização
            elif 'locationMessage' in message:
                lat = message['locationMessage'].get('degreesLatitude', 0)
                lng = message['locationMessage'].get('degreesLongitude', 0)
                return f"[Localização] Lat: {lat}, Long: {lng}"
                
            # Contato
            elif 'contactMessage' in message:
                name = message['contactMessage'].get('displayName', 'Contato')
                return f"[Contato] {name}"
                
            # Lista de contatos
            elif 'contactsArrayMessage' in message:
                count = len(message['contactsArrayMessage'].get('contacts', []))
                return f"[Contatos] {count} contatos compartilhados"
                
            # Enquete
            elif 'pollCreationMessageV3' in message:
                poll_name = message['pollCreationMessageV3'].get('name', 'Enquete')
                options_count = len(message['pollCreationMessageV3'].get('options', []))
                return f"[Enquete] {poll_name} ({options_count} opções)"
                
            return str(message)
            
        except Exception as e:
            logger.error(f"Erro ao extrair conteúdo da mensagem: {e}")
            return None
            
    def process_message_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa dados de atualização de status de mensagem
        
        Args:
            update_data: Dados do evento messages.update
            
        Returns:
            Dados processados no formato adequado
        """
        # Cria um dicionário com informações relevantes
        result = {
            'remoteJid': update_data.get('remoteJid'),
            'fromMe': update_data.get('fromMe', False),
            'status': update_data.get('status'),
            'messageId': update_data.get('messageId'),
            'keyId': update_data.get('keyId')
        }
        
        if 'participant' in update_data:
            result['participant'] = update_data['participant']
            
        return result
            
    def process_message_delete(self, delete_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa dados de exclusão de mensagem
        
        Args:
            delete_data: Dados do evento messages.delete
            
        Returns:
            Dados processados no formato adequado
        """
        # Já está em um formato simples, só retorna o mesmo
        return delete_data
            
    def process_qrcode_update(self, qrcode_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa dados de atualização de QR code
        
        Args:
            qrcode_data: Dados do evento qrcode.updated
            
        Returns:
            Dados processados com as informações do QR code
        """
        # Se o QR code está aninhado dentro de 'qrcode', extraímos ele
        if 'qrcode' in qrcode_data:
            return qrcode_data['qrcode']
        return qrcode_data

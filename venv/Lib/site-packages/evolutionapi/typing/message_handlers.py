from typing import Dict, Any, Optional, Callable, Union, TypeVar, Generic, cast
import json
import logging

from .message_types import (
    MessageData, 
    TextMessageContent, 
    ImageMessage, 
    VideoMessage,
    AudioMessage,
    StickerMessage,
    DocumentMessage,
    LocationMessage,
    ContactMessage,
    ContactsArrayMessage,
    PollMessage,
    WebhookEvent,
    MessageUpdateData,
    MessageDeleteData,
    QRCodeData,
    EVENT_MESSAGE_UPSERT,
    EVENT_MESSAGE_UPDATE,
    EVENT_MESSAGE_DELETE,
    EVENT_QRCODE_UPDATED,
    EVENT_CONNECTION_UPDATE
)

logger = logging.getLogger(__name__)

def get_message_content(message_data: MessageData) -> Optional[str]:
    """
    Extract message content based on its type
    
    Args:
        message_data: The message data object
        
    Returns:
        The extracted message content or None if not found
    """
    if 'message' not in message_data:
        return None
        
    message = message_data['message']
    message_type = message_data.get('messageType', '')
    
    # Text messages
    if 'conversation' in message:
        return message['conversation']
    
    # Extended text messages
    elif 'extendedTextMessage' in message:
        return message['extendedTextMessage'].get('text', '')
    
    # Image messages
    elif 'imageMessage' in message:
        caption = message['imageMessage'].get('caption', '')
        return f"[Image] {caption}"
    
    # Video messages
    elif 'videoMessage' in message:
        caption = message['videoMessage'].get('caption', '')
        return f"[Video] {caption}"
    
    # Audio messages
    elif 'audioMessage' in message:
        return f"[Audio] {message['audioMessage'].get('seconds', 0)} seconds"
    
    # Sticker messages
    elif 'stickerMessage' in message:
        return f"[Sticker]"
    
    # Document messages
    elif 'documentMessage' in message:
        file_name = message['documentMessage'].get('fileName', 'Document')
        return f"[Document] {file_name}"
    
    # Location messages
    elif 'locationMessage' in message:
        lat = message['locationMessage'].get('degreesLatitude', 0)
        lng = message['locationMessage'].get('degreesLongitude', 0)
        return f"[Location] Lat: {lat}, Long: {lng}"
    
    # Contact messages
    elif 'contactMessage' in message:
        name = message['contactMessage'].get('displayName', 'Contact')
        return f"[Contact] {name}"
    
    # Contacts array messages
    elif 'contactsArrayMessage' in message:
        count = len(message['contactsArrayMessage'].get('contacts', []))
        return f"[Contacts] {count} contacts shared"
    
    # Poll messages
    elif 'pollCreationMessageV3' in message:
        poll_name = message['pollCreationMessageV3'].get('name', 'Poll')
        options_count = len(message['pollCreationMessageV3'].get('options', []))
        return f"[Poll] {poll_name} ({options_count} options)"
    
    return str(message)


def is_text_message(message_data: MessageData) -> bool:
    """Check if the message is a text message"""
    if 'message' not in message_data:
        return False
    return 'conversation' in message_data['message']


def is_image_message(message_data: MessageData) -> bool:
    """Check if the message is an image message"""
    if 'message' not in message_data:
        return False
    return 'imageMessage' in message_data['message']


def is_video_message(message_data: MessageData) -> bool:
    """Check if the message is a video message"""
    if 'message' not in message_data:
        return False
    return 'videoMessage' in message_data['message']


def is_audio_message(message_data: MessageData) -> bool:
    """Check if the message is an audio message"""
    if 'message' not in message_data:
        return False
    return 'audioMessage' in message_data['message']


def is_sticker_message(message_data: MessageData) -> bool:
    """Check if the message is a sticker message"""
    if 'message' not in message_data:
        return False
    return 'stickerMessage' in message_data['message']


def is_document_message(message_data: MessageData) -> bool:
    """Check if the message is a document message"""
    if 'message' not in message_data:
        return False
    return 'documentMessage' in message_data['message']


def is_location_message(message_data: MessageData) -> bool:
    """Check if the message is a location message"""
    if 'message' not in message_data:
        return False
    return 'locationMessage' in message_data['message']


def is_contact_message(message_data: MessageData) -> bool:
    """Check if the message is a contact message"""
    if 'message' not in message_data:
        return False
    return 'contactMessage' in message_data['message']


def is_contacts_array_message(message_data: MessageData) -> bool:
    """Check if the message is a contacts array message"""
    if 'message' not in message_data:
        return False
    return 'contactsArrayMessage' in message_data['message']


def is_poll_message(message_data: MessageData) -> bool:
    """Check if the message is a poll message"""
    if 'message' not in message_data:
        return False
    return 'pollCreationMessageV3' in message_data['message']


MessageHandler = Callable[[MessageData], None]


class MessageRouter:
    """
    Router for handling different types of messages
    """
    def __init__(self):
        self.handlers: Dict[str, MessageHandler] = {}
        self.default_handler: Optional[MessageHandler] = None
    
    def register(self, message_type: str, handler: MessageHandler) -> None:
        """
        Register a handler for a specific message type
        
        Args:
            message_type: The type of message to handle
            handler: The function to handle the message
        """
        self.handlers[message_type] = handler
    
    def set_default_handler(self, handler: MessageHandler) -> None:
        """
        Set a default handler for unhandled message types
        
        Args:
            handler: The function to handle unhandled messages
        """
        self.default_handler = handler
    
    def route(self, message_data: MessageData) -> None:
        """
        Route a message to the appropriate handler
        
        Args:
            message_data: The message data to route
        """
        message_type = message_data.get('messageType', '')
        
        if message_type in self.handlers:
            self.handlers[message_type](message_data)
        elif self.default_handler:
            self.default_handler(message_data)


# Add a class that wraps dictionary data with attribute access
class AttributeDict:
    """
    Wrapper for dictionary data that allows attribute access (data.message) 
    while maintaining compatibility with dictionary access (data["message"]).
    """
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        
    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            value = self._data[name]
            if isinstance(value, dict):
                return AttributeDict(value)
            return value
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
        
    def __getitem__(self, key: str) -> Any:
        return self._data[key]
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
    
    def __contains__(self, key: str) -> bool:
        return key in self._data
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._data})"


# Type-specific attribute dicts for better IDE autocomplete
T = TypeVar('T')

class TypedAttributeDict(AttributeDict, Generic[T]):
    """AttributeDict with type information for IDE autocomplete support"""
    def __init__(self, data: Dict[str, Any], typed_dict_cls: Optional[type] = None):
        super().__init__(data)
        self._typed_dict_cls = typed_dict_cls
        
    @property
    def event(self) -> str:
        """Event type field common to all webhook events"""
        return self._data.get("event", "")
        
    @property
    def instance(self) -> str:
        """Instance ID field common to all webhook events"""
        return self._data.get("instance", "")
        
    @property
    def data(self) -> Any:
        """Event data field common to all webhook events"""
        data_value = self._data.get("data", {})
        if isinstance(data_value, dict):
            return AttributeDict(data_value)
        return data_value
        
    @property
    def destination(self) -> Optional[str]:
        """Webhook destination URL"""
        return self._data.get("destination")
        
    @property
    def date_time(self) -> Optional[str]:
        """Event timestamp"""
        return self._data.get("date_time")
        
    @property
    def server_url(self) -> Optional[str]:
        """Server URL"""
        return self._data.get("server_url")
        
    @property
    def apikey(self) -> Optional[str]:
        """API key"""
        return self._data.get("apikey")


class MessageEventDict(TypedAttributeDict['MessageUpsertEvent']):
    """AttributeDict specifically for message upsert events with IDE autocomplete"""
    @property
    def data(self) -> AttributeDict:
        """Message data with all fields"""
        message_data = self._data.get("data", {})
        return AttributeDict(message_data)


class MessageUpdateEventDict(TypedAttributeDict['MessageUpdateEvent']):
    """AttributeDict specifically for message update events with IDE autocomplete"""
    pass


class MessageDeleteEventDict(TypedAttributeDict['MessageDeleteEvent']):
    """AttributeDict specifically for message delete events with IDE autocomplete"""
    pass


class QRCodeEventDict(TypedAttributeDict['QRCodeEvent']):
    """AttributeDict specifically for QR code events with IDE autocomplete"""
    pass


class ConnectionEventDict(TypedAttributeDict['ConnectionEvent']):
    """AttributeDict specifically for connection events with IDE autocomplete"""
    pass


class MessageWrapper(AttributeDict):
    """Wrapper specifically for message data with typing hints"""
    @property
    def message(self) -> Dict[str, Any]:
        """Message content"""
        return self._data.get("message", {})
        
    @property
    def messageType(self) -> str:
        """Message type"""
        return self._data.get("messageType", "")
        
    @property
    def key(self) -> Dict[str, Any]:
        """Message key containing remoteJid, fromMe, id"""
        return self._data.get("key", {})
        
    @property
    def pushName(self) -> str:
        """Sender's name"""
        return self._data.get("pushName", "")
        
    @property
    def status(self) -> str:
        """Message status"""
        return self._data.get("status", "")
        
    @property
    def messageTimestamp(self) -> int:
        """Message timestamp"""
        return self._data.get("messageTimestamp", 0)


def wrap_event_data(event_data: Dict[str, Any]) -> TypedAttributeDict:
    """
    Wraps webhook event data in typed AttributeDict for attribute access with IDE support
    
    Args:
        event_data: Raw webhook event data
        
    Returns:
        TypedAttributeDict wrapper for the data
    """
    event_type = event_data.get("event", "")
    
    if event_type == EVENT_MESSAGE_UPSERT:
        return MessageEventDict(event_data)
    elif event_type == EVENT_MESSAGE_UPDATE:
        return MessageUpdateEventDict(event_data)
    elif event_type == EVENT_MESSAGE_DELETE:
        return MessageDeleteEventDict(event_data)
    elif event_type == EVENT_QRCODE_UPDATED:
        return QRCodeEventDict(event_data)
    elif event_type == EVENT_CONNECTION_UPDATE:
        return ConnectionEventDict(event_data)
    else:
        return TypedAttributeDict(event_data)


def wrap_message_data(message_data: MessageData) -> MessageWrapper:
    """
    Wraps message data in MessageWrapper for attribute access
    
    Args:
        message_data: Raw message data
        
    Returns:
        MessageWrapper for the data
    """
    return MessageWrapper(message_data)


class WebhookEventProcessor:
    """
    Processa eventos de webhook e encaminha para handlers registrados
    """
    def __init__(self, client=None):
        self.client = client
        self.handlers: Dict[str, Callable] = {}
        
    def register(self, event_type: str, handler: Callable) -> None:
        """
        Registra um handler para um tipo específico de evento
        
        Args:
            event_type: Tipo do evento (ex: 'messages.upsert')
            handler: Função que processará o evento
        """
        self.handlers[event_type] = handler
        
    def process_event(self, event_data: Union[Dict[str, Any], str, bytes]) -> bool:
        """
        Processa um evento de webhook e encaminha para o handler apropriado
        
        Args:
            event_data: Dados do evento (dict, string JSON ou bytes)
            
        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            # Converter dados para dict se necessário
            if isinstance(event_data, bytes):
                event_data = event_data.decode('utf-8')
                
            # Converter para AttributeDict para acesso via atributos
            if self.client:
                event_wrapper = self.client.convert_webhook_event(event_data)
            else:
                # Fallback se não tiver client
                if isinstance(event_data, str):
                    data_dict = json.loads(event_data)
                else:
                    data_dict = event_data
                event_wrapper = wrap_event_data(cast(WebhookEvent, data_dict))
                
            if not event_wrapper:
                logger.error("Falha ao converter evento")
                return False
                
            # Verificar o tipo de evento
            event_type = event_wrapper.event
            
            if event_type in self.handlers:
                # Chamar o handler com o evento completo
                self.handlers[event_type](event_wrapper)
                return True
            else:
                logger.warning(f"Nenhum handler registrado para o evento: {event_type}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao processar evento: {e}", exc_info=True)
            return False 
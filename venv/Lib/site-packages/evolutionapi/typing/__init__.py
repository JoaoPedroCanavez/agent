"""
Type definitions for Evolution API message types
"""

from .message_types import (
    MessageData,
    MessageKey,
    TextMessageContent,
    ImageMessage,
    VideoMessage,
    AudioMessage,
    DocumentMessage,
    StickerMessage,
    LocationMessage,
    ContactMessage,
    ContactsArrayMessage,
    PollMessage,
    MessageUpdateData,
    MessageDeleteData,
    QRCodeData,
    MessageUpsertEvent,
    WebhookEvent,
    MessageUpdateEvent,
    MessageDeleteEvent,
    QRCodeEvent,
    ConnectionEvent,
    EVENT_MESSAGE_UPSERT,
    EVENT_MESSAGE_UPDATE,
    EVENT_MESSAGE_DELETE,
    EVENT_MESSAGE_EDIT,
    EVENT_QRCODE_UPDATED,
    EVENT_CONNECTION_UPDATE
)

from .message_handlers import (
    MessageRouter,
    WebhookEventProcessor,
    AttributeDict,
    TypedAttributeDict,
    MessageEventDict,
    MessageUpdateEventDict, 
    MessageDeleteEventDict,
    QRCodeEventDict,
    ConnectionEventDict,
    MessageWrapper,
    wrap_event_data,
    wrap_message_data
)

from .webhook import (
    convert_webhook_to_message_data,
    parse_webhook_json,
    parse_webhook_bytes,
    WebhookProcessor
)

from .webhook_processor import (
    WebhookEventProcessor,
    EVENT_MESSAGE_UPSERT,
    EVENT_MESSAGE_UPDATE,
    EVENT_MESSAGE_DELETE,
    EVENT_QRCODE_UPDATED,
    EVENT_CONNECTION_UPDATE,
    EventHandler
)

from .response_types import (
    WhatsAppNumberInfo,
    WhatsAppNumbersResponse,
    MarkMessageAsReadResponse,
    ArchiveChatResponse,
    UnreadChatResponse,
    MessageKeyInfo,
    ProtocolMessage,
    DeleteMessageContent,
    DeleteMessageResponse,
    ProfilePictureResponse,
    MediaMessageResponse,
    UpdateMessageResponse,
    ExtendedTextMessage,
    EditedMessageContent,
    EditMessageProtocolMessage,
    EditMessageContent,
    EditedMessageResponse,
    PresenceResponse,
    MessageStatusUpdate,
    MessageRecord,
    MessagesContainer,
    ChatMessagesResponse
)

__all__ = [
    # Types
    'MessageKey',
    'MessageContextInfo',
    'TextMessageContent',
    'ExtendedTextMessageContent',
    'ImageMessage',
    'VideoMessage',
    'AudioMessage',
    'StickerMessage',
    'DocumentMessage',
    'LocationMessage',
    'ContactMessage',
    'ContactsArrayMessage',
    'PollMessage',
    'MessageData',
    'MessageUpsertEvent',
    
    'MessageUpdateData',
    'MessageUpdateEvent',
    'MessageDeleteData',
    'MessageDeleteEvent',
    'QRCodeData',
    'QRCodeInfo',
    'QRCodeUpdateEvent',
    'ConnectionUpdateData',
    'ConnectionUpdateEvent',
    
    # Response Types
    'WhatsAppNumberInfo',
    'WhatsAppNumbersResponse',
    'MarkMessageAsReadResponse',
    'ArchiveChatResponse',
    'UnreadChatResponse',
    'MessageKeyInfo',
    'ProtocolMessage',
    'DeleteMessageContent',
    'DeleteMessageResponse',
    'ProfilePictureResponse',
    'MediaMessageResponse',
    'UpdateMessageResponse',
    'ExtendedTextMessage',
    'EditedMessageContent',
    'EditMessageProtocolMessage', 
    'EditMessageContent',
    'EditedMessageResponse',
    'PresenceResponse',
    'MessageStatusUpdate',
    'MessageRecord',
    'MessagesContainer',
    'ChatMessagesResponse',
    
    # Functions
    'get_message_content',
    'is_text_message',
    'is_image_message',
    'is_video_message',
    'is_audio_message',
    'is_sticker_message',
    'is_document_message',
    'is_location_message',
    'is_contact_message',
    'is_contacts_array_message',
    'is_poll_message',
    
    # Classes
    'MessageHandler',
    'MessageRouter',
    
    # Webhook utilities
    'convert_webhook_to_message_data',
    'parse_webhook_json',
    'parse_webhook_bytes',
    'WebhookProcessor',
    
    # Event processor
    'WebhookEventProcessor',
    'EventHandler',
    
    # Event constants
    'EVENT_MESSAGE_UPSERT',
    'EVENT_MESSAGE_UPDATE',
    'EVENT_MESSAGE_DELETE',
    'EVENT_MESSAGE_EDIT',
    'EVENT_QRCODE_UPDATED',
    'EVENT_CONNECTION_UPDATE',
    
    # Event handlers and wrappers
    'MessageEventDict',
    'MessageUpdateEventDict',
    'MessageDeleteEventDict',
    'QRCodeEventDict',
    'ConnectionEventDict',
    'TypedAttributeDict',
    'MessageWrapper',
    'AttributeDict'
] 
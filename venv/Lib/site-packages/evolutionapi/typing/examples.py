import logging
from typing import Dict, Any

from .message_types import MessageData
from .message_handlers import (
    get_message_content,
    is_text_message,
    is_image_message,
    is_video_message,
    is_audio_message,
    is_sticker_message,
    is_document_message,
    is_location_message,
    is_contact_message,
    is_contacts_array_message,
    is_poll_message,
    MessageRouter
)

# Configure logger
logger = logging.getLogger(__name__)


def handle_text_message(message_data: MessageData) -> None:
    """Handler for text messages"""
    remote_jid = message_data['key']['remoteJid']
    content = get_message_content(message_data)
    logger.info(f"Text message from {remote_jid}: {content}")


def handle_image_message(message_data: MessageData) -> None:
    """Handler for image messages"""
    remote_jid = message_data['key']['remoteJid']
    image_data = message_data['message']['imageMessage']
    caption = image_data.get('caption', '')
    dimensions = f"{image_data.get('width', 0)}x{image_data.get('height', 0)}"
    logger.info(f"Image message from {remote_jid}: {dimensions} - {caption}")


def handle_video_message(message_data: MessageData) -> None:
    """Handler for video messages"""
    remote_jid = message_data['key']['remoteJid']
    video_data = message_data['message']['videoMessage']
    seconds = video_data.get('seconds', 0)
    logger.info(f"Video message from {remote_jid}: {seconds} seconds")


def handle_audio_message(message_data: MessageData) -> None:
    """Handler for audio messages"""
    remote_jid = message_data['key']['remoteJid']
    audio_data = message_data['message']['audioMessage']
    seconds = audio_data.get('seconds', 0)
    ptt = audio_data.get('ptt', False)
    type_str = "Voice note" if ptt else "Audio"
    logger.info(f"{type_str} from {remote_jid}: {seconds} seconds")


def handle_document_message(message_data: MessageData) -> None:
    """Handler for document messages"""
    remote_jid = message_data['key']['remoteJid']
    document_data = message_data['message']['documentMessage']
    file_name = document_data.get('fileName', 'Unknown')
    mime_type = document_data.get('mimetype', 'Unknown')
    logger.info(f"Document from {remote_jid}: {file_name} ({mime_type})")


def handle_location_message(message_data: MessageData) -> None:
    """Handler for location messages"""
    remote_jid = message_data['key']['remoteJid']
    location_data = message_data['message']['locationMessage']
    lat = location_data.get('degreesLatitude', 0)
    lng = location_data.get('degreesLongitude', 0)
    logger.info(f"Location from {remote_jid}: {lat}, {lng}")


def handle_generic_message(message_data: MessageData) -> None:
    """Default handler for other message types"""
    remote_jid = message_data['key']['remoteJid']
    message_type = message_data.get('messageType', 'unknown')
    logger.info(f"Message from {remote_jid} of type {message_type}")


def create_sample_router() -> MessageRouter:
    """
    Create a sample message router with handlers for different message types
    
    Returns:
        Configured MessageRouter instance
    """
    router = MessageRouter()
    
    # Register handlers for different message types
    router.register('conversation', handle_text_message)
    router.register('imageMessage', handle_image_message)
    router.register('videoMessage', handle_video_message)
    router.register('audioMessage', handle_audio_message)
    router.register('documentMessage', handle_document_message)
    router.register('locationMessage', handle_location_message)
    
    # Set default handler for other message types
    router.set_default_handler(handle_generic_message)
    
    return router


def enhanced_on_message(data: Dict[str, Any]) -> None:
    """
    Enhanced message handler using the typed message structures
    
    Args:
        data: The raw data from the websocket event
    """
    try:
        if 'data' in data:
            message_data = data['data']
            router = create_sample_router()
            
            logger.info("=== Message Received ===")
            logger.info(f"From: {message_data['key']['remoteJid']}")
            logger.info(f"Type: {message_data['messageType']}")
            
            # Route the message to the appropriate handler
            router.route(message_data)
            
            logger.info("=======================")
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True) 
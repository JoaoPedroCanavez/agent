from typing import Union, BinaryIO, Optional, List, Dict, Any, cast
from ..models.chat import *
from ..typing.response_types import (
    WhatsAppNumbersResponse, 
    MarkMessageAsReadResponse, 
    ArchiveChatResponse,
    UnreadChatResponse,
    DeleteMessageResponse,
    ProfilePictureResponse,
    MediaMessageResponse,
    UpdateMessageResponse,
    PresenceResponse,
    ChatMessagesResponse
)

class ChatService:
    def __init__(self, client):
        self.client = client

    def check_is_whatsapp_numbers(self, instance_id: str, data: CheckIsWhatsappNumber, instance_token: str) -> WhatsAppNumbersResponse:
        """
        Check if the provided numbers are registered on WhatsApp
        
        Args:
            instance_id: The instance ID
            data: The data with numbers to check
            instance_token: The instance token
            
        Returns:
            List of objects containing the status of each number
        """
        response = self.client.post(
            f'chat/checkIsWhatsappNumber/{instance_id}',
            data=data.__dict__,
            instance_token=instance_token
        )
        return cast(WhatsAppNumbersResponse, response)
    
    def mark_message_as_read(self, instance_id: str, messages: List[ReadMessage], instance_token: str) -> MarkMessageAsReadResponse:
        """
        Mark messages as read
        
        Args:
            instance_id: The instance ID
            messages: List of message identifiers to mark as read
            instance_token: The instance token
            
        Returns:
            Object containing the result of the operation
        """
        response = self.client.post(
            f'chat/markMessageAsRead/{instance_id}',
            data={"readMessages": [m.__dict__ for m in messages]},
            instance_token=instance_token
        )
        return cast(MarkMessageAsReadResponse, response)

    def archive_chat(self, instance_id: str, data: ArchiveChat, instance_token: str) -> ArchiveChatResponse:
        """
        Archive or unarchive a chat
        
        Args:
            instance_id: The instance ID
            data: The chat data and archive state
            instance_token: The instance token
            
        Returns:
            Object containing the chat ID and its archived state
        """
        response = self.client.post(
            f'chat/archiveChat/{instance_id}',
            data=data.__dict__,
            instance_token=instance_token
        )
        return cast(ArchiveChatResponse, response)

    def mark_chat_unread(self, instance_id: str, data: UnreadChat, instance_token: str) -> UnreadChatResponse:
        """
        Mark a chat as unread
        
        Args:
            instance_id: The instance ID
            data: The chat data containing last message information
            instance_token: The instance token
            
        Returns:
            Object containing the chat ID and its unread state
        """
        response = self.client.post(
            f'chat/markChatUnread/{instance_id}',
            data=data.__dict__,
            instance_token=instance_token
        )
        return cast(UnreadChatResponse, response)

    def delete_message_for_everyone(self, instance_id: str, data: MessageKey, instance_token: str) -> DeleteMessageResponse:
        """
        Delete a message for everyone in the chat
        
        Args:
            instance_id: The instance ID
            data: The message key identifying the message to delete
            instance_token: The instance token
            
        Returns:
            Object containing the protocol message confirming deletion
        """
        response = self.client.delete(
            f'chat/deleteMessageForEveryone/{instance_id}',
            data=data.__dict__,
            instance_token=instance_token
        )
        return cast(DeleteMessageResponse, response)

    def fetch_profile_picture_url(self, instance_id: str, data: ProfilePicture, instance_token: str) -> ProfilePictureResponse:
        """
        Fetch the profile picture URL for a WhatsApp number
        
        Args:
            instance_id: The instance ID
            data: The profile picture request data containing the number
            instance_token: The instance token
            
        Returns:
            Object containing the WhatsApp user ID and profile picture URL
        """
        response = self.client.post(
            f'chat/fetchProfilePictureUrl/{instance_id}',
            data=data.__dict__,
            instance_token=instance_token
        )
        return cast(ProfilePictureResponse, response)

    def get_base64_from_media_message(self, instance_id: str, data: MediaMessage, instance_token: str) -> MediaMessageResponse:
        """
        Get base64-encoded media content from a message
        
        Args:
            instance_id: The instance ID
            data: The media message data
            instance_token: The instance token
            
        Returns:
            Object containing the base64-encoded media and metadata
        """
        response = self.client.post(
            f'chat/getBase64FromMediaMessage/{instance_id}',
            data=data.__dict__,
            instance_token=instance_token
        )
        return cast(MediaMessageResponse, response)

    def update_message(self, instance_id: str, data: UpdateMessage, instance_token: str) -> UpdateMessageResponse:
        """
        Update the text content of a message
        
        Args:
            instance_id: The instance ID
            data: The update message data with new text
            instance_token: The instance token
            
        Returns:
            Object containing the status of the update operation
        """
        response = self.client.post(
            f'chat/updateMessage/{instance_id}',
            data=data.__dict__,
            instance_token=instance_token
        )
        return cast(UpdateMessageResponse, response)

    def send_presence(self, instance_id: str, data: Presence, instance_token: str) -> PresenceResponse:
        """
        Send a presence update (typing, recording, etc.) to a chat
        
        Args:
            instance_id: The instance ID
            data: The presence data with number, delay, and presence type
            instance_token: The instance token
            
        Returns:
            Object confirming the presence type that was sent
        """
        response = self.client.post(
            f'chat/sendPresence/{instance_id}',
            data=data.__dict__,
            instance_token=instance_token
        )
        return cast(PresenceResponse, response)
    
    def get_messages(
        self, 
        instance_id: str, 
        remote_jid: str, 
        instance_token: str, 
        message_id: Optional[str] = None,
        whatsapp_message_id: Optional[str] = None,
        from_me: Optional[bool] = None,
        message_type: Optional[str] = None,
        source: Optional[str] = None,
        timestamp_start: Optional[str] = None,
        timestamp_end: Optional[str] = None,
        page: int = 1, 
        offset: int = 50
    ) -> ChatMessagesResponse:
        """
        Retrieve messages from a chat with optional filters
        
        Args:
            instance_id: The instance ID
            remote_jid: The WhatsApp ID of the chat (e.g. '557499879409@s.whatsapp.net')
            instance_token: The instance token
            message_id: Filter by Evolution API message ID
            whatsapp_message_id: Filter by WhatsApp message ID
            from_me: Filter messages sent by the user (True) or received (False)
            message_type: Filter by message type (e.g. 'conversation', 'imageMessage')
            source: Filter by message source (e.g. 'android', 'web')
            timestamp_start: Start date in ISO format (e.g. '2025-01-16T00:00:00Z')
            timestamp_end: End date in ISO format (e.g. '2025-01-16T23:59:59Z')
            page: Page number for pagination
            offset: Number of messages per page
            
        Returns:
            Chat messages with pagination information and message records
        """
        where = {"key": {"remoteJid": remote_jid}}
        
        if message_id:
            where["id"] = message_id
        if whatsapp_message_id:
            where["key"]["id"] = whatsapp_message_id
        if from_me is not None:
            where["key"]["fromMe"] = from_me
        if message_type:
            where["messageType"] = message_type
        if source:
            where["source"] = source
        if timestamp_start or timestamp_end:
            where["messageTimestamp"] = {}
            if timestamp_start:
                where["messageTimestamp"]["gte"] = timestamp_start
            if timestamp_end:
                where["messageTimestamp"]["lte"] = timestamp_end
            
        payload = {
            "where": where,
            "page": page,
            "offset": offset,
        }
        
        response = self.client.post(
            f'chat/findMessages/{instance_id}', 
            data=payload,
            instance_token=instance_token,
        )
        return cast(ChatMessagesResponse, response)

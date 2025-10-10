from typing import List, Dict, Optional, Any, TypedDict, Literal, Union

class WhatsAppNumberInfo(TypedDict):
    """Information about a phone number's WhatsApp status"""
    exists: bool 
    jid: str
    number: str
    name: Optional[str]  # Only present if exists=True

# Type alias for the list of number info
WhatsAppNumbersResponse = List[WhatsAppNumberInfo]

class MarkMessageAsReadResponse(TypedDict):
    """Response from marking messages as read"""
    message: str  # Usually "Read messages"
    read: Literal["success", "error"]  # Status of the operation

class ArchiveChatResponse(TypedDict):
    """Response from archiving a chat"""
    chatId: str  # The JID of the chat that was archived/unarchived
    archived: bool  # Whether the chat is now archived (true) or unarchived (false)

class UnreadChatResponse(TypedDict):
    """Response from marking a chat as unread"""
    chatId: str  # The JID of the chat that was marked as unread
    markedChatUnread: bool  # Whether the chat was successfully marked as unread

class MessageKeyInfo(TypedDict):
    """Information about a message key"""
    remoteJid: str
    fromMe: bool
    id: str

class ProtocolMessage(TypedDict):
    """Protocol message containing revocation information"""
    key: MessageKeyInfo
    type: Literal["REVOKE"]  # Type of protocol message

class DeleteMessageContent(TypedDict):
    """Content of the delete message confirmation"""
    protocolMessage: ProtocolMessage

class DeleteMessageResponse(TypedDict):
    """Response from deleting a message for everyone"""
    key: MessageKeyInfo  # Information about the confirmation message
    message: DeleteMessageContent  # Content with protocol message
    messageTimestamp: str  # Timestamp as string
    status: Literal["PENDING", "SERVER_ACK", "DELIVERY_ACK", "READ", "PLAYED"]  # Message status 

class ProfilePictureResponse(TypedDict):
    """Response from fetching a profile picture URL"""
    wuid: str  # WhatsApp User ID (JID format)
    profilePictureUrl: Optional[str]  # URL to the profile picture, may be None if not available

class MediaSize(TypedDict):
    """Size information for media files"""
    fileLength: str  # File size in bytes (as string)
    height: Optional[int]  # Image/video height
    width: Optional[int]  # Image/video width

class MediaMessageResponse(TypedDict):
    """Response from getting base64 from media message"""
    mediaType: str  # Type of media (e.g., imageMessage, videoMessage)
    fileName: str  # Name of the file
    size: MediaSize  # Object with size information
    mimetype: str  # MIME type of the media
    base64: str  # Base64-encoded media content
    buffer: Optional[Any]  # Buffer data, can be null

class UpdateMessageResponse(TypedDict):
    """Response from updating a message"""
    status: bool  # Whether the update was successful
    message: str  # Status message

class ExtendedTextMessage(TypedDict):
    """Extended text message content"""
    text: str  # The text content of the message

class EditedMessageContent(TypedDict):
    """Content of the edited message"""
    extendedTextMessage: ExtendedTextMessage  # The edited text message

class EditMessageProtocolMessage(TypedDict):
    """Protocol message for edited messages"""
    key: MessageKeyInfo  # The original message key
    type: Literal["MESSAGE_EDIT"]  # Type of protocol message
    editedMessage: EditedMessageContent  # The edited message content
    timestampMs: str  # Timestamp in milliseconds

class EditMessageContent(TypedDict):
    """Content of the edit message confirmation"""
    protocolMessage: EditMessageProtocolMessage  # Protocol message with edit information

class EditedMessageResponse(TypedDict):
    """Response from editing a message"""
    key: MessageKeyInfo  # Information about the confirmation message
    message: EditMessageContent  # Content with protocol message
    messageTimestamp: str  # Timestamp as string
    status: Literal["PENDING", "SERVER_ACK", "DELIVERY_ACK", "READ", "PLAYED"]  # Message status

class PresenceResponse(TypedDict):
    """Response from sending a presence update"""
    presence: str  # The presence type sent (composing, recording, paused)

class MessageStatusUpdate(TypedDict):
    """Status update for a message"""
    status: Literal["PENDING", "SERVER_ACK", "DELIVERY_ACK", "READ", "PLAYED", "EDITED", "DELETED"]

class MessageRecord(TypedDict):
    """Individual message record from chat history"""
    id: str  # Message ID in Evolution's database
    key: MessageKeyInfo  # WhatsApp message key information
    pushName: str  # Sender's name
    messageType: str  # Type of message (conversation, imageMessage, etc.)
    message: Dict[str, Any]  # Actual message content (varies by type)
    messageTimestamp: int  # Timestamp when message was sent
    instanceId: str  # Instance ID that received the message
    source: str  # Source device (android, ios, web, etc.)
    contextInfo: Optional[Dict[str, Any]]  # Additional context info if available
    MessageUpdate: List[MessageStatusUpdate]  # Status updates for this message

class MessagesContainer(TypedDict):
    """Container for messages in chat history response"""
    total: int  # Total number of messages matching criteria
    pages: int  # Total number of pages
    currentPage: int  # Current page number
    records: List[MessageRecord]  # List of message records

class ChatMessagesResponse(TypedDict):
    """Response from retrieving chat messages"""
    messages: MessagesContainer  # Container with message records and pagination info 
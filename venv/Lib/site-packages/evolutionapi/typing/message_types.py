from typing import Dict, List, Optional, Any, Union, TypedDict

# Event constants for easier identification
EVENT_MESSAGE_UPSERT = "messages.upsert"
EVENT_MESSAGE_UPDATE = "messages.update"
EVENT_MESSAGE_DELETE = "messages.delete"
EVENT_MESSAGE_EDIT = "messages.edit"
EVENT_QRCODE_UPDATED = "qrcode.updated"
EVENT_CONNECTION_UPDATE = "connection.update"

class MessageKey(TypedDict):
    remoteJid: str
    fromMe: bool
    id: str


class DeviceListMetadata(TypedDict):
    senderKeyHash: str
    senderTimestamp: str
    recipientKeyHash: str
    recipientTimestamp: str


class MessageContextInfo(TypedDict):
    deviceListMetadata: DeviceListMetadata
    deviceListMetadataVersion: int
    messageSecret: str


# Text Message
class TextMessageContent(TypedDict):
    conversation: str
    messageContextInfo: Optional[MessageContextInfo]


# Extended Text Message
class ExtendedTextMessageContent(TypedDict):
    extendedTextMessage: Dict[str, Any]
    messageContextInfo: Optional[MessageContextInfo]


# Image Message
class ImageMessageContent(TypedDict):
    url: str
    mimetype: str
    fileSha256: str
    fileLength: str
    height: int
    width: int
    mediaKey: str
    fileEncSha256: str
    directPath: str
    mediaKeyTimestamp: str
    jpegThumbnail: str
    contextInfo: Optional[Dict[str, Any]]


class ImageMessage(TypedDict):
    imageMessage: ImageMessageContent
    messageContextInfo: Optional[MessageContextInfo]
    base64: Optional[str]
    mediaUrl: Optional[str]


# Video Message
class VideoMessageContent(TypedDict):
    url: str
    mimetype: str
    fileSha256: str
    fileLength: str
    seconds: int
    mediaKey: str
    height: int
    width: int
    fileEncSha256: str
    directPath: str
    mediaKeyTimestamp: str
    jpegThumbnail: str
    contextInfo: Optional[Dict[str, Any]]
    streamingSidecar: Optional[str]
    externalShareFullVideoDurationInSeconds: int


class VideoMessage(TypedDict):
    videoMessage: VideoMessageContent
    messageContextInfo: Optional[MessageContextInfo]
    base64: Optional[str]
    mediaUrl: Optional[str]


# Audio Message
class AudioMessageContent(TypedDict):
    url: str
    mimetype: str
    fileSha256: str
    fileLength: str
    seconds: int
    ptt: bool
    mediaKey: str
    fileEncSha256: str
    directPath: str
    mediaKeyTimestamp: str
    waveform: Optional[str]


class AudioMessage(TypedDict):
    audioMessage: AudioMessageContent
    messageContextInfo: Optional[MessageContextInfo]
    base64: Optional[str]
    mediaUrl: Optional[str]


# Sticker Message
class StickerMessageContent(TypedDict):
    url: str
    fileSha256: str
    fileEncSha256: str
    mediaKey: str
    mimetype: str
    height: int
    width: int
    directPath: str
    fileLength: str
    mediaKeyTimestamp: str
    isAnimated: bool
    stickerSentTs: str
    isAvatar: bool
    isAiSticker: bool
    isLottie: bool


class StickerMessage(TypedDict):
    stickerMessage: StickerMessageContent
    messageContextInfo: Optional[MessageContextInfo]
    base64: Optional[str]
    mediaUrl: Optional[str]


# Document Message
class DocumentMessageContent(TypedDict):
    url: str
    mimetype: str
    fileSha256: str
    fileLength: str
    pageCount: int
    mediaKey: str
    fileName: str
    fileEncSha256: str
    directPath: str
    mediaKeyTimestamp: str
    thumbnailDirectPath: Optional[str]
    thumbnailSha256: Optional[str]
    thumbnailEncSha256: Optional[str]
    jpegThumbnail: Optional[str]
    thumbnailHeight: Optional[int]
    thumbnailWidth: Optional[int]


class DocumentMessage(TypedDict):
    documentMessage: DocumentMessageContent
    messageContextInfo: Optional[MessageContextInfo]
    base64: Optional[str]
    mediaUrl: Optional[str]


# Location Message
class LocationMessageContent(TypedDict):
    degreesLatitude: float
    degreesLongitude: float
    jpegThumbnail: str


class LocationMessage(TypedDict):
    locationMessage: LocationMessageContent
    messageContextInfo: Optional[MessageContextInfo]


# Contact Message
class ContactMessageContent(TypedDict):
    displayName: str
    vcard: str


class ContactMessage(TypedDict):
    contactMessage: ContactMessageContent
    messageContextInfo: Optional[MessageContextInfo]


# Contact Array Message
class ContactArrayItem(TypedDict):
    displayName: str
    vcard: str


class ContactsArrayMessageContent(TypedDict):
    displayName: str
    contacts: List[ContactArrayItem]


class ContactsArrayMessage(TypedDict):
    contactsArrayMessage: ContactsArrayMessageContent
    messageContextInfo: Optional[MessageContextInfo]


# Poll Message
class PollOption(TypedDict):
    optionName: str


class PollCreationMessageContent(TypedDict):
    name: str
    options: List[PollOption]
    selectableOptionsCount: int


class PollMessage(TypedDict):
    pollCreationMessageV3: PollCreationMessageContent
    messageContextInfo: Optional[MessageContextInfo]


# Message Data
class MessageData(TypedDict):
    key: MessageKey
    pushName: str
    status: str
    message: Union[
        TextMessageContent,
        ExtendedTextMessageContent,
        ImageMessage,
        VideoMessage,
        AudioMessage,
        StickerMessage,
        DocumentMessage,
        LocationMessage,
        ContactMessage,
        ContactsArrayMessage,
        PollMessage,
    ]
    contextInfo: Optional[Dict[str, Any]]
    messageType: str
    messageTimestamp: int
    instanceId: str
    source: str


# Generic Webhook Event type to handle all events
class WebhookEvent(TypedDict):
    event: str
    instance: str
    data: Any
    destination: Optional[str]
    date_time: Optional[str]
    server_url: Optional[str]
    apikey: Optional[str]
    sender: Optional[str]


class MessageUpdateData(TypedDict):
    messageId: str
    keyId: str
    remoteJid: str
    fromMe: bool
    status: str
    instanceId: str
    participant: Optional[str]


class MessageUpdateEvent(TypedDict):
    event: str  # 'messages.update'
    instance: str
    data: MessageUpdateData
    destination: Optional[str]
    date_time: str
    sender: str
    server_url: str
    apikey: str


# MessageDelete Event (messages.delete)
class MessageDeleteData(TypedDict):
    remoteJid: str
    fromMe: bool
    id: str


class MessageDeleteEvent(TypedDict):
    event: str  # 'messages.delete'
    instance: str
    data: MessageDeleteData
    destination: Optional[str]
    date_time: str
    sender: str
    server_url: str
    apikey: str


# QRCode Event (qrcode.updated)
class QRCodeData(TypedDict):
    instance: str
    pairingCode: Optional[str]
    code: str
    base64: str


class QRCodeInfo(TypedDict):
    qrcode: QRCodeData


class QRCodeUpdateEvent(TypedDict):
    event: str  # 'qrcode.updated'
    instance: str
    data: QRCodeInfo
    destination: Optional[str]
    date_time: str
    sender: str
    server_url: str
    apikey: str


# Connection Update Event (connection.update)
class ConnectionUpdateData(TypedDict):
    instance: str
    state: str  # 'connecting', 'open', 'close', etc.
    statusReason: int
    lastDisconnect: Optional[Dict[str, Any]]


class ConnectionUpdateEvent(TypedDict):
    event: str  # 'connection.update'
    instance: str
    data: ConnectionUpdateData
    destination: Optional[str]
    date_time: Optional[str]
    sender: Optional[str]
    server_url: Optional[str]
    apikey: Optional[str]


# Specific event types
class MessageUpsertEvent(WebhookEvent):
    data: MessageData


class MessageUpdateEvent(WebhookEvent):
    data: MessageUpdateData


class MessageDeleteEvent(WebhookEvent):
    data: MessageDeleteData


class QRCodeEvent(WebhookEvent):
    data: QRCodeData


class ConnectionEvent(WebhookEvent):
    data: ConnectionUpdateData

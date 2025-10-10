from typing import Union, BinaryIO
from ..models.message import *

class MessageService:
    def __init__(self, client):
        self.client = client

    def send_text(self, instance_id: str, message: TextMessage, instance_token: str):
        return self.client.post(
            f'message/sendText/{instance_id}',
            data=message.__dict__,
            instance_token=instance_token
        )

    def send_media(self, instance_id: str, message: MediaMessage, instance_token: str, file: BinaryIO = None):
        payload = {
            'data': message.__dict__,
            'instance_token': instance_token
        }
        
        if file:
            payload['files'] = {'file': file}
            
        return self.client.post(
            f'message/sendMedia/{instance_id}',
            **payload
        )

    def send_ptv(self, instance_id: str, message: dict, instance_token: str, file: BinaryIO = None):
        payload = {
            'data': message,
            'instance_token': instance_token
        }
        
        if file:
            payload['files'] = {'file': file}
            
        return self.client.post(
            f'message/sendPtv/{instance_id}',
            **payload
        )

    def send_whatsapp_audio(self, instance_id: str, message: dict, instance_token: str, file: BinaryIO = None):
        payload = {
            'data': message,
            'instance_token': instance_token
        }
        
        if file:
            payload['files'] = {'file': file}
            
        return self.client.post(
            f'message/sendWhatsAppAudio/{instance_id}',
            **payload
        )

    def send_status(self, instance_id: str, message: StatusMessage, instance_token: str):
        return self.client.post(
            f'message/sendStatus/{instance_id}',
            data=message.__dict__,
            instance_token=instance_token
        )

    def send_sticker(self, instance_id: str, message: dict, instance_token: str):
        return self.client.post(
            f'message/sendSticker/{instance_id}',
            data=message,
            instance_token=instance_token
        )

    def send_location(self, instance_id: str, message: LocationMessage, instance_token: str):
        return self.client.post(
            f'message/sendLocation/{instance_id}',
            data=message.__dict__,
            instance_token=instance_token
        )

    def send_contact(self, instance_id: str, message: ContactMessage, instance_token: str):
        return self.client.post(
            f'message/sendContact/{instance_id}',
            data=message.__dict__,
            instance_token=instance_token
        )

    def send_reaction(self, instance_id: str, message: ReactionMessage, instance_token: str):
        return self.client.post(
            f'message/sendReaction/{instance_id}',
            data=message.__dict__,
            instance_token=instance_token
        )

    def send_poll(self, instance_id: str, message: PollMessage, instance_token: str):
        return self.client.post(
            f'message/sendPoll/{instance_id}',
            data=message.__dict__,
            instance_token=instance_token
        )

    def send_list(self, instance_id: str, message: ListMessage, instance_token: str):
        return self.client.post(
            f'message/sendList/{instance_id}',
            data=message.__dict__,
            instance_token=instance_token
        )

    def send_buttons(self, instance_id: str, message: ButtonMessage, instance_token: str):
        return self.client.post(
            f'message/sendButtons/{instance_id}',
            data=message.__dict__,
            instance_token=instance_token
        )
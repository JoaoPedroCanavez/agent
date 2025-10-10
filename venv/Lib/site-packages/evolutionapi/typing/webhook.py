import json
import logging
from typing import Dict, Any, Optional, Union, cast

from .message_types import MessageData, MessageUpsertEvent

logger = logging.getLogger(__name__)


def convert_webhook_to_message_data(data: Dict[str, Any]) -> Optional[MessageData]:
    """
    Converte dados de webhook para o tipo MessageData
    
    Args:
        data: Dados recebidos do webhook
        
    Returns:
        MessageData se conversão for bem-sucedida, None caso contrário
    """
    try:
        if 'data' in data:
            # Se já tiver a estrutura esperada, apenas faz o cast
            return cast(MessageData, data['data'])
        elif 'event' in data and data['event'] == 'messages.upsert':
            # Se for um evento do tipo MessageUpsertEvent
            return cast(MessageData, data['data'])
        else:
            logger.warning(f"Formato de dados desconhecido: {data.keys()}")
            return None
    except Exception as e:
        logger.error(f"Erro ao converter mensagem: {e}", exc_info=True)
        return None


def parse_webhook_json(webhook_data: str) -> Optional[MessageData]:
    """
    Processa dados de webhook recebidos como string JSON
    
    Args:
        webhook_data: String JSON com dados do webhook
        
    Returns:
        MessageData se conversão for bem-sucedida, None caso contrário
    """
    try:
        data = json.loads(webhook_data)
        return convert_webhook_to_message_data(data)
    except json.JSONDecodeError:
        logger.error("Dados de webhook inválidos - não é um JSON válido")
        return None
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}", exc_info=True)
        return None


def parse_webhook_bytes(webhook_data: bytes) -> Optional[MessageData]:
    """
    Processa dados de webhook recebidos como bytes
    
    Args:
        webhook_data: Bytes com dados do webhook
        
    Returns:
        MessageData se conversão for bem-sucedida, None caso contrário
    """
    try:
        decoded_data = webhook_data.decode('utf-8')
        return parse_webhook_json(decoded_data)
    except UnicodeDecodeError:
        logger.error("Erro ao decodificar dados do webhook - não é UTF-8 válido")
        return None
    except Exception as e:
        logger.error(f"Erro ao processar webhook bytes: {e}", exc_info=True)
        return None


class WebhookProcessor:
    """
    Classe para processar webhooks recebidos da Evolution API
    """
    
    def __init__(self):
        self.handlers = {}
    
    def register_handler(self, event_type: str, handler_func):
        """
        Registra uma função de handler para determinado tipo de evento
        
        Args:
            event_type: Tipo de evento ('messages.upsert', etc)
            handler_func: Função que será chamada quando o evento ocorrer
        """
        self.handlers[event_type] = handler_func
    
    def process_webhook(self, webhook_data: Union[str, bytes, Dict[str, Any]]) -> bool:
        """
        Processa dados de webhook e dispara o handler apropriado
        
        Args:
            webhook_data: Dados do webhook (string JSON, bytes ou dict)
            
        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            # Converte para dict se for string ou bytes
            data = None
            
            if isinstance(webhook_data, str):
                data = json.loads(webhook_data)
            elif isinstance(webhook_data, bytes):
                data = json.loads(webhook_data.decode('utf-8'))
            elif isinstance(webhook_data, dict):
                data = webhook_data
            else:
                logger.error(f"Tipo de dados de webhook não suportado: {type(webhook_data)}")
                return False
            
            # Verifica o tipo de evento
            if 'event' not in data:
                logger.warning("Webhook não contém campo 'event'")
                return False
            
            event_type = data['event']
            
            # Verifica se há um handler registrado para esse evento
            if event_type in self.handlers:
                # Converte para MessageData se for evento de mensagem
                if event_type == 'messages.upsert':
                    message_data = convert_webhook_to_message_data(data)
                    if message_data:
                        self.handlers[event_type](message_data)
                    else:
                        logger.warning("Falha ao converter dados de mensagem")
                        return False
                else:
                    # Para outros tipos de evento, passa o dado bruto
                    self.handlers[event_type](data)
                
                return True
            else:
                logger.info(f"Nenhum handler registrado para evento '{event_type}'")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}", exc_info=True)
            return False 
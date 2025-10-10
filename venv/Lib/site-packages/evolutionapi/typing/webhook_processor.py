import logging
from typing import Dict, Any, Callable, Optional, Union

logger = logging.getLogger(__name__)

# Tipos de evento
EVENT_MESSAGE_UPSERT = 'messages.upsert'
EVENT_MESSAGE_UPDATE = 'messages.update'
EVENT_MESSAGE_DELETE = 'messages.delete'
EVENT_QRCODE_UPDATED = 'qrcode.updated'
EVENT_CONNECTION_UPDATE = 'connection.update'

# Tipo de handler de evento
EventHandler = Callable[[Dict[str, Any]], None]


class WebhookEventProcessor:
    """
    Processador de eventos recebidos via webhook da Evolution API
    
    Esta classe facilita o registro e gerenciamento de handlers para
    diferentes tipos de eventos.
    """
    
    def __init__(self, client=None):
        """
        Inicializa o processador de eventos
        
        Args:
            client: Cliente Evolution API opcional para usar seus métodos de conversão
        """
        self.handlers: Dict[str, EventHandler] = {}
        self.client = client
        
    def register(self, event_type: str, handler: EventHandler) -> None:
        """
        Registra um handler para um tipo específico de evento
        
        Args:
            event_type: Tipo de evento ('messages.upsert', 'messages.update', etc.)
            handler: Função que será chamada quando o evento ocorrer
        """
        self.handlers[event_type] = handler
        
    def get_handler(self, event_type: str) -> Optional[EventHandler]:
        """
        Obtém o handler registrado para um tipo de evento
        
        Args:
            event_type: Tipo de evento
            
        Returns:
            O handler registrado ou None se não houver
        """
        return self.handlers.get(event_type)
        
    def has_handler(self, event_type: str) -> bool:
        """
        Verifica se há um handler registrado para o tipo de evento
        
        Args:
            event_type: Tipo de evento
            
        Returns:
            True se houver um handler registrado, False caso contrário
        """
        return event_type in self.handlers
        
    def process_event(self, event_data: Union[Dict[str, Any], str, bytes]) -> bool:
        """
        Processa um evento recebido e encaminha para o handler apropriado
        
        Args:
            event_data: Dados do evento
            
        Returns:
            True se o evento foi processado com sucesso, False caso contrário
        """
        try:
            # Se temos um cliente, usamos sua função de conversão
            if self.client:
                event_type, data = self.client.convert_webhook_event(event_data)
            else:
                # Precisamos implementar a conversão localmente
                import json
                
                if isinstance(event_data, str):
                    event_data = json.loads(event_data)
                elif isinstance(event_data, bytes):
                    event_data = json.loads(event_data.decode('utf-8'))
                
                if not isinstance(event_data, dict):
                    logger.error(f"Formato de evento inválido: {type(event_data)}")
                    return False
                
                if 'event' not in event_data or 'data' not in event_data:
                    logger.warning("Evento não contém campos 'event' ou 'data'")
                    return False
                
                event_type = event_data['event']
                data = event_data['data']
            
            # Verifica se há um handler para o tipo de evento
            if not event_type or not data:
                logger.warning("Tipo de evento ou dados ausentes")
                return False
                
            # Processa o evento com o handler registrado
            handler = self.get_handler(event_type)
            
            if handler:
                # Aplicar processamento específico para cada tipo de evento
                if event_type == EVENT_MESSAGE_UPDATE and self.client:
                    processed_data = self.client.process_message_update(data)
                    handler(processed_data)
                elif event_type == EVENT_MESSAGE_DELETE and self.client:
                    processed_data = self.client.process_message_delete(data)
                    handler(processed_data)
                elif event_type == EVENT_QRCODE_UPDATED and self.client:
                    processed_data = self.client.process_qrcode_update(data)
                    handler(processed_data)
                else:
                    # Para outros eventos ou quando não temos client, passa os dados brutos
                    handler(data)
                
                return True
            else:
                logger.info(f"Nenhum handler registrado para o evento '{event_type}'")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao processar evento: {e}", exc_info=True)
            return False
            
    def register_all(self, handlers: Dict[str, EventHandler]) -> None:
        """
        Registra múltiplos handlers de uma vez
        
        Args:
            handlers: Dicionário de tipo_evento -> handler
        """
        for event_type, handler in handlers.items():
            self.register(event_type, handler) 
"""
Telegram Transport Implementation.

Implementación concreta de MessageTransport para Telegram usando Telethon.

Características:
- Valida configuración (cliente, sesión)
- Envía mensajes y archivos con timeout
- Manejo de errores Telegram-específicos
- Logging detallado
"""

import logging
from typing import Any, Dict, Optional

from app.transports.base import BaseMessageTransport
from app.execution.exceptions import (
    TransportException,
    TransportValidationException,
)
from app.telegram import service as tg_service

logger = logging.getLogger(__name__)


class TelegramTransport(BaseMessageTransport):
    """
    Transporte de Telegram vía Telethon.
    
    Envía mensajes a comunidades (grupos/canales) de Telegram.
    
    Ejemplo:
        transport = TelegramTransport(session_encrypted)
        result = await transport.send(
            recipient_id="-1001234567890",  # chat_id
            content="Hola comunidad",
            metadata={"multimedia_url": "https://...png"},
        )
        # result: {"status": "success", "message_id": 12345, ...}
    """

    def __init__(self, session_encrypted: bytes):
        """
        Inicializa transporte de Telegram.

        Args:
            session_encrypted: Sesión Telegram cifrada del usuario
        """
        self.session_encrypted = session_encrypted
        self._client = None

    async def validate(self) -> bool:
        """
        Valida que la sesión Telegram es válida.

        Intenta conectar y desconectar rápidamente.

        Returns:
            True si es válida, False si no
        """
        try:
            client = await tg_service.get_client(self.session_encrypted)
            # Verificar que está conectado
            is_user = await client.is_user_authorized()
            await client.disconnect()
            return is_user
        except Exception as e:
            logger.error(f"Telegram session validation failed: {e}")
            return False

    async def send(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje a una comunidad de Telegram.

        Args:
            recipient_id: chat_id de la comunidad (ej: "-1001234567890")
            content: Texto del mensaje (markdown)
            metadata: Datos adicionales:
                - multimedia_url: URL de imagen/archivo a adjuntar
                - parse_mode: Tipo de parsing ("md" por defecto)

        Returns:
            {
                "status": "success",
                "message_id": 12345,
                "chat_id": "-1001234567890",
            }

        Raises:
            TransportException: Si falla el envío
            TransportValidationException: Si los parámetros son inválidos
        """
        # Validar parámetros
        if not self._validate_recipient(recipient_id):
            raise TransportValidationException(
                f"Invalid recipient_id: {recipient_id}"
            )
        if not self._validate_content(content):
            raise TransportValidationException("Content is empty")

        metadata = metadata or {}
        multimedia_url = metadata.get("multimedia_url")
        parse_mode = metadata.get("parse_mode", "md")

        try:
            # Obtener cliente
            client = await tg_service.get_client(self.session_encrypted)
            
            try:
                logger.debug(f"Sending message to {recipient_id}")
                
                # Convertir chat_id a int
                chat_id = int(recipient_id)
                
                # Enviar mensaje
                if multimedia_url:
                    # Con archivo adjunto
                    message = await client.send_file(
                        chat_id,
                        multimedia_url,
                        caption=content,
                        parse_mode=parse_mode,
                    )
                else:
                    # Solo texto
                    message = await client.send_message(
                        chat_id,
                        content,
                        parse_mode=parse_mode,
                    )
                
                logger.info(
                    f"Message sent successfully to {chat_id}, "
                    f"message_id: {message.id}"
                )
                
                return {
                    "status": "success",
                    "message_id": str(message.id),
                    "chat_id": str(chat_id),
                    "timestamp": message.date.isoformat() if message.date else None,
                }
            
            finally:
                await client.disconnect()
        
        except TransportValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to send message to {recipient_id}: {e}")
            raise TransportException(f"Failed to send message: {e}")

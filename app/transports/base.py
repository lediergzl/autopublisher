"""
Base Transport Implementation.

Clase base para transports concretos.
"""

import logging
from abc import abstractmethod
from typing import Any, Dict, Optional

from app.execution.interfaces import MessageTransport
from app.execution.exceptions import TransportValidationException

logger = logging.getLogger(__name__)


class BaseMessageTransport(MessageTransport):
    """
    Clase base para implementaciones de transporte.
    
    Proporciona utilidades comunes.
    """

    async def validate(self) -> bool:
        """
        Valida que el transporte esté correctamente configurado.
        
        Implementación por defecto: override en subclases.
        """
        return True

    @abstractmethod
    async def send(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje.
        
        Implementar en subclases.
        """
        pass

    def _validate_recipient(self, recipient_id: str) -> bool:
        """
        Valida formato básico de destinatario.
        """
        return bool(recipient_id and len(recipient_id.strip()) > 0)

    def _validate_content(self, content: str) -> bool:
        """
        Valida que el contenido no esté vacío.
        """
        return bool(content and len(content.strip()) > 0)

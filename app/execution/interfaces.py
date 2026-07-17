"""
Interfaces abstractas del motor de ejecución.

Define contratos para componentes pluggables.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class MessageTransport(ABC):
    """
    Interfaz abstracta para transporte de mensajes.
    
    Permite implementaciones concretas para diferentes plataformas
    (Telegram, WhatsApp, Email, etc.) sin acoplar la lógica de ejecución.
    
    Ejemplo:
        - TelegramTransport: envía mensajes via Telegram
        - WhatsAppTransport: envía mensajes via WhatsApp
        - EmailTransport: envía mensajes via Email
    """

    @abstractmethod
    async def send(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje a un destinatario.

        Args:
            recipient_id: Identificador del destinatario (chat_id, user_id, email, etc.)
            content: Contenido del mensaje
            metadata: Datos adicionales (multimedia, parsing, etc.)

        Returns:
            Dict con resultado de envío: {"status": "success", "message_id": "...", ...}

        Raises:
            TransportException: Si falla el envío
        """
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """
        Valida que el transporte está correctamente configurado.

        Returns:
            True si es válido, False en caso contrario
        """
        pass


class ExecutionRepository(ABC):
    """
    Interfaz para persistencia de ejecuciones.
    
    Permite cambiar el backend de almacenamiento sin impactar la lógica.
    """

    @abstractmethod
    async def create_execution(
        self,
        campaign_id: int,
        user_id: int,
        task_count: int,
    ) -> Dict[str, Any]:
        """
        Crea un nuevo registro de ejecución.

        Returns:
            execution_id y metadata
        """
        pass

    @abstractmethod
    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Obtiene los detalles de una ejecución.
        """
        pass

    @abstractmethod
    async def update_execution_state(
        self,
        execution_id: str,
        state: str,
    ) -> None:
        """
        Actualiza el estado global de una ejecución.
        """
        pass

    @abstractmethod
    async def record_task_audit(
        self,
        execution_id: str,
        task_id: str,
        event: str,
        details: Dict[str, Any],
    ) -> None:
        """
        Registra un evento de auditoría para una tarea.
        """
        pass


class QueueBackend(ABC):
    """
    Interfaz para backend de colas de trabajo.
    
    Permite usar Redis, RabbitMQ, SQS, etc.
    """

    @abstractmethod
    async def enqueue(
        self,
        queue_name: str,
        task_id: str,
        payload: Dict[str, Any],
    ) -> None:
        """
        Encola una tarea para procesamiento.
        """
        pass

    @abstractmethod
    async def dequeue(
        self,
        queue_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Desencola una tarea del frente.
        """
        pass

    @abstractmethod
    async def mark_processing(
        self,
        queue_name: str,
        task_id: str,
    ) -> None:
        """
        Marca una tarea como en procesamiento.
        """
        pass

    @abstractmethod
    async def mark_completed(
        self,
        queue_name: str,
        task_id: str,
    ) -> None:
        """
        Marca una tarea como completada.
        """
        pass

    @abstractmethod
    async def mark_failed(
        self,
        queue_name: str,
        task_id: str,
        error: str,
        retry_count: int,
    ) -> None:
        """
        Marca una tarea como fallida.
        """
        pass

    @abstractmethod
    async def get_queue_length(self, queue_name: str) -> int:
        """
        Obtiene la cantidad de tareas en cola.
        """
        pass

"""
Queue Manager: Orquestador de colas.

Capa de abstracción sobre el backend de colas.
Permite cambiar Redis por otro sistema sin afectar los workers.
"""

import logging
from typing import Dict, Any, Optional

from app.execution.interfaces import QueueBackend

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Gestor de colas con interfaz unificada.
    
    Delega operaciones al backend concreto (Redis, RabbitMQ, etc).
    """

    def __init__(self, backend: QueueBackend):
        """
        Inicializa con un backend de colas.

        Args:
            backend: Implementación de QueueBackend
        """
        self.backend = backend

    async def enqueue(
        self,
        queue_name: str,
        task_id: str,
        payload: Dict[str, Any],
    ) -> None:
        """
        Encola una tarea.
        """
        await self.backend.enqueue(queue_name, task_id, payload)
        logger.debug(f"Task {task_id} enqueued to {queue_name}")

    async def dequeue(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """
        Desencola una tarea.
        """
        task = await self.backend.dequeue(queue_name)
        if task:
            logger.debug(f"Task dequeued from {queue_name}: {task.get('task_id')}")
        return task

    async def mark_processing(
        self,
        queue_name: str,
        task_id: str,
    ) -> None:
        """
        Marca una tarea como en procesamiento.
        """
        await self.backend.mark_processing(queue_name, task_id)

    async def mark_completed(
        self,
        queue_name: str,
        task_id: str,
    ) -> None:
        """
        Marca una tarea como completada.
        """
        await self.backend.mark_completed(queue_name, task_id)
        logger.debug(f"Task {task_id} marked as completed")

    async def mark_failed(
        self,
        queue_name: str,
        task_id: str,
        error: str,
        retry_count: int = 0,
    ) -> None:
        """
        Marca una tarea como fallida.
        """
        await self.backend.mark_failed(queue_name, task_id, error, retry_count)
        logger.debug(f"Task {task_id} marked as failed, retries: {retry_count}")

    async def get_queue_length(self, queue_name: str) -> int:
        """
        Obtiene el tamaño actual de la cola.
        """
        return await self.backend.get_queue_length(queue_name)

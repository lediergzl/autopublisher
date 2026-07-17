"""
Task Processor: Procesa tareas de ejecución.

Responsable de:
- Desencollar tareas
- Validar integridad
- Invocar transporte
- Registrar auditoría
- Manejar reintentos
"""

import logging
from typing import Optional
import asyncio

from app.execution.models import CampaignExecutionTask, TaskState
from app.execution.interfaces import MessageTransport
from app.execution.exceptions import TaskProcessingException, TransportException
from app.queue.manager import QueueManager
from app.execution.manager import CampaignManager

logger = logging.getLogger(__name__)


class TaskProcessor:
    """
    Procesador de tareas individual.
    
    Orquesta el envío de un mensaje para una tarea específica.
    
    Arquitectura:
    1. Desencollar tarea
    2. Validar
    3. Marcar como procesando
    4. Enviar via transporte
    5. Registrar resultado
    6. Manejo de errores y reintentos
    """

    def __init__(
        self,
        queue_manager: QueueManager,
        campaign_manager: CampaignManager,
        message_transport: MessageTransport,
    ):
        """
        Inicializa procesador de tareas.

        Args:
            queue_manager: Gestor de colas
            campaign_manager: Gestor de ejecuciones
            message_transport: Transporte para envío de mensajes
        """
        self.queue_manager = queue_manager
        self.campaign_manager = campaign_manager
        self.message_transport = message_transport

    async def process_task(
        self,
        execution_id: str,
        queue_name: str,
        task_data: dict,
    ) -> bool:
        """
        Procesa una tarea completa.

        Args:
            execution_id: ID de la ejecución
            queue_name: Nombre de la cola
            task_data: Datos de la tarea desencolada

        Returns:
            True si se procesó exitosamente, False si falló

        Raises:
            TaskProcessingException: Para errores no recuperables
        """
        try:
            # Deserializar
            task = CampaignExecutionTask.from_dict(task_data)
            
            # Validar
            self._validate_task(task)
            
            # Marcar como procesando
            await self.queue_manager.mark_processing(queue_name, task.task_id)
            await self.campaign_manager.record_task_start(
                execution_id,
                task.task_id,
                task.campaign_id,
                task.community_id,
            )
            
            # Enviar mensaje
            logger.info(f"Processing task {task.task_id}")
            result = await self._send_message(task)
            
            # Registrar éxito
            await self.queue_manager.mark_completed(queue_name, task.task_id)
            await self.campaign_manager.record_task_completion(
                execution_id,
                task.task_id,
                result.get("message_id", "unknown"),
            )
            
            logger.info(f"Task completed successfully: {task.task_id}")
            return True
        
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            await self._handle_task_failure(
                execution_id,
                queue_name,
                task_data,
                str(e),
            )
            return False

    async def _send_message(self, task: CampaignExecutionTask) -> dict:
        """
        Envía el mensaje usando el transporte.

        Returns:
            Resultado del transporte

        Raises:
            TransportException: Si falla el envío
        """
        try:
            # Validar transporte
            if not await self.message_transport.validate():
                raise TransportException("Transport validation failed")
            
            # Enviar con timeout
            result = await asyncio.wait_for(
                self.message_transport.send(
                    recipient_id=task.recipient_id,
                    content=task.content,
                    metadata={
                        "multimedia_url": task.multimedia_url,
                        **task.metadata,
                    },
                ),
                timeout=task.timeout_seconds,
            )
            
            return result
        except asyncio.TimeoutError:
            raise TransportException(f"Send timeout after {task.timeout_seconds}s")
        except Exception as e:
            raise TransportException(f"Send failed: {e}")

    async def _handle_task_failure(
        self,
        execution_id: str,
        queue_name: str,
        task_data: dict,
        error: str,
    ) -> None:
        """
        Maneja el fallo de una tarea.
        """
        task_id = task_data.get("task_id")
        retry_count = task_data.get("retry_count", 0)
        
        try:
            await self.queue_manager.mark_failed(
                queue_name,
                task_id,
                error,
                retry_count,
            )
            await self.campaign_manager.record_task_failure(
                execution_id,
                task_id,
                error,
                retry_count,
            )
        except Exception as e:
            logger.error(f"Failed to record task failure: {e}")

    def _validate_task(self, task: CampaignExecutionTask) -> None:
        """
        Valida la integridad de una tarea.

        Raises:
            TaskProcessingException: Si la tarea es inválida
        """
        if not task.task_id:
            raise TaskProcessingException("Task ID is missing")
        if not task.execution_id:
            raise TaskProcessingException("Execution ID is missing")
        if not task.recipient_id:
            raise TaskProcessingException("Recipient ID is missing")
        if not task.content or not task.content.strip():
            raise TaskProcessingException("Content is empty")

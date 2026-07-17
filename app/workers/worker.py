"""
Worker: Proceso independiente para procesar tareas.

Responsable de:
- Conectar a la cola
- Desencolar tareas
- Invocar procesador
- Manejar ciclo de vida
- Logging

Puede ejecutarse como:
- Proceso separado
- Greenlet
- Celery task
"""

import logging
import asyncio
from typing import Optional

from app.queue.manager import QueueManager
from app.execution.manager import CampaignManager
from app.workers.task_processor import TaskProcessor

logger = logging.getLogger(__name__)


class Worker:
    """
    Worker independiente para procesar tareas de ejecución de campañas.
    
    Ejemplo de uso:
        worker = Worker(
            queue_manager=queue_manager,
            campaign_manager=campaign_manager,
            task_processor=task_processor,
            concurrency=4,
        )
        await worker.start()
        # Procesa tareas en loop
        await worker.stop()
    """

    def __init__(
        self,
        queue_manager: QueueManager,
        campaign_manager: CampaignManager,
        task_processor: TaskProcessor,
        concurrency: int = 1,
        poll_interval_seconds: float = 1.0,
    ):
        """
        Inicializa un worker.

        Args:
            queue_manager: Gestor de colas
            campaign_manager: Gestor de ejecuciones
            task_processor: Procesador de tareas
            concurrency: Cantidad de tareas simultaneas
            poll_interval_seconds: Intervalo entre polling de cola
        """
        self.queue_manager = queue_manager
        self.campaign_manager = campaign_manager
        self.task_processor = task_processor
        self.concurrency = concurrency
        self.poll_interval_seconds = poll_interval_seconds
        self._running = False
        self._active_tasks: set = set()

    async def start(self, execution_id: str, queue_name: str) -> None:
        """
        Inicia el worker.

        Args:
            execution_id: ID de la ejecución a procesar
            queue_name: Nombre de la cola a monitorear
        """
        self._running = True
        logger.info(f"Worker starting for execution {execution_id}")
        
        try:
            while self._running:
                # Mantener concurrencia
                if len(self._active_tasks) < self.concurrency:
                    # Intentar desencolar
                    task_data = await self.queue_manager.dequeue(queue_name)
                    
                    if task_data:
                        # Crear tarea asyncio
                        task = asyncio.create_task(
                            self.task_processor.process_task(
                                execution_id,
                                queue_name,
                                task_data,
                            )
                        )
                        self._active_tasks.add(task)
                        task.add_done_callback(self._active_tasks.discard)
                    else:
                        # Cola vacía, esperar
                        await asyncio.sleep(self.poll_interval_seconds)
                else:
                    # A capacidad, esperar
                    await asyncio.sleep(self.poll_interval_seconds)
        
        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """
        Detiene el worker.
        
        Espera a que completen las tareas activas.
        """
        logger.info("Worker stopping...")
        self._running = False
        
        # Esperar tareas activas
        if self._active_tasks:
            logger.info(f"Waiting for {len(self._active_tasks)} active tasks...")
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        
        logger.info("Worker stopped")

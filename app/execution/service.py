"""
Execution Engine Service.

Servicio de alto nivel que orquesta toda la ejecución de campañas.

Responsable de:
- Inicializar componentes
- Inyectar dependencias
- Orquestar el flujo de ejecución
- Manejo de errores global
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.manager import CampaignManager
from app.execution.repositories import DatabaseExecutionRepository
from app.queue.manager import QueueManager
from app.queue.redis_backend import RedisQueueBackend
from app.workers.task_processor import TaskProcessor
from app.transports.telegram import TelegramTransport
from app.execution.models import CampaignExecutionTask
from app.execution.exceptions import ExecutionEngineException
from app.core.config import settings

logger = logging.getLogger(__name__)


class ExecutionEngineService:
    """
    Orquestador central del motor de ejecución.
    
    Crea y gestiona todas las dependencias.
    
    Ejemplo:
        service = ExecutionEngineService(db_session)
        execution_id = await service.create_and_execute_campaign(
            campaign_id=42,
            user_id=5,
            tasks=[...],
            session_encrypted=b"...",
        )
    """

    def __init__(self, db_session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            db_session: Sesión AsyncSQL para persistencia
        """
        self.db_session = db_session
        self._repository: Optional[DatabaseExecutionRepository] = None
        self._queue_backend: Optional[RedisQueueBackend] = None
        self._queue_manager: Optional[QueueManager] = None
        self._campaign_manager: Optional[CampaignManager] = None

    async def initialize(self, redis_url: str = "redis://localhost") -> None:
        """
        Inicializa todos los componentes.

        Args:
            redis_url: URL de conexión a Redis
        """
        try:
            # Repositorio de BD
            self._repository = DatabaseExecutionRepository(self.db_session)
            
            # Backend de colas
            self._queue_backend = RedisQueueBackend(redis_url)
            await self._queue_backend.connect()
            
            # Gestor de colas
            self._queue_manager = QueueManager(self._queue_backend)
            
            # Gestor de campañas
            self._campaign_manager = CampaignManager(
                self._repository,
                self._queue_backend,
            )
            
            logger.info("Execution Engine Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Execution Engine Service: {e}")
            raise ExecutionEngineException(
                f"Failed to initialize service: {e}"
            )

    async def shutdown(self) -> None:
        """
        Desconecta recursos.
        """
        if self._queue_backend:
            await self._queue_backend.disconnect()
        logger.info("Execution Engine Service shut down")

    async def create_and_execute_campaign(
        self,
        campaign_id: int,
        user_id: int,
        tasks: list[CampaignExecutionTask],
        session_encrypted: bytes,
    ) -> str:
        """
        Crea una ejecución y encola todas las tareas.

        Args:
            campaign_id: ID de la campaña
            user_id: ID del usuario
            tasks: Lista de tareas a ejecutar
            session_encrypted: Sesión Telegram cifrada

        Returns:
            execution_id
        """
        if not self._campaign_manager:
            raise ExecutionEngineException("Service not initialized")
        
        try:
            # Crear ejecución
            execution_id = await self._campaign_manager.create_execution(
                campaign_id=campaign_id,
                user_id=user_id,
                tasks=tasks,
            )
            
            # Encolar tareas
            for task in tasks:
                await self._campaign_manager.enqueue_task(execution_id, task)
            
            # Iniciar
            await self._campaign_manager.start_execution(execution_id)
            
            logger.info(
                f"Campaign execution started: {execution_id}, "
                f"campaign {campaign_id}, user {user_id}, "
                f"tasks: {len(tasks)}"
            )
            
            return execution_id
        except Exception as e:
            logger.error(f"Failed to create and execute campaign: {e}")
            raise ExecutionEngineException(
                f"Failed to create and execute campaign: {e}"
            )

    async def create_task_processor(
        self,
        session_encrypted: bytes,
    ) -> TaskProcessor:
        """
        Crea un procesador de tareas con transporte Telegram.

        Args:
            session_encrypted: Sesión Telegram cifrada

        Returns:
            TaskProcessor listo para usar
        """
        if not self._queue_manager or not self._campaign_manager:
            raise ExecutionEngineException("Service not initialized")
        
        telegram_transport = TelegramTransport(session_encrypted)
        
        return TaskProcessor(
            queue_manager=self._queue_manager,
            campaign_manager=self._campaign_manager,
            message_transport=telegram_transport,
        )

    def get_campaign_manager(self) -> CampaignManager:
        """
        Retorna el gestor de campañas.
        """
        if not self._campaign_manager:
            raise ExecutionEngineException("Service not initialized")
        return self._campaign_manager

    def get_queue_manager(self) -> QueueManager:
        """
        Retorna el gestor de colas.
        """
        if not self._queue_manager:
            raise ExecutionEngineException("Service not initialized")
        return self._queue_manager

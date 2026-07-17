"""
Campaign Manager: Orquestador de ejecuciones de campañas.

Responsable de:
- Crear ejecuciones
- Controlar ciclo de vida
- Pausar/Reanudar/Cancelar
- Coordinar con queue manager
- Generar reportes de auditoría

Principios SOLID:
- Single Responsibility: solo gestiona ejecuciones, no transporte
- Open/Closed: extensible via inyección de dependencias
- Liskov Substitution: usa interfaces abstractas
- Interface Segregation: interfaces mínimas y focalizadas
- Dependency Inversion: depende de abstracciones, no implementaciones
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.execution.models import (
    ExecutionState,
    TaskState,
    CampaignExecutionTask,
    ExecutionAuditLog,
    TaskAuditLog,
)
from app.execution.exceptions import (
    InvalidStateTransitionException,
    CampaignExecutionException,
    ExecutionNotFoundException,
)
from app.execution.interfaces import ExecutionRepository, QueueBackend

logger = logging.getLogger(__name__)


class CampaignManager:
    """
    Gestor central del ciclo de vida de ejecuciones de campaña.
    
    Arquitectura desacoplada:
    - No conoce detalles de transporte (Telegram, etc)
    - No conoce detalles de almacenamiento (BD, Redis, etc)
    - Usa inyección de dependencias para abstracción
    
    Ejemplo de uso:
        manager = CampaignManager(repository, queue_manager)
        execution_id = await manager.create_execution(
            campaign_id=42,
            user_id=5,
            tasks=[
                CampaignExecutionTask(task_id="t1", ...),
                CampaignExecutionTask(task_id="t2", ...),
            ]
        )
        await manager.start_execution(execution_id)
        await manager.pause_execution(execution_id)
        await manager.resume_execution(execution_id)
        audit = await manager.get_audit_log(execution_id)
    """

    def __init__(
        self,
        repository: ExecutionRepository,
        queue_backend: QueueBackend,
    ):
        """
        Inicializa el Campaign Manager con sus dependencias.

        Args:
            repository: Implementación de ExecutionRepository
            queue_backend: Implementación de QueueBackend
        """
        self.repository = repository
        self.queue_backend = queue_backend
        self._executions_state: Dict[str, ExecutionState] = {}
        self._audit_logs: Dict[str, ExecutionAuditLog] = {}

    async def create_execution(
        self,
        campaign_id: int,
        user_id: int,
        tasks: List[CampaignExecutionTask],
    ) -> str:
        """
        Crea una nueva ejecución de campaña.

        Args:
            campaign_id: ID de la campaña
            user_id: ID del usuario propietario
            tasks: Lista de tareas a ejecutar (una por comunidad)

        Returns:
            execution_id: Identificador único de la ejecución

        Raises:
            CampaignExecutionException: Si falla la creación
        """
        try:
            execution_id = str(uuid4())
            
            # Crear registro en BD
            await self.repository.create_execution(
                campaign_id=campaign_id,
                user_id=user_id,
                task_count=len(tasks),
            )
            
            # Inicializar estado
            self._executions_state[execution_id] = ExecutionState.PENDING
            
            # Inicializar auditoría
            self._audit_logs[execution_id] = ExecutionAuditLog(
                execution_id=execution_id,
                campaign_id=campaign_id,
                user_id=user_id,
                total_tasks=len(tasks),
                status=ExecutionState.PENDING.value,
            )
            
            logger.info(
                f"Execution created: {execution_id} "
                f"for campaign {campaign_id}, user {user_id}, "
                f"tasks: {len(tasks)}"
            )
            
            return execution_id
        except Exception as e:
            logger.error(f"Failed to create execution: {e}")
            raise CampaignExecutionException(f"Failed to create execution: {e}")

    async def start_execution(self, execution_id: str) -> None:
        """
        Inicia una ejecución encolando todas las tareas.

        Args:
            execution_id: ID de la ejecución a iniciar

        Raises:
            ExecutionNotFoundException: Si no existe
            InvalidStateTransitionException: Si no puede iniciarse
        """
        if execution_id not in self._executions_state:
            raise ExecutionNotFoundException(f"Execution not found: {execution_id}")
        
        current_state = self._executions_state[execution_id]
        
        # Validar transición de estado
        if current_state != ExecutionState.PENDING:
            raise InvalidStateTransitionException(
                f"Cannot start execution in state {current_state.value}"
            )
        
        # Cambiar a PROCESSING
        self._executions_state[execution_id] = ExecutionState.PROCESSING
        audit = self._audit_logs[execution_id]
        audit.started_at = datetime.utcnow()
        audit.status = ExecutionState.PROCESSING.value
        
        await self.repository.update_execution_state(
            execution_id,
            ExecutionState.PROCESSING.value,
        )
        
        logger.info(f"Execution started: {execution_id}")

    async def pause_execution(self, execution_id: str) -> None:
        """
        Pausa una ejecución en progreso.
        
        Las tareas en procesamiento continuarán, pero no se encolaron nuevas.

        Args:
            execution_id: ID de la ejecución a pausar

        Raises:
            ExecutionNotFoundException: Si no existe
            InvalidStateTransitionException: Si no puede pausarse
        """
        if execution_id not in self._executions_state:
            raise ExecutionNotFoundException(f"Execution not found: {execution_id}")
        
        current_state = self._executions_state[execution_id]
        
        if current_state != ExecutionState.PROCESSING:
            raise InvalidStateTransitionException(
                f"Can only pause execution in PROCESSING state, current: {current_state.value}"
            )
        
        self._executions_state[execution_id] = ExecutionState.PAUSED
        await self.repository.update_execution_state(
            execution_id,
            ExecutionState.PAUSED.value,
        )
        
        logger.info(f"Execution paused: {execution_id}")

    async def resume_execution(self, execution_id: str) -> None:
        """
        Reanuda una ejecución pausada.

        Args:
            execution_id: ID de la ejecución a reanudar

        Raises:
            ExecutionNotFoundException: Si no existe
            InvalidStateTransitionException: Si no puede reanudarse
        """
        if execution_id not in self._executions_state:
            raise ExecutionNotFoundException(f"Execution not found: {execution_id}")
        
        current_state = self._executions_state[execution_id]
        
        if current_state != ExecutionState.PAUSED:
            raise InvalidStateTransitionException(
                f"Can only resume execution in PAUSED state, current: {current_state.value}"
            )
        
        self._executions_state[execution_id] = ExecutionState.PROCESSING
        await self.repository.update_execution_state(
            execution_id,
            ExecutionState.PROCESSING.value,
        )
        
        logger.info(f"Execution resumed: {execution_id}")

    async def cancel_execution(self, execution_id: str) -> None:
        """
        Cancela una ejecución.
        
        Las tareas ya encoladas pueden completarse, pero no se encolarán nuevas.

        Args:
            execution_id: ID de la ejecución a cancelar

        Raises:
            ExecutionNotFoundException: Si no existe
        """
        if execution_id not in self._executions_state:
            raise ExecutionNotFoundException(f"Execution not found: {execution_id}")
        
        self._executions_state[execution_id] = ExecutionState.CANCELLED
        await self.repository.update_execution_state(
            execution_id,
            ExecutionState.CANCELLED.value,
        )
        
        logger.info(f"Execution cancelled: {execution_id}")

    async def enqueue_task(
        self,
        execution_id: str,
        task: CampaignExecutionTask,
    ) -> None:
        """
        Encola una tarea para procesamiento.

        Args:
            execution_id: ID de la ejecución
            task: Tarea a encolar

        Raises:
            ExecutionNotFoundException: Si no existe
            CampaignExecutionException: Si falla el encolado
        """
        if execution_id not in self._executions_state:
            raise ExecutionNotFoundException(f"Execution not found: {execution_id}")
        
        try:
            queue_name = f"campaign-execution:{execution_id}"
            await self.queue_backend.enqueue(
                queue_name=queue_name,
                task_id=task.task_id,
                payload=task.to_dict(),
            )
            logger.debug(f"Task enqueued: {task.task_id} in execution {execution_id}")
        except Exception as e:
            logger.error(f"Failed to enqueue task {task.task_id}: {e}")
            raise CampaignExecutionException(f"Failed to enqueue task: {e}")

    async def record_task_start(
        self,
        execution_id: str,
        task_id: str,
        campaign_id: int,
        community_id: int,
    ) -> None:
        """
        Registra el inicio del procesamiento de una tarea.

        Args:
            execution_id: ID de la ejecución
            task_id: ID de la tarea
            campaign_id: ID de la campaña
            community_id: ID de la comunidad
        """
        if execution_id not in self._audit_logs:
            return
        
        audit = self._audit_logs[execution_id]
        task_log = TaskAuditLog(
            task_id=task_id,
            campaign_id=campaign_id,
            community_id=community_id,
            started_at=datetime.utcnow(),
            status=TaskState.PROCESSING.value,
        )
        audit.task_logs.append(task_log)
        
        logger.debug(f"Task started: {task_id}")

    async def record_task_completion(
        self,
        execution_id: str,
        task_id: str,
        message_id: str,
    ) -> None:
        """
        Registra la completación exitosa de una tarea.

        Args:
            execution_id: ID de la ejecución
            task_id: ID de la tarea
            message_id: ID del mensaje enviado
        """
        if execution_id not in self._audit_logs:
            return
        
        audit = self._audit_logs[execution_id]
        task_log = self._find_task_log(audit, task_id)
        
        if task_log:
            task_log.completed_at = datetime.utcnow()
            task_log.status = TaskState.COMPLETED.value
            task_log.message_id = message_id
            task_log.duration_ms = int(
                (task_log.completed_at - task_log.started_at).total_seconds() * 1000
            )
            audit.completed_tasks += 1
        
        logger.debug(f"Task completed: {task_id}, message_id: {message_id}")

    async def record_task_failure(
        self,
        execution_id: str,
        task_id: str,
        error: str,
        retry_count: int = 0,
    ) -> None:
        """
        Registra el fallo de una tarea.

        Args:
            execution_id: ID de la ejecución
            task_id: ID de la tarea
            error: Mensaje de error
            retry_count: Cantidad de reintentos
        """
        if execution_id not in self._audit_logs:
            return
        
        audit = self._audit_logs[execution_id]
        task_log = self._find_task_log(audit, task_id)
        
        if task_log:
            task_log.completed_at = datetime.utcnow()
            task_log.status = TaskState.FAILED.value
            task_log.retry_count = retry_count
            task_log.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": error,
            })
            if not (retry_count > 0):
                audit.failed_tasks += 1
        
        logger.debug(f"Task failed: {task_id}, error: {error}, retries: {retry_count}")

    async def finalize_execution(self, execution_id: str) -> ExecutionAuditLog:
        """
        Finaliza una ejecución calculando estado final.

        Returns:
            Reporte de auditoría con detalles completos

        Raises:
            ExecutionNotFoundException: Si no existe
        """
        if execution_id not in self._executions_state:
            raise ExecutionNotFoundException(f"Execution not found: {execution_id}")
        
        audit = self._audit_logs[execution_id]
        audit.completed_at = datetime.utcnow()
        audit.duration_ms = int(
            (audit.completed_at - audit.started_at).total_seconds() * 1000
        ) if audit.started_at else 0
        
        # Determinar estado final
        if audit.failed_tasks == 0:
            final_state = ExecutionState.COMPLETED
        elif audit.failed_tasks < audit.total_tasks:
            final_state = ExecutionState.PARTIAL_FAILURE
        else:
            final_state = ExecutionState.FAILED
        
        self._executions_state[execution_id] = final_state
        audit.status = final_state.value
        
        await self.repository.update_execution_state(
            execution_id,
            final_state.value,
        )
        
        logger.info(
            f"Execution finalized: {execution_id}, "
            f"status: {final_state.value}, "
            f"completed: {audit.completed_tasks}/{audit.total_tasks}, "
            f"failed: {audit.failed_tasks}, "
            f"duration: {audit.duration_ms}ms"
        )
        
        return audit

    async def get_execution_state(self, execution_id: str) -> ExecutionState:
        """
        Obtiene el estado actual de una ejecución.

        Returns:
            Estado actual

        Raises:
            ExecutionNotFoundException: Si no existe
        """
        if execution_id not in self._executions_state:
            raise ExecutionNotFoundException(f"Execution not found: {execution_id}")
        
        return self._executions_state[execution_id]

    async def get_audit_log(self, execution_id: str) -> ExecutionAuditLog:
        """
        Obtiene el reporte de auditoría de una ejecución.

        Returns:
            Reporte completo con detalles de todas las tareas

        Raises:
            ExecutionNotFoundException: Si no existe
        """
        if execution_id not in self._audit_logs:
            raise ExecutionNotFoundException(f"Execution not found: {execution_id}")
        
        return self._audit_logs[execution_id]

    def _find_task_log(self, audit: ExecutionAuditLog, task_id: str) -> Optional[TaskAuditLog]:
        """
        Busca un registro de tarea en auditoría.
        """
        for task_log in audit.task_logs:
            if task_log.task_id == task_id:
                return task_log
        return None

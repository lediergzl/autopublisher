"""
Modelos de datos para el motor de ejecución.

Define estados, esquemas y estructuras de datos.
"""

import enum
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from uuid import uuid4


class ExecutionState(str, enum.Enum):
    """
    Estados globales de una ejecución de campaña.
    
    PENDING: Esperando inicio
    PROCESSING: En proceso (algunas tareas activas)
    PAUSED: Pausada por usuario
    COMPLETED: Todas las tareas completadas exitosamente
    PARTIAL_FAILURE: Algunas tareas fallaron
    CANCELLED: Cancelada por usuario
    FAILED: Error crítico en toda la ejecución
    """
    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskState(str, enum.Enum):
    """
    Estados de una tarea individual (una comunidad en una campaña).
    
    PENDING: Esperando procesamiento
    PROCESSING: En proceso
    COMPLETED: Completada exitosamente
    FAILED: Falló
    RETRY: En cola para reintento
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class TaskAuditLog:
    """
    Registro de auditoría para una tarea individual.
    
    Ejemplo:
        {
            "task_id": "task-123",
            "campaign_id": 42,
            "community_id": 10,
            "started_at": "2024-01-15T10:30:00Z",
            "completed_at": "2024-01-15T10:30:05Z",
            "duration_ms": 5000,
            "status": "completed",
            "message_id": "msg-456",
            "retry_count": 0,
            "errors": [],
        }
    """
    task_id: str
    campaign_id: int
    community_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    status: str = "pending"
    message_id: Optional[str] = None
    retry_count: int = 0
    errors: list = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data


@dataclass
class ExecutionAuditLog:
    """
    Registro de auditoría para una ejecución completa.
    
    Ejemplo:
        {
            "execution_id": "exec-789",
            "campaign_id": 42,
            "user_id": 5,
            "started_at": "2024-01-15T10:00:00Z",
            "completed_at": "2024-01-15T10:05:30Z",
            "duration_ms": 330000,
            "total_tasks": 10,
            "completed_tasks": 9,
            "failed_tasks": 1,
            "status": "partial_failure",
            "task_logs": [...]
        }
    """
    execution_id: str
    campaign_id: int
    user_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    status: str = "pending"
    task_logs: list = None

    def __post_init__(self):
        if self.task_logs is None:
            self.task_logs = []

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        data["task_logs"] = [log.to_dict() if isinstance(log, TaskAuditLog) else log for log in self.task_logs]
        return data


@dataclass
class CampaignExecutionTask:
    """
    Estructura de una tarea de ejecución (una comunidad en una campaña).
    
    Payload que se encola en Redis.
    """
    task_id: str
    execution_id: str
    campaign_id: int
    user_id: int
    community_id: int
    content_id: int
    recipient_id: str  # telegram_chat_id
    content: str
    multimedia_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    max_retries: int = 3
    timeout_seconds: int = 30

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignExecutionTask":
        return cls(**data)

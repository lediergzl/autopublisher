"""
Campaign Execution Engine Module.

Núcleo del motor de ejecución de campañas con arquitectura desacoplada.
"""

from app.execution.manager import CampaignManager
from app.execution.models import ExecutionState, TaskState

__all__ = [
    "CampaignManager",
    "ExecutionState",
    "TaskState",
]

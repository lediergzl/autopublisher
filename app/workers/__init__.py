"""
Workers Module.

Workers independientes para procesar tareas de ejecución de campañas.
"""

from app.workers.task_processor import TaskProcessor
from app.workers.worker import Worker

__all__ = [
    "TaskProcessor",
    "Worker",
]

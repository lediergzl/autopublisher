"""
Redis Queue Backend Implementation.

Implementación concreta de QueueBackend usando Redis.

Estructura de datos en Redis:
- Colas: queue:execution:{execution_id} (lista)
- En procesamiento: processing:execution:{execution_id} (set)
- Completadas: completed:execution:{execution_id} (set)
- Fallidas: failed:execution:{execution_id} (set con score=retry_count)
- Metadata de tarea: task:{task_id} (hash)
"""

import logging
import json
from typing import Dict, Any, Optional
import aioredis

from app.execution.interfaces import QueueBackend
from app.execution.exceptions import QueueException

logger = logging.getLogger(__name__)


class RedisQueueBackend(QueueBackend):
    """
    Backend de colas basado en Redis.
    
    Características:
    - Cola de pendientes: FIFO
    - Seguimiento de estado: procesando, completadas, fallidas
    - Reintentos automáticos
    - Persistencia
    """

    def __init__(self, redis_url: str = "redis://localhost"):
        """
        Inicializa conexión a Redis.

        Args:
            redis_url: URL de conexión a Redis
        """
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """
        Establece conexión con Redis.
        """
        try:
            self.redis = await aioredis.from_url(self.redis_url)
            logger.info(f"Connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise QueueException(f"Failed to connect to Redis: {e}")

    async def disconnect(self) -> None:
        """
        Cierra conexión con Redis.
        """
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")

    async def enqueue(
        self,
        queue_name: str,
        task_id: str,
        payload: Dict[str, Any],
    ) -> None:
        """
        Encola una tarea.
        """
        if not self.redis:
            raise QueueException("Redis not connected")
        
        try:
            # Guardar payload
            await self.redis.hset(
                f"task:{task_id}",
                mapping={
                    "payload": json.dumps(payload),
                    "status": "pending",
                    "retry_count": 0,
                }
            )
            
            # Encolar
            await self.redis.rpush(queue_name, task_id)
            logger.debug(f"Task {task_id} enqueued to {queue_name}")
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_id}: {e}")
            raise QueueException(f"Failed to enqueue task: {e}")

    async def dequeue(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """
        Desencola una tarea del frente.
        """
        if not self.redis:
            raise QueueException("Redis not connected")
        
        try:
            task_id = await self.redis.lpop(queue_name)
            if not task_id:
                return None
            
            # Obtener payload
            task_data = await self.redis.hgetall(f"task:{task_id}")
            if task_data:
                payload = json.loads(task_data.get(b"payload", b"{}"))
                return {
                    "task_id": task_id,
                    **payload,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue from {queue_name}: {e}")
            raise QueueException(f"Failed to dequeue task: {e}")

    async def mark_processing(
        self,
        queue_name: str,
        task_id: str,
    ) -> None:
        """
        Marca una tarea como en procesamiento.
        """
        if not self.redis:
            raise QueueException("Redis not connected")
        
        try:
            await self.redis.hset(f"task:{task_id}", "status", "processing")
            await self.redis.sadd(f"processing:{queue_name}", task_id)
            logger.debug(f"Task {task_id} marked as processing")
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as processing: {e}")
            raise QueueException(f"Failed to mark task as processing: {e}")

    async def mark_completed(
        self,
        queue_name: str,
        task_id: str,
    ) -> None:
        """
        Marca una tarea como completada.
        """
        if not self.redis:
            raise QueueException("Redis not connected")
        
        try:
            await self.redis.hset(f"task:{task_id}", "status", "completed")
            await self.redis.srem(f"processing:{queue_name}", task_id)
            await self.redis.sadd(f"completed:{queue_name}", task_id)
            logger.debug(f"Task {task_id} marked as completed")
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as completed: {e}")
            raise QueueException(f"Failed to mark task as completed: {e}")

    async def mark_failed(
        self,
        queue_name: str,
        task_id: str,
        error: str,
        retry_count: int = 0,
    ) -> None:
        """
        Marca una tarea como fallida.
        
        Si hay reintentos disponibles, la reencola.
        """
        if not self.redis:
            raise QueueException("Redis not connected")
        
        try:
            max_retries = 3  # TODO: hacer configurable
            
            if retry_count < max_retries:
                # Reencolamos para reintento
                retry_count += 1
                await self.redis.hset(
                    f"task:{task_id}",
                    mapping={
                        "status": "retry",
                        "retry_count": retry_count,
                        "last_error": error,
                    }
                )
                await self.redis.rpush(queue_name, task_id)
                logger.debug(f"Task {task_id} requeued for retry {retry_count}/{max_retries}")
            else:
                # Fallida permanentemente
                await self.redis.hset(
                    f"task:{task_id}",
                    mapping={
                        "status": "failed",
                        "retry_count": retry_count,
                        "last_error": error,
                    }
                )
                await self.redis.srem(f"processing:{queue_name}", task_id)
                await self.redis.zadd(f"failed:{queue_name}", {task_id: retry_count})
                logger.debug(f"Task {task_id} marked as permanently failed")
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as failed: {e}")
            raise QueueException(f"Failed to mark task as failed: {e}")

    async def get_queue_length(self, queue_name: str) -> int:
        """
        Obtiene el tamaño de la cola.
        """
        if not self.redis:
            raise QueueException("Redis not connected")
        
        try:
            length = await self.redis.llen(queue_name)
            return length or 0
        except Exception as e:
            logger.error(f"Failed to get queue length for {queue_name}: {e}")
            raise QueueException(f"Failed to get queue length: {e}")

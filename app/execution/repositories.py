"""
Execution Repository Implementations.

Implementaciones concretas de ExecutionRepository usando SQLAlchemy.
"""

import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, update, select

from app.execution.interfaces import ExecutionRepository
from app.execution.models import ExecutionState, TaskState
from app.execution.exceptions import ExecutionNotFoundException

logger = logging.getLogger(__name__)

# Importar modelos de BD
from app.campaigns.models import Campaign, CampaignCommunity, PublicacionStatus


class DatabaseExecutionRepository(ExecutionRepository):
    """
    Repositorio de ejecuciones persistido en PostgreSQL.
    
    Utiliza SQLAlchemy async para almacenar:
    - Metadatos de ejecución
    - Estados de tareas
    - Registros de auditoría
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa repositorio con sesión de BD.

        Args:
            session: AsyncSession de SQLAlchemy
        """
        self.session = session

    async def create_execution(
        self,
        campaign_id: int,
        user_id: int,
        task_count: int,
    ) -> Dict[str, Any]:
        """
        Crea un nuevo registro de ejecución en BD.
        
        Actualiza el estado de la campaña a IN_PROGRESS.

        Returns:
            {
                "execution_id": "...",
                "campaign_id": 42,
                "user_id": 5,
                "task_count": 10,
            }
        """
        try:
            # Verificar que la campaña existe
            campaign_result = await self.session.execute(
                select(Campaign).where(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id,
                )
            )
            campaign = campaign_result.scalar_one_or_none()
            if not campaign:
                raise ExecutionNotFoundException(
                    f"Campaign {campaign_id} not found for user {user_id}"
                )
            
            # Actualizar estado de campaña
            from app.campaigns.models import CampaignStatus
            campaign.estado = CampaignStatus.in_progress
            self.session.add(campaign)
            await self.session.flush()
            
            logger.info(
                f"Execution created for campaign {campaign_id}, user {user_id}, "
                f"tasks: {task_count}"
            )
            
            return {
                "execution_id": str(campaign_id),
                "campaign_id": campaign_id,
                "user_id": user_id,
                "task_count": task_count,
            }
        except Exception as e:
            logger.error(f"Failed to create execution: {e}")
            raise

    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Obtiene los detalles de una ejecución.
        """
        try:
            campaign_id = int(execution_id)
            result = await self.session.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()
            if not campaign:
                raise ExecutionNotFoundException(
                    f"Execution {execution_id} not found"
                )
            
            # Contar tareas
            cc_result = await self.session.execute(
                select(CampaignCommunity).where(
                    CampaignCommunity.campaign_id == campaign_id
                )
            )
            tasks = list(cc_result.scalars().all())
            
            return {
                "execution_id": execution_id,
                "campaign_id": campaign.id,
                "user_id": campaign.user_id,
                "total_tasks": len(tasks),
                "state": campaign.estado.value,
            }
        except Exception as e:
            logger.error(f"Failed to get execution: {e}")
            raise

    async def update_execution_state(
        self,
        execution_id: str,
        state: str,
    ) -> None:
        """
        Actualiza el estado global de una ejecución.
        """
        try:
            campaign_id = int(execution_id)
            result = await self.session.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()
            if not campaign:
                raise ExecutionNotFoundException(
                    f"Execution {execution_id} not found"
                )
            
            # Mapear estado de ejecución a estado de campaña
            from app.campaigns.models import CampaignStatus
            if state == ExecutionState.COMPLETED.value:
                campaign.estado = CampaignStatus.done
            elif state == ExecutionState.PARTIAL_FAILURE.value:
                campaign.estado = CampaignStatus.in_progress
            elif state == ExecutionState.FAILED.value:
                campaign.estado = CampaignStatus.draft
            elif state == ExecutionState.CANCELLED.value:
                campaign.estado = CampaignStatus.draft
            
            self.session.add(campaign)
            await self.session.flush()
            logger.debug(f"Execution {execution_id} state updated to {state}")
        except Exception as e:
            logger.error(f"Failed to update execution state: {e}")
            raise

    async def record_task_audit(
        self,
        execution_id: str,
        task_id: str,
        event: str,
        details: Dict[str, Any],
    ) -> None:
        """
        Registra un evento de auditoría para una tarea.
        
        Actualiza el registro de CampaignCommunity en BD.
        """
        try:
            campaign_id = int(execution_id)
            community_id = int(task_id.split("-")[-1]) if "-" in task_id else None
            
            if not community_id:
                logger.warning(f"Cannot parse community_id from task_id: {task_id}")
                return
            
            cc_result = await self.session.execute(
                select(CampaignCommunity).where(
                    CampaignCommunity.campaign_id == campaign_id,
                    CampaignCommunity.community_id == community_id,
                )
            )
            campaign_community = cc_result.scalar_one_or_none()
            if not campaign_community:
                logger.warning(
                    f"CampaignCommunity not found: "
                    f"campaign {campaign_id}, community {community_id}"
                )
                return
            
            # Actualizar según evento
            if event == "completed":
                campaign_community.publicado = PublicacionStatus.publicado
                campaign_community.fecha_publicacion = datetime.utcnow()
            elif event == "failed":
                campaign_community.publicado = PublicacionStatus.error
                campaign_community.error_detalle = details.get("error", "Unknown error")
            
            self.session.add(campaign_community)
            await self.session.flush()
            logger.debug(
                f"Task audit recorded: campaign {campaign_id}, "
                f"community {community_id}, event: {event}"
            )
        except Exception as e:
            logger.error(f"Failed to record task audit: {e}")
            # No lanzar excepción para no romper la ejecución

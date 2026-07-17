from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_session
from app.core.deps import get_current_user
from app.analytics.models import ActivityLog
from app.analytics.schemas import ActivityLogOut, DashboardOut
from app.communities.models import Community
from app.content.models import Post
from app.campaigns.models import Campaign, CampaignStatus
from app.users.models import User

router = APIRouter(tags=["analytics"])


@router.get("/activity", response_model=list[ActivityLogOut])
async def get_activity(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(ActivityLog).where(ActivityLog.user_id == user.id).order_by(ActivityLog.fecha.desc()).limit(50)
    )
    return list(result.scalars().all())


@router.get("/dashboard", response_model=DashboardOut)
async def get_dashboard(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    comunidades = await session.scalar(
        select(func.count()).select_from(Community).where(Community.user_id == user.id)
    )
    publicaciones = await session.scalar(
        select(func.count()).select_from(Post).where(Post.user_id == user.id)
    )
    campanas_activas = await session.scalar(
        select(func.count()).select_from(Campaign).where(
            Campaign.user_id == user.id,
            Campaign.estado.in_([CampaignStatus.ready, CampaignStatus.in_progress]),
        )
    )
    actividad_result = await session.execute(
        select(ActivityLog).where(ActivityLog.user_id == user.id).order_by(ActivityLog.fecha.desc()).limit(10)
    )
    return DashboardOut(
        comunidades=comunidades or 0,
        publicaciones=publicaciones or 0,
        campanas_activas=campanas_activas or 0,
        actividad_reciente=list(actividad_result.scalars().all()),
    )

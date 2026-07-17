from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.core.deps import get_current_user
from app.communities import service
from app.communities.models import Community
from app.communities.schemas import CommunityOut, CommunityUpdate
from app.users.models import User

router = APIRouter(tags=["communities"])


@router.post("/sync", response_model=list[CommunityOut])
async def sync(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.sync_communities(session, user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("", response_model=list[CommunityOut])
async def list_communities(
    categoria: str | None = None,
    q: str | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Community).where(Community.user_id == user.id)
    if categoria:
        stmt = stmt.where(Community.categoria == categoria)
    if q:
        stmt = stmt.where(Community.nombre.ilike(f"%{q}%"))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.patch("/{community_id}", response_model=CommunityOut)
async def update_community(
    community_id: int,
    data: CommunityUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Community).where(Community.id == community_id, Community.user_id == user.id)
    )
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(404, "Comunidad no encontrada")

    if data.categoria is not None:
        community.categoria = data.categoria
    if data.estado is not None:
        community.estado = data.estado

    await session.commit()
    await session.refresh(community)
    return community

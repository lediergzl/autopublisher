from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.core.deps import get_current_user
from app.core.limits import check_limit
from app.campaigns.models import Campaign, CampaignCommunity, CampaignStatus, PublicacionStatus
from app.campaigns.schemas import CampaignCreate, CampaignOut
from app.content.models import Post
from app.content.service import render_post
from app.communities.models import Community
from app.telegram.models import TelegramSession
from app.telegram import service as tg_service
from app.analytics.models import ActivityLog
from app.users.models import User

router = APIRouter(tags=["campaigns"])


@router.post("", response_model=CampaignOut)
async def create_campaign(
    data: CampaignCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    post_result = await session.execute(
        select(Post).where(Post.id == data.contenido_id, Post.user_id == user.id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(404, "Publicación no encontrada")

    communities_result = await session.execute(
        select(Community).where(Community.id.in_(data.community_ids), Community.user_id == user.id)
    )
    valid_communities = list(communities_result.scalars().all())
    if len(valid_communities) != len(data.community_ids):
        raise HTTPException(400, "Alguna comunidad seleccionada no pertenece al usuario")

    campaign = Campaign(
        user_id=user.id,
        nombre=data.nombre,
        contenido_id=data.contenido_id,
        estado=CampaignStatus.ready,
        fecha_planeada=data.fecha_planeada,
    )
    session.add(campaign)
    await session.flush()  # obtiene campaign.id sin cerrar la transacción

    for community in valid_communities:
        session.add(CampaignCommunity(campaign_id=campaign.id, community_id=community.id))

    await session.commit()

    return await _get_campaign_full(session, campaign.id, user.id)


@router.get("", response_model=list[CampaignOut])
async def list_campaigns(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Campaign).where(Campaign.user_id == user.id))
    campaigns = list(result.scalars().all())
    out = []
    for c in campaigns:
        out.append(await _get_campaign_full(session, c.id, user.id))
    return out


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _get_campaign_full(session, campaign_id, user.id)


@router.post("/{campaign_id}/execute-one")
async def execute_one(
    campaign_id: int,
    community_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Publica el contenido de la campaña en UNA sola comunidad, con un click
    explícito del usuario. Este es el único mecanismo de publicación:
    no existe un disparador que envíe a todas las comunidades automáticamente.
    Protegido por rate limit anti-abuso.
    """
    check_limit(user.id)

    campaign_result = await session.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    )
    campaign = campaign_result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "Campaña no encontrada")

    cc_result = await session.execute(
        select(CampaignCommunity).where(
            CampaignCommunity.campaign_id == campaign_id,
            CampaignCommunity.community_id == community_id,
        )
    )
    campaign_community = cc_result.scalar_one_or_none()
    if not campaign_community:
        raise HTTPException(404, "Esta comunidad no forma parte de la campaña")

    if campaign_community.publicado == PublicacionStatus.publicado:
        raise HTTPException(400, "Ya fue publicado en esta comunidad")

    post_result = await session.execute(select(Post).where(Post.id == campaign.contenido_id))
    post = post_result.scalar_one_or_none()

    community_result = await session.execute(select(Community).where(Community.id == community_id))
    community = community_result.scalar_one_or_none()

    tg_session_result = await session.execute(
        select(TelegramSession).where(TelegramSession.user_id == user.id)
    )
    tg_session = tg_session_result.scalar_one_or_none()
    if not tg_session:
        raise HTTPException(400, "Cuenta de Telegram no conectada")

    texto = render_post(post.contenido, {})

    try:
        client = await tg_service.get_client(tg_session.session_encrypted)
        try:
            if post.multimedia:
                await client.send_file(int(community.telegram_chat_id), post.multimedia, caption=texto, parse_mode="md")
            else:
                await client.send_message(int(community.telegram_chat_id), texto, parse_mode="md")
        finally:
            await client.disconnect()

        campaign_community.publicado = PublicacionStatus.publicado
        campaign_community.fecha_publicacion = datetime.utcnow()
        session.add(ActivityLog(
            user_id=user.id, campaign_id=campaign_id, community_id=community_id,
            estado="publicado",
        ))
    except Exception as e:
        campaign_community.publicado = PublicacionStatus.error
        campaign_community.error_detalle = str(e)
        session.add(ActivityLog(
            user_id=user.id, campaign_id=campaign_id, community_id=community_id,
            estado="error",
        ))
        await session.commit()
        raise HTTPException(500, f"Error al publicar: {e}")

    # actualiza estado global de la campaña
    all_cc_result = await session.execute(
        select(CampaignCommunity).where(CampaignCommunity.campaign_id == campaign_id)
    )
    all_cc = list(all_cc_result.scalars().all())
    if all(cc.publicado == PublicacionStatus.publicado for cc in all_cc):
        campaign.estado = CampaignStatus.done
    else:
        campaign.estado = CampaignStatus.in_progress

    await session.commit()
    return {"status": "publicado", "community_id": community_id}


async def _get_campaign_full(session: AsyncSession, campaign_id: int, user_id: int) -> Campaign:
    result = await session.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "Campaña no encontrada")

    cc_result = await session.execute(
        select(CampaignCommunity).where(CampaignCommunity.campaign_id == campaign_id)
    )
    campaign.comunidades = list(cc_result.scalars().all())
    return campaign

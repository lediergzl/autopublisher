from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.communities.models import Community
from app.telegram.models import TelegramSession
from app.telegram import service as tg_service


async def sync_communities(session: AsyncSession, user_id: int) -> list[Community]:
    """
    Lee las comunidades (grupos/canales) a las que el usuario YA pertenece
    en su propia cuenta de Telegram, y las sincroniza en la DB local.
    No busca ni sugiere comunidades externas para unirse.
    """
    result = await session.execute(
        select(TelegramSession).where(TelegramSession.user_id == user_id)
    )
    tg_session = result.scalar_one_or_none()
    if not tg_session:
        raise ValueError("El usuario no ha conectado su cuenta de Telegram")

    client = await tg_service.get_client(tg_session.session_encrypted)
    try:
        dialogs = await client.get_dialogs()
    finally:
        await client.disconnect()

    existing_result = await session.execute(
        select(Community).where(Community.user_id == user_id)
    )
    existing_by_chat = {c.telegram_chat_id: c for c in existing_result.scalars().all()}

    for d in dialogs:
        if not (d.is_group or d.is_channel):
            continue
        chat_id = str(d.id)
        if chat_id in existing_by_chat:
            existing_by_chat[chat_id].nombre = d.name
        else:
            nueva = Community(user_id=user_id, telegram_chat_id=chat_id, nombre=d.name)
            session.add(nueva)

    await session.commit()

    result = await session.execute(select(Community).where(Community.user_id == user_id))
    return list(result.scalars().all())

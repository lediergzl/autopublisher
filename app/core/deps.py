from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.core.config import settings
from app.telegram.auth import verify_init_data
from app.users.models import User


async def get_current_user(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    session: AsyncSession = Depends(get_session),
) -> User:
    data = verify_init_data(x_telegram_init_data, settings.bot_token)
    if not data:
        raise HTTPException(401, "Init data inválida o expirada")

    tg_user = data.get("user", {})
    telegram_id = str(tg_user.get("id"))
    if not telegram_id or telegram_id == "None":
        raise HTTPException(401, "No se pudo identificar al usuario")

    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(telegram_id=telegram_id, username=tg_user.get("username"))
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user

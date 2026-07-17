from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.core.deps import get_current_user
from app.telegram import service
from app.telegram.models import TelegramSession
from app.telegram.schemas import LoginStartIn, LoginStartOut, LoginCompleteIn
from app.users.models import User

router = APIRouter(tags=["telegram-auth"])


@router.post("/login-start", response_model=LoginStartOut)
async def login_start(data: LoginStartIn, user: User = Depends(get_current_user)):
    session_temporal, phone_code_hash = await service.start_login(data.phone)
    return LoginStartOut(session_temporal=session_temporal, phone_code_hash=phone_code_hash)


@router.post("/login-complete")
async def login_complete(
    data: LoginCompleteIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        encrypted = await service.complete_login(
            data.session_temporal, data.phone, data.code, data.phone_code_hash
        )
    except Exception as e:
        raise HTTPException(400, f"No se pudo completar el login: {e}")

    result = await session.execute(
        select(TelegramSession).where(TelegramSession.user_id == user.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.session_encrypted = encrypted
        existing.phone = data.phone
    else:
        session.add(TelegramSession(user_id=user.id, session_encrypted=encrypted, phone=data.phone))

    await session.commit()
    return {"status": "conectado"}


@router.get("/status")
async def login_status(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(TelegramSession).where(TelegramSession.user_id == user.id)
    )
    existing = result.scalar_one_or_none()
    return {"conectado": existing is not None}

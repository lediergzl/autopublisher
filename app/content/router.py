from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.core.deps import get_current_user
from app.content.models import Post
from app.content.schemas import PostCreate, PostUpdate, PostOut, PostPreview
from app.content.service import render_post
from app.users.models import User

router = APIRouter(tags=["content"])


@router.post("", response_model=PostOut)
async def create_post(
    data: PostCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    post = Post(user_id=user.id, **data.model_dump())
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@router.get("", response_model=list[PostOut])
async def list_posts(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Post).where(Post.user_id == user.id))
    return list(result.scalars().all())


@router.get("/{post_id}", response_model=PostOut)
async def get_post(
    post_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Publicación no encontrada")
    return post


@router.patch("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    data: PostUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Publicación no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    await session.commit()
    await session.refresh(post)
    return post


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Publicación no encontrada")
    await session.delete(post)
    await session.commit()
    return {"status": "eliminado"}


@router.post("/{post_id}/preview")
async def preview_post(
    post_id: int,
    data: PostPreview,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Publicación no encontrada")
    return {"preview": render_post(post.contenido, data.variables)}

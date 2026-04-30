from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas.auth import UserAdminCreate, UserAdminUpdate
from app.security import hash_password


def _now() -> datetime:
    # Колонка users.created_at/updated_at — TIMESTAMP WITHOUT TIME ZONE,
    # asyncpg отказывается биндить tz-aware значения.
    return datetime.utcnow()


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id.desc()))
    return list(result.scalars().all())


async def create_user(db: AsyncSession, data: UserAdminCreate) -> User:
    existing = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        is_active=1 if data.is_active else 0,
        is_admin=1 if data.is_admin else 0,
        created_at=_now(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession, user_id: int, data: UserAdminUpdate
) -> User:
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if data.email is not None and data.email != user.email:
        # уникальность email среди других юзеров
        clash = (
            await db.execute(
                select(User).where(User.email == data.email, User.id != user_id)
            )
        ).scalar_one_or_none()
        if clash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        user.email = data.email

    if data.full_name is not None:
        user.full_name = data.full_name

    if data.password is not None and data.password != "":
        user.password_hash = hash_password(data.password)

    if data.is_active is not None:
        user.is_active = 1 if data.is_active else 0

    if data.is_admin is not None:
        user.is_admin = 1 if data.is_admin else 0

    user.updated_at = _now()

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> None:
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await db.delete(user)
    await db.commit()

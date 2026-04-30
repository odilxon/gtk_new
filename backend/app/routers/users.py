from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas.auth import UserAdminCreate, UserAdminResponse, UserAdminUpdate
from app.security import get_current_admin
from app.services import users as users_service

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=list[UserAdminResponse])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[User]:
    return await users_service.list_users(db)


@router.post("", response_model=UserAdminResponse, status_code=201)
async def create_user(
    data: UserAdminCreate, db: AsyncSession = Depends(get_db)
) -> User:
    return await users_service.create_user(db, data)


@router.patch("/{user_id}", response_model=UserAdminResponse)
async def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_admin),
) -> User:
    # Себя нельзя разжаловать или деактивировать — иначе можно потерять
    # последний админ-доступ.
    if user_id == me.id:
        if data.is_admin is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revoke admin from yourself",
            )
        if data.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself",
            )
    return await users_service.update_user(db, user_id, data)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_admin),
) -> None:
    if user_id == me.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    await users_service.delete_user(db, user_id)

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import require_role
from core.limits import get_limits
from db import get_db
from models import SystemLimit, User
from schemas import SystemLimitResponse, SystemLimitUpdate, UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserResponse])
async def list_all_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> list[User]:
    return list((await db.execute(select(User))).scalars().all())


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> Response:
    if user_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "An admin cannot delete their own account")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    await db.delete(user)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/limits", response_model=SystemLimitResponse)
async def read_limits(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> SystemLimit:
    return await get_limits(db)


@router.put("/limits", response_model=SystemLimitResponse)
async def update_limits(
    data: SystemLimitUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> SystemLimit:
    limits = await get_limits(db)
    for field, value in data.model_dump().items():
        setattr(limits, field, value)
    await db.commit()
    await db.refresh(limits)
    return limits

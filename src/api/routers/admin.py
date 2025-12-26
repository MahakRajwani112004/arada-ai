"""Admin API router for superuser operations."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentSuperuser
from src.auth.schemas import (
    PasswordResetByAdmin,
    UserAdminResponse,
    UserListResponse,
    UserStatusUpdate,
    UserUpdateByAdmin,
)
from src.auth.service import AuthService
from src.config.logging import get_logger
from src.storage.database import get_session

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    current_user: CurrentSuperuser,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """List all users with pagination (superuser only)."""
    auth_service = AuthService(session)

    skip = (page - 1) * limit
    users, total = await auth_service.list_all_users(skip=skip, limit=limit)

    logger.info(
        "admin_list_users",
        admin_id=current_user.id,
        page=page,
        limit=limit,
        total=total,
    )

    return UserListResponse(
        users=[UserAdminResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user(
    user_id: str,
    current_user: CurrentSuperuser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get a specific user by ID (superuser only)."""
    auth_service = AuthService(session)

    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    logger.info(
        "admin_get_user",
        admin_id=current_user.id,
        target_user_id=user_id,
    )

    return UserAdminResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserAdminResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdateByAdmin,
    current_user: CurrentSuperuser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update a user's profile (superuser only)."""
    auth_service = AuthService(session)

    try:
        user = await auth_service.update_user_by_admin(
            user_id=user_id,
            email=update_data.email,
            display_name=update_data.display_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    logger.info(
        "admin_update_user",
        admin_id=current_user.id,
        target_user_id=user_id,
        updated_fields=update_data.model_dump(exclude_none=True),
    )

    return UserAdminResponse.model_validate(user)


@router.put("/users/{user_id}/password")
async def reset_user_password(
    user_id: str,
    password_data: PasswordResetByAdmin,
    current_user: CurrentSuperuser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Reset a user's password (superuser only)."""
    auth_service = AuthService(session)

    try:
        await auth_service.reset_user_password(
            user_id=user_id,
            new_password=password_data.new_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    logger.info(
        "admin_reset_password",
        admin_id=current_user.id,
        target_user_id=user_id,
    )

    return {"message": "Password reset successfully"}


@router.put("/users/{user_id}/status", response_model=UserAdminResponse)
async def toggle_user_status(
    user_id: str,
    status_data: UserStatusUpdate,
    current_user: CurrentSuperuser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Activate or deactivate a user (superuser only)."""
    # Prevent self-deactivation
    if user_id == current_user.id and not status_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    auth_service = AuthService(session)

    try:
        user = await auth_service.toggle_user_status(
            user_id=user_id,
            is_active=status_data.is_active,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    action = "activated" if status_data.is_active else "deactivated"
    logger.info(
        f"admin_user_{action}",
        admin_id=current_user.id,
        target_user_id=user_id,
    )

    return UserAdminResponse.model_validate(user)

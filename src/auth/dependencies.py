"""FastAPI authentication dependencies."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt_handler import decode_token
from src.auth.schemas import UserMe
from src.storage.database import get_session
from src.storage.models import UserModel

# Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserMe:
    """Get the current authenticated user from JWT token.

    Args:
        credentials: Bearer token from Authorization header
        session: Database session

    Returns:
        Current user info

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Decode the JWT token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database to ensure they still exist and are active
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserMe(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_superuser=user.is_superuser,
        org_id=user.org_id,
    )


async def get_current_superuser(
    current_user: Annotated[UserMe, Depends(get_current_user)],
) -> UserMe:
    """Get the current user and verify they are a superuser.

    Args:
        current_user: Current authenticated user

    Returns:
        Current superuser info

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return current_user


# Type aliases for dependency injection
CurrentUser = Annotated[UserMe, Depends(get_current_user)]
CurrentSuperuser = Annotated[UserMe, Depends(get_current_superuser)]

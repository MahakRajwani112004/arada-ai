"""Authentication API router."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser, CurrentSuperuser
from src.auth.schemas import (
    InviteCreate,
    InviteResponse,
    InviteValidate,
    InviteValidateResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserMe,
    UserResponse,
)
from src.auth.service import AuthService
from src.config.logging import get_logger
from src.storage.database import get_session

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Login with email and password.

    Returns access and refresh tokens.
    """
    auth_service = AuthService(session)

    user = await auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password,
    )

    if user is None:
        logger.warning(
            "login_failed",
            email=credentials.email,
            reason="invalid_credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    tokens = await auth_service.create_tokens(user)

    logger.info(
        "user_logged_in",
        user_id=user.id,
        email=user.email,
        org_id=user.org_id,
    )

    return tokens


@router.post("/signup", response_model=TokenResponse)
async def signup(
    user_data: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Register a new user (open signup).

    Creates a new user account with email and password.
    """
    auth_service = AuthService(session)

    # Check if user already exists
    existing_user = await auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Create user
    user = await auth_service.create_user(
        email=user_data.email,
        password=user_data.password,
        display_name=user_data.display_name,
    )

    # Create tokens
    tokens = await auth_service.create_tokens(user)

    logger.info("user_registered", user_id=user.id, email=user.email)

    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Refresh access token using a refresh token.

    The old refresh token is revoked and a new one is issued.
    """
    auth_service = AuthService(session)

    tokens = await auth_service.refresh_tokens(request.refresh_token)

    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return tokens


@router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Logout by revoking the refresh token."""
    auth_service = AuthService(session)

    await auth_service.revoke_refresh_token(request.refresh_token)

    logger.info("user_logged_out")

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserMe)
async def get_current_user_info(current_user: CurrentUser):
    """Get current authenticated user info."""
    return current_user


# ============ Invite Endpoints (Superuser only) ============


@router.post("/invite", response_model=InviteResponse)
async def create_invite(
    invite_data: InviteCreate,
    current_user: CurrentSuperuser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create an invite for a new user.

    Only superusers can create invites.
    """
    auth_service = AuthService(session)

    try:
        invite = await auth_service.create_invite(
            email=invite_data.email,
            invited_by=current_user.id,
            org_id=current_user.org_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    logger.info(
        "invite_created",
        invite_id=invite.id,
        email=invite.email,
        invited_by=current_user.id,
    )

    return invite


@router.post("/invite/validate", response_model=InviteValidateResponse)
async def validate_invite(
    request: InviteValidate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Validate an invite code (public endpoint).

    Used by frontend to check if invite is valid before showing signup form.
    """
    auth_service = AuthService(session)

    invite = await auth_service.validate_invite(request.invite_code)

    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invite code",
        )

    return InviteValidateResponse(
        valid=True,
        email=invite.email,
        expires_at=invite.expires_at,
    )

"""OAuth callback endpoints for Google services."""
import os
import uuid
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from pydantic import BaseModel

from src.config.logging import get_logger
from src.secrets import get_secrets_manager

router = APIRouter(prefix="/oauth", tags=["oauth"])
logger = get_logger(__name__)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/oauth/google/callback")

# Scopes for different services
GOOGLE_SCOPES = {
    "calendar": ["https://www.googleapis.com/auth/calendar"],
    "gmail": [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
    ],
    "drive": ["https://www.googleapis.com/auth/drive"],
}


class TokenResponse(BaseModel):
    """Response containing token reference (not the actual token)."""
    token_ref: str
    service: str
    message: str


async def get_oauth_credentials(token_ref: str) -> Dict[str, str]:
    """Retrieve OAuth credentials from secure storage.

    This is for internal use only - never expose refresh tokens to clients.

    Args:
        token_ref: The token reference returned from OAuth callback

    Returns:
        Dictionary with refresh_token and service

    Raises:
        KeyError: If token reference not found
    """
    secrets_manager = get_secrets_manager()
    return await secrets_manager.retrieve(token_ref)


def _create_google_flow(scopes: list[str]) -> Flow:
    """Create Google OAuth flow."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )

    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [OAUTH_REDIRECT_URI],
        }
    }

    return Flow.from_client_config(
        client_config,
        scopes=scopes,
        redirect_uri=OAUTH_REDIRECT_URI,
    )


@router.get("/google/authorize")
async def google_authorize(
    service: str = Query(..., description="Service to authorize: calendar, gmail, drive"),
    state: Optional[str] = Query(None, description="Optional state to pass through"),
):
    """
    Start Google OAuth flow.

    Redirects user to Google consent screen.
    After authorization, Google redirects to /oauth/google/callback
    """
    if service not in GOOGLE_SCOPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service. Choose from: {list(GOOGLE_SCOPES.keys())}"
        )

    scopes = GOOGLE_SCOPES[service]
    flow = _create_google_flow(scopes)

    # Include service in state so callback knows which service was authorized
    combined_state = f"{service}:{state}" if state else service

    auth_url, _ = flow.authorization_url(
        access_type="offline",  # Required to get refresh_token
        include_granted_scopes="true",
        prompt="consent",  # Force consent to always get refresh_token
        state=combined_state,
    )

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State passed through OAuth"),
    error: Optional[str] = Query(None, description="Error from Google"),
):
    """
    Google OAuth callback.

    Exchanges authorization code for tokens and returns the refresh_token.
    In production, this would store the token in vault and redirect to UI.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    # Parse service from state
    service = "calendar"  # default
    user_state = None
    if state:
        parts = state.split(":", 1)
        service = parts[0]
        user_state = parts[1] if len(parts) > 1 else None

    if service not in GOOGLE_SCOPES:
        service = "calendar"

    scopes = GOOGLE_SCOPES[service]
    flow = _create_google_flow(scopes)

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {str(e)}")

    credentials = flow.credentials

    if not credentials.refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No refresh token received. User may have already authorized. Revoke access at https://myaccount.google.com/permissions and try again."
        )

    # Store refresh token securely in vault
    secrets_manager = get_secrets_manager()
    token_ref = f"oauth_google_{service}_{uuid.uuid4().hex[:12]}"

    try:
        await secrets_manager.store(
            key=token_ref,
            value={
                "refresh_token": credentials.refresh_token,
                "service": service,
                "provider": "google",
            }
        )
        logger.info("oauth_token_stored", service=service, token_ref=token_ref)
    except Exception as e:
        logger.error("oauth_token_storage_failed", service=service, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to store OAuth credentials securely"
        )

    # Return only the token reference - never the actual refresh token
    return TokenResponse(
        token_ref=token_ref,
        service=service,
        message=f"Successfully authorized {service}. Use token_ref '{token_ref}' to access this service."
    )


@router.get("/google/authorize-url")
async def get_authorize_url(
    service: str = Query(..., description="Service to authorize: calendar, gmail, drive"),
    redirect_after: Optional[str] = Query(None, description="URL to redirect after OAuth"),
):
    """
    Get the authorization URL without redirecting.

    Useful for SPAs that want to handle the redirect themselves.
    """
    if service not in GOOGLE_SCOPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service. Choose from: {list(GOOGLE_SCOPES.keys())}"
        )

    scopes = GOOGLE_SCOPES[service]
    flow = _create_google_flow(scopes)

    state = f"{service}:{redirect_after}" if redirect_after else service

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )

    return {"authorization_url": auth_url, "service": service}

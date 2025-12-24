"""OAuth callback endpoints for Google services."""
import os
import uuid
from typing import Dict, Optional
from urllib.parse import urlencode

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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

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
        prompt="consent",  # Force consent to always get refresh_token
        state=combined_state,
    )

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = Query(None, description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State passed through OAuth"),
    error: Optional[str] = Query(None, description="Error from Google"),
):
    """
    Google OAuth callback.

    Exchanges authorization code for tokens, stores in vault, and redirects to frontend.
    Handles both new connections and reconnections (credential updates).
    """
    # Parse state: format is "service" or "service:reconnect:server_id"
    service = "calendar"  # default
    is_reconnect = False
    server_id = None

    if state:
        parts = state.split(":")
        service = parts[0]
        if len(parts) >= 3 and parts[1] == "reconnect":
            is_reconnect = True
            server_id = parts[2]

    if service not in GOOGLE_SCOPES:
        service = "calendar"

    # Determine redirect URL based on reconnect or new connection
    callback_path = "/oauth/callback"

    # Handle OAuth errors - redirect to frontend with error
    if error:
        params = urlencode({"error": error, "service": service})
        if is_reconnect and server_id:
            params = urlencode({"error": error, "service": service, "server_id": server_id, "reconnect": "true"})
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    if not code:
        params = urlencode({"error": "No authorization code received", "service": service})
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    scopes = GOOGLE_SCOPES[service]
    flow = _create_google_flow(scopes)

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        logger.error("oauth_token_exchange_failed", service=service, error=str(e))
        params = urlencode({"error": f"Failed to exchange code: {str(e)}", "service": service})
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    credentials = flow.credentials

    if not credentials.refresh_token:
        params = urlencode({
            "error": "No refresh token received. Please revoke access at https://myaccount.google.com/permissions and try again.",
            "service": service
        })
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    # Store refresh token securely in vault
    secrets_manager = get_secrets_manager()
    token_ref = f"oauth_google_{service}_{uuid.uuid4().hex[:12]}"

    try:
        await secrets_manager.store(
            ref=token_ref,
            data={
                "refresh_token": credentials.refresh_token,
                "service": service,
                "provider": "google",
            }
        )
        logger.info("oauth_token_stored", service=service, token_ref=token_ref, is_reconnect=is_reconnect)
    except Exception as e:
        logger.error("oauth_token_storage_failed", service=service, error=str(e))
        params = urlencode({"error": "Failed to store OAuth credentials securely", "service": service})
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    # Redirect to frontend with token reference
    if is_reconnect and server_id:
        params = urlencode({
            "token_ref": token_ref,
            "service": service,
            "server_id": server_id,
            "reconnect": "true",
        })
    else:
        params = urlencode({"token_ref": token_ref, "service": service})

    return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")


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
        prompt="consent",
        state=state,
    )

    return {"authorization_url": auth_url, "service": service}

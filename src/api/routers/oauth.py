"""OAuth callback endpoints for Google and Microsoft services."""
import base64
import json
import os
import uuid
from typing import Dict, Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from pydantic import BaseModel

from src.auth.dependencies import CurrentUser
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

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")
MICROSOFT_OAUTH_REDIRECT_URI = os.getenv(
    "MICROSOFT_OAUTH_REDIRECT_URI",
    "http://localhost:8000/api/v1/oauth/microsoft/callback"
)
MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

# Microsoft Graph API scopes for different services
MICROSOFT_SCOPES = {
    "calendar": ["Calendars.ReadWrite", "offline_access"],
    "email": ["Mail.ReadWrite", "Mail.Send", "offline_access"],
    "sharepoint": ["Sites.ReadWrite.All", "Files.ReadWrite.All", "offline_access"],
    "onedrive": ["Files.ReadWrite.All", "offline_access"],
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


def _encode_oauth_state(user_id: str, service: str, extra_state: Optional[str] = None) -> str:
    """Encode user_id and service into OAuth state parameter."""
    state_data = {
        "user_id": user_id,
        "service": service,
        "extra": extra_state,
    }
    return base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()


def _decode_oauth_state(state: str) -> dict:
    """Decode OAuth state parameter to extract user_id and service."""
    try:
        state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
        return state_data
    except Exception:
        # Fallback for legacy state format (just service name)
        return {"user_id": None, "service": state, "extra": None}


@router.get("/google/authorize")
async def google_authorize(
    current_user: CurrentUser,
    service: str = Query(..., description="Service to authorize: calendar, gmail, drive"),
    state: Optional[str] = Query(None, description="Optional state to pass through"),
):
    """
    Start Google OAuth flow.

    Requires authentication to track which user is authorizing.
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

    # Encode user_id in state for secure retrieval in callback
    combined_state = _encode_oauth_state(str(current_user.id), service, state)

    auth_url, _ = flow.authorization_url(
        access_type="offline",  # Required to get refresh_token
        prompt="select_account",  # Force consent to always get refresh_token
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
    Tokens are stored under user-specific paths for security isolation.
    """
    # Parse state to extract user_id and service
    service = "calendar"  # default
    user_id = None
    is_reconnect = False
    server_id = None

    if state:
        state_data = _decode_oauth_state(state)
        user_id = state_data.get("user_id")
        service = state_data.get("service", "calendar")
        extra = state_data.get("extra")

        # Check if this is a reconnect flow
        if extra and extra.startswith("reconnect:"):
            is_reconnect = True
            server_id = extra.split(":", 1)[1] if ":" in extra else None

    if service not in GOOGLE_SCOPES:
        service = "calendar"

    # Ensure we have a user_id for secure storage
    if not user_id:
        logger.warning("oauth_callback_missing_user_id", service=service)
        params = urlencode({
            "error": "OAuth session expired or invalid. Please try again.",
            "service": service
        })
        return RedirectResponse(url=f"{FRONTEND_URL}/oauth/callback?{params}")

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

    # Store refresh token securely in vault under user-specific path
    secrets_manager = get_secrets_manager()
    # Use user-scoped path for proper isolation
    token_ref = f"users/{user_id}/oauth/google/{service}/{uuid.uuid4().hex}"

    try:
        await secrets_manager.store(
            key=token_ref,
            value={
                "refresh_token": credentials.refresh_token,
                "service": service,
                "provider": "google",
                "user_id": user_id,  # Store user_id for validation
            }
        )
        logger.info("oauth_token_stored", service=service, token_ref=token_ref, user_id=user_id, is_reconnect=is_reconnect)
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
    current_user: CurrentUser,
    service: str = Query(..., description="Service to authorize: calendar, gmail, drive"),
    redirect_after: Optional[str] = Query(None, description="URL to redirect after OAuth"),
):
    """
    Get the authorization URL without redirecting.

    Requires authentication to track which user is authorizing.
    Useful for SPAs that want to handle the redirect themselves.
    """
    if service not in GOOGLE_SCOPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service. Choose from: {list(GOOGLE_SCOPES.keys())}"
        )

    scopes = GOOGLE_SCOPES[service]
    flow = _create_google_flow(scopes)

    # Encode user_id in state for secure retrieval in callback
    state = _encode_oauth_state(str(current_user.id), service, redirect_after)

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="select_account",
        state=state,
    )

    return {"authorization_url": auth_url, "service": service}


# =============================================================================
# Microsoft OAuth Endpoints
# =============================================================================


@router.get("/microsoft/authorize-url")
async def get_microsoft_authorize_url(
    current_user: CurrentUser,
    service: str = Query(..., description="Service to authorize: calendar, email, sharepoint, onedrive"),
    redirect_after: Optional[str] = Query(None, description="URL to redirect after OAuth"),
):
    """
    Get the Microsoft authorization URL without redirecting.

    Requires authentication to track which user is authorizing.
    Useful for SPAs that want to handle the redirect themselves.
    """
    if service not in MICROSOFT_SCOPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service. Choose from: {list(MICROSOFT_SCOPES.keys())}"
        )

    if not MICROSOFT_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Microsoft OAuth not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET."
        )

    scopes = MICROSOFT_SCOPES[service]
    state = _encode_oauth_state(str(current_user.id), f"microsoft-{service}", redirect_after)

    params = {
        "client_id": MICROSOFT_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": MICROSOFT_OAUTH_REDIRECT_URI,
        "response_mode": "query",
        "scope": " ".join(scopes),
        "state": state,
        "prompt": "select_account",  # Force consent to get refresh token
    }

    auth_url = f"{MICROSOFT_AUTH_URL.format(tenant=MICROSOFT_TENANT_ID)}?{urlencode(params)}"
    return {"authorization_url": auth_url, "service": f"outlook-{service}"}


@router.get("/microsoft/authorize")
async def microsoft_authorize(
    current_user: CurrentUser,
    service: str = Query(..., description="Service to authorize: calendar, email, sharepoint, onedrive"),
    state: Optional[str] = Query(None, description="Optional state to pass through"),
):
    """
    Start Microsoft OAuth flow.

    Requires authentication to track which user is authorizing.
    Redirects user to Microsoft consent screen.
    After authorization, Microsoft redirects to /oauth/microsoft/callback
    """
    result = await get_microsoft_authorize_url(current_user, service, state)
    return RedirectResponse(url=result["authorization_url"])


@router.get("/microsoft/callback")
async def microsoft_callback(
    code: Optional[str] = Query(None, description="Authorization code from Microsoft"),
    state: Optional[str] = Query(None, description="State passed through OAuth"),
    error: Optional[str] = Query(None, description="Error from Microsoft"),
    error_description: Optional[str] = Query(None, description="Error description"),
):
    """
    Microsoft OAuth callback.

    Exchanges authorization code for tokens, stores in vault, and redirects to frontend.
    Handles both new connections and reconnections (credential updates).
    Tokens are stored under user-specific paths for security isolation.
    """
    # Parse state to extract user_id and service
    service = "calendar"  # default
    user_id = None
    is_reconnect = False
    server_id = None

    if state:
        state_data = _decode_oauth_state(state)
        user_id = state_data.get("user_id")
        full_service = state_data.get("service", "microsoft-calendar")
        # Extract service name (e.g., "microsoft-calendar" -> "calendar")
        service = full_service.replace("microsoft-", "") if full_service.startswith("microsoft-") else full_service
        extra = state_data.get("extra")

        # Check if this is a reconnect flow
        if extra and extra.startswith("reconnect:"):
            is_reconnect = True
            server_id = extra.split(":", 1)[1] if ":" in extra else None

    callback_path = "/oauth/callback"

    # Handle OAuth errors - redirect to frontend with error
    if error:
        error_msg = error_description or error
        logger.warning("microsoft_oauth_error", error=error, description=error_description, service=service)
        params = urlencode({"error": error_msg, "service": service, "provider": "microsoft"})
        if is_reconnect and server_id:
            params = urlencode({
                "error": error_msg,
                "service": service,
                "server_id": server_id,
                "reconnect": "true",
                "provider": "microsoft",
            })
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    # Ensure we have required data
    if not code or not user_id:
        logger.warning("microsoft_oauth_callback_invalid", has_code=bool(code), has_user_id=bool(user_id))
        params = urlencode({
            "error": "OAuth session expired or invalid. Please try again.",
            "service": service,
            "provider": "microsoft",
        })
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    # Exchange authorization code for tokens
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                MICROSOFT_TOKEN_URL.format(tenant=MICROSOFT_TENANT_ID),
                data={
                    "client_id": MICROSOFT_CLIENT_ID,
                    "client_secret": MICROSOFT_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": MICROSOFT_OAUTH_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )

            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error_description", error_data.get("error", "Token exchange failed"))
                logger.error("microsoft_oauth_token_exchange_failed", error=error_msg, status=response.status_code)
                params = urlencode({"error": error_msg, "service": service, "provider": "microsoft"})
                return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

            tokens = response.json()
    except Exception as e:
        logger.error("microsoft_oauth_token_exchange_exception", error=str(e))
        params = urlencode({"error": f"Token exchange failed: {str(e)}", "service": service, "provider": "microsoft"})
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        logger.warning("microsoft_oauth_no_refresh_token", service=service)
        params = urlencode({
            "error": "No refresh token received. Try revoking app access at https://account.live.com/consent/manage and re-authorizing.",
            "service": service,
            "provider": "microsoft",
        })
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    # Store refresh token securely in vault under user-specific path
    secrets_manager = get_secrets_manager()
    token_ref = f"users/{user_id}/oauth/microsoft/{service}/{uuid.uuid4().hex}"

    try:
        await secrets_manager.store(
            key=token_ref,
            value={
                "refresh_token": refresh_token,
                "service": f"outlook-{service}",
                "provider": "microsoft",
                "user_id": user_id,
            }
        )
        logger.info(
            "microsoft_oauth_token_stored",
            service=service,
            token_ref=token_ref,
            user_id=user_id,
            is_reconnect=is_reconnect,
        )
    except Exception as e:
        logger.error("microsoft_oauth_token_storage_failed", error=str(e))
        params = urlencode({
            "error": "Failed to store OAuth credentials securely",
            "service": service,
            "provider": "microsoft",
        })
        return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

    # Redirect to frontend with token reference
    if is_reconnect and server_id:
        params = urlencode({
            "token_ref": token_ref,
            "service": service,
            "server_id": server_id,
            "reconnect": "true",
            "provider": "microsoft",
        })
    else:
        params = urlencode({
            "token_ref": token_ref,
            "service": service,
            "provider": "microsoft",
        })

    return RedirectResponse(url=f"{FRONTEND_URL}{callback_path}?{params}")

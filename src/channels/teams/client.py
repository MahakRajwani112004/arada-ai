"""Microsoft Teams Bot Framework client.

This module provides a client for sending messages to Microsoft Teams
using the Bot Framework REST API.
"""
import httpx
import structlog
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = structlog.get_logger(__name__)


class TeamsClient:
    """Client for Microsoft Teams Bot Framework API.

    Handles authentication and message sending to Teams conversations.
    """

    # Bot Framework OAuth endpoint templates
    OAUTH_URL_MULTI_TENANT = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"
    OAUTH_URL_SINGLE_TENANT = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    # Bot Connector API base URL (service URL from conversation reference)
    CONNECTOR_API_VERSION = "v3"

    def __init__(
        self,
        app_id: str,
        app_password: str,
        tenant_id: Optional[str] = None,
    ):
        """Initialize Teams client.

        Args:
            app_id: Microsoft App ID (Bot registration)
            app_password: Microsoft App Password/Secret
            tenant_id: Azure AD tenant ID (for single-tenant apps)
        """
        self.app_id = app_id
        self.app_password = app_password
        self.tenant_id = tenant_id

        # Token cache
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def _get_oauth_url(self) -> str:
        """Get the appropriate OAuth URL based on tenant configuration.

        For single-tenant bots, uses the specific tenant ID.
        For multi-tenant bots, uses the botframework.com tenant.
        """
        if self.tenant_id:
            return self.OAUTH_URL_SINGLE_TENANT.format(tenant_id=self.tenant_id)
        return self.OAUTH_URL_MULTI_TENANT

    async def _get_access_token(self) -> str:
        """Get or refresh access token for Bot Framework API.

        Returns:
            Access token string
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.now(timezone.utc) < self._token_expires_at:
                return self._access_token

        # Get the appropriate OAuth URL for this bot's configuration
        oauth_url = self._get_oauth_url()
        logger.debug("teams_oauth_request", oauth_url=oauth_url, tenant_id=self.tenant_id)

        # Request new token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                oauth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.app_id,
                    "client_secret": self.app_password,
                    "scope": "https://api.botframework.com/.default",
                },
            )
            response.raise_for_status()
            data = response.json()

        self._access_token = data["access_token"]
        # Expire 5 minutes early to be safe
        expires_in = data.get("expires_in", 3600) - 300
        self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        logger.info("teams_token_refreshed", expires_in=expires_in)
        return self._access_token

    async def send_message(
        self,
        service_url: str,
        conversation_id: str,
        message: str,
        reply_to_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a text message to a Teams conversation.

        Args:
            service_url: Bot Framework service URL from conversation reference
            conversation_id: Teams conversation ID
            message: Text message to send
            reply_to_id: Optional message ID to reply to

        Returns:
            Response from Bot Framework API
        """
        token = await self._get_access_token()

        # Build activity payload with required fields
        activity = {
            "type": "message",
            "text": message,
            "from": {
                "id": self.app_id,
                "name": "MagoneAI Bot",
            },
            "conversation": {
                "id": conversation_id,
            },
        }

        if reply_to_id:
            activity["replyToId"] = reply_to_id

        # Build URL
        url = f"{service_url.rstrip('/')}/{self.CONNECTOR_API_VERSION}/conversations/{conversation_id}/activities"

        logger.debug(
            "teams_send_message_request",
            url=url,
            activity=activity,
            service_url=service_url,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=activity,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            if response.status_code >= 400:
                error_body = response.text
                logger.error(
                    "teams_send_message_failed",
                    status_code=response.status_code,
                    error_body=error_body,
                    url=url,
                    activity=activity,
                )
            response.raise_for_status()

        result = response.json()
        logger.info(
            "teams_message_sent",
            conversation_id=conversation_id,
            message_id=result.get("id"),
        )
        return result

    async def send_activity(
        self,
        service_url: str,
        conversation_id: str,
        activity: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send a custom activity to a Teams conversation.

        Args:
            service_url: Bot Framework service URL
            conversation_id: Teams conversation ID
            activity: Full activity payload

        Returns:
            Response from Bot Framework API
        """
        token = await self._get_access_token()

        # Ensure required fields are present
        if "from" not in activity:
            activity["from"] = {
                "id": self.app_id,
                "name": "MagoneAI Bot",
            }
        if "conversation" not in activity:
            activity["conversation"] = {
                "id": conversation_id,
            }

        url = f"{service_url.rstrip('/')}/{self.CONNECTOR_API_VERSION}/conversations/{conversation_id}/activities"

        logger.debug(
            "teams_send_activity_request",
            url=url,
            activity_type=activity.get("type"),
            service_url=service_url,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=activity,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            if response.status_code >= 400:
                error_body = response.text
                logger.error(
                    "teams_send_activity_failed",
                    status_code=response.status_code,
                    error_body=error_body,
                    url=url,
                    activity_type=activity.get("type"),
                )
            response.raise_for_status()

        # Handle empty responses (typing indicators return 201/202 with no body)
        if response.status_code in (201, 202) or not response.content:
            return {"status": response.status_code}
        return response.json()

    async def send_typing_indicator(
        self,
        service_url: str,
        conversation_id: str,
    ) -> None:
        """Send a typing indicator to a Teams conversation.

        Args:
            service_url: Bot Framework service URL
            conversation_id: Teams conversation ID
        """
        await self.send_activity(
            service_url=service_url,
            conversation_id=conversation_id,
            activity={
                "type": "typing",
                "from": {
                    "id": self.app_id,
                    "name": "MagoneAI Bot",
                },
                "conversation": {
                    "id": conversation_id,
                },
            },
        )

    async def reply_to_activity(
        self,
        service_url: str,
        conversation_id: str,
        activity_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """Reply to a specific activity in a Teams conversation.

        Args:
            service_url: Bot Framework service URL
            conversation_id: Teams conversation ID
            activity_id: Activity ID to reply to
            message: Reply message

        Returns:
            Response from Bot Framework API
        """
        token = await self._get_access_token()

        activity = {
            "type": "message",
            "text": message,
            "from": {
                "id": self.app_id,
                "name": "MagoneAI Bot",
            },
            "conversation": {
                "id": conversation_id,
            },
        }

        url = (
            f"{service_url.rstrip('/')}/{self.CONNECTOR_API_VERSION}"
            f"/conversations/{conversation_id}/activities/{activity_id}"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=activity,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()

        return response.json()

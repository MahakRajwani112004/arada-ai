"""Outlook Email MCP Server.

Provides MCP tools for Outlook Email via Microsoft Graph API:
- list_emails: List recent emails
- get_email: Get full email content
- send_email: Send an email
- search_emails: Search emails

Credentials passed via HTTP header:
- X-Microsoft-Refresh-Token: OAuth refresh token
"""
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseMCPServer, tool

# Microsoft OAuth Configuration
DEFAULT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
DEFAULT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
DEFAULT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")
TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"


class OutlookEmailServer(BaseMCPServer):
    """MCP Server for Outlook Email via Microsoft Graph API."""

    def __init__(self):
        super().__init__(
            name="outlook-email",
            version="1.0.0",
            description="Outlook Email MCP Server",
        )

    async def _get_access_token(self, credentials: Dict[str, str]) -> str:
        """Exchange refresh token for access token."""
        refresh_token = credentials.get("microsoft_refresh_token")
        if not refresh_token:
            raise ValueError("Missing X-Microsoft-Refresh-Token header")

        client_id = credentials.get("microsoft_client_id") or DEFAULT_CLIENT_ID
        client_secret = credentials.get("microsoft_client_secret") or DEFAULT_CLIENT_SECRET
        tenant_id = credentials.get("microsoft_tenant_id") or DEFAULT_TENANT_ID

        if not client_id or not client_secret:
            raise ValueError(
                "Missing OAuth client credentials. Set MICROSOFT_CLIENT_ID and "
                "MICROSOFT_CLIENT_SECRET environment variables or pass via headers."
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TOKEN_URL.format(tenant=tenant_id),
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": "https://graph.microsoft.com/.default offline_access",
                },
            )

            if response.status_code == 400:
                error_data = response.json()
                error_desc = error_data.get("error_description", "Token refresh failed")
                raise ValueError(f"Token refresh failed: {error_desc}")

            response.raise_for_status()
            return response.json()["access_token"]

    async def _graph_request(
        self,
        credentials: Dict[str, str],
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated request to Microsoft Graph API."""
        access_token = await self._get_access_token(credentials)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=f"{GRAPH_API_URL}{endpoint}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=json_data,
                params=params,
            )

            if response.status_code == 401:
                raise ValueError("Authentication failed. Please re-authenticate with Microsoft.")
            elif response.status_code == 403:
                raise ValueError("Access denied. Check email permissions.")
            elif response.status_code == 404:
                raise ValueError("Resource not found.")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded. Please try again later.")
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get("message", response.text)
                raise ValueError(f"Graph API error: {error_msg}")

            if response.status_code == 204 or response.status_code == 202:
                return {}
            return response.json()

    @tool(
        name="list_emails",
        description="List recent emails from inbox or specified folder",
        input_schema={
            "type": "object",
            "properties": {
                "folder": {
                    "type": "string",
                    "description": "Folder name: inbox, drafts, sentitems, deleteditems, junkemail (default: inbox)",
                    "default": "inbox",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of emails (default 20)",
                    "default": 20,
                },
                "unread_only": {
                    "type": "boolean",
                    "description": "Only return unread emails",
                    "default": False,
                },
            },
        },
        credential_headers=[
            "X-Microsoft-Refresh-Token",
            "X-Microsoft-Client-Id",
            "X-Microsoft-Client-Secret",
            "X-Microsoft-Tenant-Id",
        ],
    )
    async def list_emails(
        self,
        credentials: Dict[str, str],
        folder: str = "inbox",
        max_results: int = 20,
        unread_only: bool = False,
    ) -> Dict[str, Any]:
        """List emails from specified folder."""
        params: Dict[str, Any] = {
            "$top": max_results,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,isRead,bodyPreview,hasAttachments,importance",
        }

        if unread_only:
            params["$filter"] = "isRead eq false"

        result = await self._graph_request(
            credentials,
            "GET",
            f"/me/mailFolders/{folder}/messages",
            params=params,
        )

        messages = result.get("value", [])

        return {
            "count": len(messages),
            "folder": folder,
            "emails": [
                {
                    "id": m.get("id"),
                    "subject": m.get("subject", "(No subject)"),
                    "from": m.get("from", {}).get("emailAddress", {}).get("address"),
                    "from_name": m.get("from", {}).get("emailAddress", {}).get("name"),
                    "to": [
                        r.get("emailAddress", {}).get("address")
                        for r in m.get("toRecipients", [])
                    ],
                    "cc": [
                        r.get("emailAddress", {}).get("address")
                        for r in m.get("ccRecipients", [])
                    ],
                    "date": m.get("receivedDateTime"),
                    "is_read": m.get("isRead"),
                    "snippet": (m.get("bodyPreview") or "")[:150],
                    "has_attachments": m.get("hasAttachments"),
                    "importance": m.get("importance"),
                }
                for m in messages
            ],
        }

    @tool(
        name="get_email",
        description="Get full email content by ID",
        input_schema={
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "Email message ID"},
                "mark_as_read": {
                    "type": "boolean",
                    "description": "Mark the email as read after fetching",
                    "default": False,
                },
            },
            "required": ["email_id"],
        },
        credential_headers=[
            "X-Microsoft-Refresh-Token",
            "X-Microsoft-Client-Id",
            "X-Microsoft-Client-Secret",
            "X-Microsoft-Tenant-Id",
        ],
    )
    async def get_email(
        self,
        credentials: Dict[str, str],
        email_id: str,
        mark_as_read: bool = False,
    ) -> Dict[str, Any]:
        """Get full email content."""
        params = {
            "$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,isRead,body,hasAttachments,importance,webLink,attachments",
            "$expand": "attachments($select=id,name,contentType,size)",
        }

        result = await self._graph_request(
            credentials,
            "GET",
            f"/me/messages/{email_id}",
            params=params,
        )

        # Optionally mark as read
        if mark_as_read and not result.get("isRead"):
            await self._graph_request(
                credentials,
                "PATCH",
                f"/me/messages/{email_id}",
                json_data={"isRead": True},
            )

        body = result.get("body", {})
        body_content = body.get("content", "")
        # Truncate very long emails
        if len(body_content) > 10000:
            body_content = body_content[:10000] + "\n\n... (truncated)"

        return {
            "id": result.get("id"),
            "subject": result.get("subject", "(No subject)"),
            "from": result.get("from", {}).get("emailAddress", {}).get("address"),
            "from_name": result.get("from", {}).get("emailAddress", {}).get("name"),
            "to": [
                r.get("emailAddress", {}).get("address")
                for r in result.get("toRecipients", [])
            ],
            "cc": [
                r.get("emailAddress", {}).get("address")
                for r in result.get("ccRecipients", [])
            ],
            "date": result.get("receivedDateTime"),
            "is_read": result.get("isRead"),
            "body_type": body.get("contentType"),
            "body": body_content,
            "has_attachments": result.get("hasAttachments"),
            "attachments": [
                {
                    "id": a.get("id"),
                    "name": a.get("name"),
                    "content_type": a.get("contentType"),
                    "size": a.get("size"),
                }
                for a in result.get("attachments", [])
            ],
            "importance": result.get("importance"),
            "web_link": result.get("webLink"),
        }

    @tool(
        name="send_email",
        description="Send an email",
        input_schema={
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address (comma-separated for multiple)",
                },
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body (HTML supported)"},
                "cc": {
                    "type": "string",
                    "description": "CC recipients (comma-separated)",
                },
                "bcc": {
                    "type": "string",
                    "description": "BCC recipients (comma-separated)",
                },
                "is_html": {
                    "type": "boolean",
                    "description": "Whether body is HTML",
                    "default": False,
                },
                "importance": {
                    "type": "string",
                    "description": "Email importance: low, normal, high",
                    "default": "normal",
                },
                "save_to_sent": {
                    "type": "boolean",
                    "description": "Save a copy to Sent Items",
                    "default": True,
                },
            },
            "required": ["to", "subject", "body"],
        },
        credential_headers=[
            "X-Microsoft-Refresh-Token",
            "X-Microsoft-Client-Id",
            "X-Microsoft-Client-Secret",
            "X-Microsoft-Tenant-Id",
        ],
    )
    async def send_email(
        self,
        credentials: Dict[str, str],
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        is_html: bool = False,
        importance: str = "normal",
        save_to_sent: bool = True,
    ) -> Dict[str, Any]:
        """Send an email."""
        # Parse recipients
        to_recipients = [
            {"emailAddress": {"address": email.strip()}}
            for email in to.split(",")
            if email.strip()
        ]

        cc_recipients = [
            {"emailAddress": {"address": email.strip()}}
            for email in cc.split(",")
            if email.strip()
        ] if cc else []

        bcc_recipients = [
            {"emailAddress": {"address": email.strip()}}
            for email in bcc.split(",")
            if email.strip()
        ] if bcc else []

        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if is_html else "Text",
                    "content": body,
                },
                "toRecipients": to_recipients,
                "importance": importance,
            },
            "saveToSentItems": save_to_sent,
        }

        if cc_recipients:
            message["message"]["ccRecipients"] = cc_recipients

        if bcc_recipients:
            message["message"]["bccRecipients"] = bcc_recipients

        await self._graph_request(
            credentials,
            "POST",
            "/me/sendMail",
            json_data=message,
        )

        return {
            "success": True,
            "to": to,
            "subject": subject,
            "message": "Email sent successfully",
        }

    @tool(
        name="search_emails",
        description="Search emails by query",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (searches subject, body, sender)",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default 20)",
                    "default": 20,
                },
                "folder": {
                    "type": "string",
                    "description": "Folder to search in (default: all folders)",
                },
            },
            "required": ["query"],
        },
        credential_headers=[
            "X-Microsoft-Refresh-Token",
            "X-Microsoft-Client-Id",
            "X-Microsoft-Client-Secret",
            "X-Microsoft-Tenant-Id",
        ],
    )
    async def search_emails(
        self,
        credentials: Dict[str, str],
        query: str,
        max_results: int = 20,
        folder: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search emails by query."""
        params: Dict[str, Any] = {
            "$search": f'"{query}"',
            "$top": max_results,
            "$select": "id,subject,from,toRecipients,receivedDateTime,isRead,bodyPreview,hasAttachments",
        }

        endpoint = f"/me/mailFolders/{folder}/messages" if folder else "/me/messages"

        result = await self._graph_request(
            credentials,
            "GET",
            endpoint,
            params=params,
        )

        messages = result.get("value", [])

        return {
            "count": len(messages),
            "query": query,
            "folder": folder or "all",
            "emails": [
                {
                    "id": m.get("id"),
                    "subject": m.get("subject", "(No subject)"),
                    "from": m.get("from", {}).get("emailAddress", {}).get("address"),
                    "from_name": m.get("from", {}).get("emailAddress", {}).get("name"),
                    "to": [
                        r.get("emailAddress", {}).get("address")
                        for r in m.get("toRecipients", [])
                    ],
                    "date": m.get("receivedDateTime"),
                    "is_read": m.get("isRead"),
                    "snippet": (m.get("bodyPreview") or "")[:150],
                    "has_attachments": m.get("hasAttachments"),
                }
                for m in messages
            ],
        }


# Create server instance
server = OutlookEmailServer()
app = server.app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server.run(host="0.0.0.0", port=port)

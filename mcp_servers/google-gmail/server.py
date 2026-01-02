"""Google Gmail MCP Server.

Provides MCP tools for Gmail:
- list_emails: List recent emails
- get_email: Get full email content
- send_email: Send an email

Credentials passed via HTTP header:
- X-Google-Refresh-Token: OAuth refresh token
"""
import base64
import os
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from dotenv import load_dotenv
load_dotenv()  # Load from .env file

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseMCPServer, tool


# Default OAuth client (users can override)
DEFAULT_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
DEFAULT_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
TOKEN_URI = "https://oauth2.googleapis.com/token"


class GoogleGmailServer(BaseMCPServer):
    """MCP Server for Gmail."""

    def __init__(self):
        super().__init__(
            name="google-gmail",
            version="1.0.0",
            description="Google Gmail MCP Server",
        )

    def _get_credentials(self, credentials: Dict[str, str]) -> Credentials:
        """Build Google credentials from refresh token."""
        refresh_token = credentials.get("google_refresh_token")
        if not refresh_token:
            raise ValueError("Missing X-Google-Refresh-Token header")

        client_id = credentials.get("google_client_id") or DEFAULT_CLIENT_ID
        client_secret = credentials.get("google_client_secret") or DEFAULT_CLIENT_SECRET

        if not client_id or not client_secret:
            raise ValueError(
                "Missing OAuth client credentials. Set GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET environment variables or pass via headers."
            )

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=TOKEN_URI,
            client_id=client_id,
            client_secret=client_secret,
            scopes=[
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.modify",
            ],
        )
        creds.refresh(GoogleRequest())
        return creds

    def _get_service(self, credentials: Dict[str, str]):
        """Get Gmail API service."""
        creds = self._get_credentials(credentials)
        return build("gmail", "v1", credentials=creds)

    @tool(
        name="list_emails",
        description="List recent emails from inbox",
        input_schema={
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of emails (default 20)",
                    "default": 20,
                },
                "query": {
                    "type": "string",
                    "description": "Gmail search query (e.g., 'is:unread', 'from:someone@example.com')",
                },
            },
        },
        credential_headers=["X-Google-Refresh-Token", "X-Google-Client-Id", "X-Google-Client-Secret"],
    )
    async def list_emails(
        self,
        credentials: Dict[str, str],
        max_results: int = 20,
        query: str = "",
    ) -> Dict[str, Any]:
        """List emails from inbox."""
        service = self._get_service(credentials)

        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_results, q=query)
            .execute()
        )

        messages = results.get("messages", [])

        emails = []
        for msg in messages[:max_results]:
            msg_data = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="metadata")
                .execute()
            )

            headers = {
                h["name"]: h["value"]
                for h in msg_data.get("payload", {}).get("headers", [])
            }

            emails.append({
                "id": msg["id"],
                "thread_id": msg["threadId"],
                "subject": headers.get("Subject", "(No subject)"),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "snippet": msg_data.get("snippet", "")[:100],
            })

        return {"count": len(emails), "emails": emails}

    @tool(
        name="get_email",
        description="Get full email content by ID",
        input_schema={
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "Email ID"},
            },
            "required": ["email_id"],
        },
        credential_headers=["X-Google-Refresh-Token", "X-Google-Client-Id", "X-Google-Client-Secret"],
    )
    async def get_email(
        self,
        credentials: Dict[str, str],
        email_id: str,
    ) -> Dict[str, Any]:
        """Get full email content."""
        service = self._get_service(credentials)

        msg = (
            service.users()
            .messages()
            .get(userId="me", id=email_id, format="full")
            .execute()
        )

        headers = {
            h["name"]: h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }

        # Extract body
        body = ""
        payload = msg.get("payload", {})
        if "body" in payload and payload["body"].get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        elif "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break

        return {
            "id": msg["id"],
            "thread_id": msg["threadId"],
            "subject": headers.get("Subject", "(No subject)"),
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "date": headers.get("Date", ""),
            "body": body[:5000],
            "labels": msg.get("labelIds", []),
        }

    @tool(
        name="send_email",
        description="Send an email",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body (plain text)"},
                "cc": {"type": "string", "description": "CC recipients (comma-separated)"},
            },
            "required": ["to", "subject", "body"],
        },
        credential_headers=["X-Google-Refresh-Token", "X-Google-Client-Id", "X-Google-Client-Secret"],
    )
    async def send_email(
        self,
        credentials: Dict[str, str],
        to: str,
        subject: str,
        body: str,
        cc: str = "",
    ) -> Dict[str, Any]:
        """Send an email."""
        service = self._get_service(credentials)

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if cc:
            message["cc"] = cc

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        sent = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )

        return {
            "success": True,
            "message_id": sent.get("id"),
            "thread_id": sent.get("threadId"),
            "to": to,
            "subject": subject,
        }


# Create server instance
server = GoogleGmailServer()
app = server.app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server.run(host="0.0.0.0", port=port)

"""Google Calendar MCP Server.

Provides MCP tools for Google Calendar:
- list_events: List calendar events
- create_event: Create new event
- delete_event: Delete event

Credentials passed via HTTP header:
- X-Google-Refresh-Token: OAuth refresh token
"""
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

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


class GoogleCalendarServer(BaseMCPServer):
    """MCP Server for Google Calendar."""

    def __init__(self):
        super().__init__(
            name="google-calendar",
            version="1.0.0",
            description="Google Calendar MCP Server",
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
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        creds.refresh(GoogleRequest())
        return creds

    def _get_service(self, credentials: Dict[str, str]):
        """Get Google Calendar API service."""
        creds = self._get_credentials(credentials)
        return build("calendar", "v3", credentials=creds)

    @tool(
        name="list_events",
        description="List calendar events for a given date range",
        input_schema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (defaults to today)",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to fetch (default 1)",
                    "default": 1,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of events (default 50)",
                    "default": 50,
                },
            },
        },
        credential_headers=[
            "X-Google-Refresh-Token",
            "X-Google-Client-Id",
            "X-Google-Client-Secret",
        ],
    )
    async def list_events(
        self,
        credentials: Dict[str, str],
        date: Optional[str] = None,
        days: int = 1,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """List calendar events."""
        service = self._get_service(credentials)

        if date:
            start_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        end_date = start_date + timedelta(days=days)

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_date.isoformat() + "Z",
                timeMax=end_date.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        return {
            "count": len(events),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "events": [
                {
                    "id": e.get("id"),
                    "title": e.get("summary", "(No title)"),
                    "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date")),
                    "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date")),
                    "location": e.get("location"),
                    "attendees": [a.get("email") for a in e.get("attendees", [])],
                    "description": e.get("description", "")[:200],
                    "hangout_link": e.get("hangoutLink"),
                }
                for e in events
            ],
        }

    @tool(
        name="create_event",
        description="Create a new calendar event",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start_time": {"type": "string", "description": "Start time (ISO format)"},
                "end_time": {"type": "string", "description": "End time (ISO format)"},
                "description": {"type": "string", "description": "Event description"},
                "location": {"type": "string", "description": "Event location"},
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Attendee emails",
                },
            },
            "required": ["title", "start_time", "end_time"],
        },
        credential_headers=["X-Google-Refresh-Token", "X-Google-Client-Id", "X-Google-Client-Secret"],
    )
    async def create_event(
        self,
        credentials: Dict[str, str],
        title: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a calendar event."""
        service = self._get_service(credentials)

        event = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {"dateTime": start_time, "timeZone": "UTC"},
            "end": {"dateTime": end_time, "timeZone": "UTC"},
        }

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        created = service.events().insert(calendarId="primary", body=event).execute()

        return {
            "success": True,
            "event_id": created.get("id"),
            "html_link": created.get("htmlLink"),
            "title": created.get("summary"),
        }

    @tool(
        name="delete_event",
        description="Delete a calendar event by ID",
        input_schema={
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Event ID to delete"},
            },
            "required": ["event_id"],
        },
        credential_headers=["X-Google-Refresh-Token", "X-Google-Client-Id", "X-Google-Client-Secret"],
    )
    async def delete_event(
        self,
        credentials: Dict[str, str],
        event_id: str,
    ) -> Dict[str, Any]:
        """Delete a calendar event."""
        service = self._get_service(credentials)
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return {"success": True, "deleted_event_id": event_id}


# Create server instance
server = GoogleCalendarServer()
app = server.app

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8001)

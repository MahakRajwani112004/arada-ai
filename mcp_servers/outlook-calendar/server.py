"""Outlook Calendar MCP Server.

Provides MCP tools for Outlook Calendar via Microsoft Graph API:
- list_events: List calendar events
- create_event: Create new event
- update_event: Update existing event
- delete_event: Delete event

Credentials passed via HTTP header:
- X-Microsoft-Refresh-Token: OAuth refresh token
"""
import os
from datetime import datetime, timedelta, timezone
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


class OutlookCalendarServer(BaseMCPServer):
    """MCP Server for Outlook Calendar via Microsoft Graph API."""

    def __init__(self):
        super().__init__(
            name="outlook-calendar",
            version="1.0.0",
            description="Outlook Calendar MCP Server",
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
                raise ValueError("Access denied. Check calendar permissions.")
            elif response.status_code == 404:
                raise ValueError("Resource not found.")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded. Please try again later.")
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get("message", response.text)
                raise ValueError(f"Graph API error: {error_msg}")

            if response.status_code == 204:
                return {}
            return response.json()

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
            "X-Microsoft-Refresh-Token",
            "X-Microsoft-Client-Id",
            "X-Microsoft-Client-Secret",
            "X-Microsoft-Tenant-Id",
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
        if date:
            try:
                start_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                raise ValueError(f"Invalid date format: '{date}'. Expected YYYY-MM-DD.")
        else:
            start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        end_date = start_date + timedelta(days=days)

        # Format dates for Graph API (ISO 8601)
        start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Use calendarView for expanded recurring events
        params = {
            "startDateTime": start_iso,
            "endDateTime": end_iso,
            "$top": max_results,
            "$orderby": "start/dateTime",
            "$select": "id,subject,start,end,location,attendees,bodyPreview,webLink,isOnlineMeeting,onlineMeetingUrl",
        }

        result = await self._graph_request(
            credentials,
            "GET",
            "/me/calendar/calendarView",
            params=params,
        )

        events = result.get("value", [])

        return {
            "count": len(events),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "events": [
                {
                    "id": e.get("id"),
                    "title": e.get("subject", "(No title)"),
                    "start": e.get("start", {}).get("dateTime"),
                    "end": e.get("end", {}).get("dateTime"),
                    "timezone": e.get("start", {}).get("timeZone"),
                    "location": e.get("location", {}).get("displayName"),
                    "attendees": [
                        a.get("emailAddress", {}).get("address")
                        for a in e.get("attendees", [])
                    ],
                    "description": (e.get("bodyPreview") or "")[:200],
                    "web_link": e.get("webLink"),
                    "is_online_meeting": e.get("isOnlineMeeting"),
                    "online_meeting_url": e.get("onlineMeetingUrl"),
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
                "start_time": {"type": "string", "description": "Start time (ISO format, e.g., 2024-01-15T10:00:00)"},
                "end_time": {"type": "string", "description": "End time (ISO format, e.g., 2024-01-15T11:00:00)"},
                "description": {"type": "string", "description": "Event description (HTML supported)"},
                "location": {"type": "string", "description": "Event location"},
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Attendee email addresses",
                },
                "is_online_meeting": {
                    "type": "boolean",
                    "description": "Create as Teams meeting",
                    "default": False,
                },
                "timezone": {
                    "type": "string",
                    "description": "Timezone (default: UTC)",
                    "default": "UTC",
                },
            },
            "required": ["title", "start_time", "end_time"],
        },
        credential_headers=[
            "X-Microsoft-Refresh-Token",
            "X-Microsoft-Client-Id",
            "X-Microsoft-Client-Secret",
            "X-Microsoft-Tenant-Id",
        ],
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
        is_online_meeting: bool = False,
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        """Create a calendar event."""
        event = {
            "subject": title,
            "body": {
                "contentType": "HTML" if "<" in description else "Text",
                "content": description,
            },
            "start": {
                "dateTime": start_time,
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_time,
                "timeZone": timezone,
            },
            "isOnlineMeeting": is_online_meeting,
        }

        if location:
            event["location"] = {"displayName": location}

        if attendees:
            event["attendees"] = [
                {
                    "emailAddress": {"address": email},
                    "type": "required",
                }
                for email in attendees
            ]

        if is_online_meeting:
            event["onlineMeetingProvider"] = "teamsForBusiness"

        created = await self._graph_request(
            credentials,
            "POST",
            "/me/calendar/events",
            json_data=event,
        )

        return {
            "success": True,
            "event_id": created.get("id"),
            "web_link": created.get("webLink"),
            "title": created.get("subject"),
            "online_meeting_url": created.get("onlineMeeting", {}).get("joinUrl") if is_online_meeting else None,
        }

    @tool(
        name="update_event",
        description="Update an existing calendar event",
        input_schema={
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Event ID to update"},
                "title": {"type": "string", "description": "New event title"},
                "start_time": {"type": "string", "description": "New start time (ISO format)"},
                "end_time": {"type": "string", "description": "New end time (ISO format)"},
                "description": {"type": "string", "description": "New event description"},
                "location": {"type": "string", "description": "New event location"},
                "timezone": {"type": "string", "description": "Timezone for times"},
            },
            "required": ["event_id"],
        },
        credential_headers=[
            "X-Microsoft-Refresh-Token",
            "X-Microsoft-Client-Id",
            "X-Microsoft-Client-Secret",
            "X-Microsoft-Tenant-Id",
        ],
    )
    async def update_event(
        self,
        credentials: Dict[str, str],
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        """Update a calendar event."""
        event: Dict[str, Any] = {}

        if title is not None:
            event["subject"] = title

        if description is not None:
            event["body"] = {
                "contentType": "HTML" if "<" in description else "Text",
                "content": description,
            }

        if start_time is not None:
            event["start"] = {"dateTime": start_time, "timeZone": timezone}

        if end_time is not None:
            event["end"] = {"dateTime": end_time, "timeZone": timezone}

        if location is not None:
            event["location"] = {"displayName": location}

        if not event:
            raise ValueError("No fields provided to update")

        updated = await self._graph_request(
            credentials,
            "PATCH",
            f"/me/calendar/events/{event_id}",
            json_data=event,
        )

        return {
            "success": True,
            "event_id": updated.get("id"),
            "title": updated.get("subject"),
            "web_link": updated.get("webLink"),
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
        credential_headers=[
            "X-Microsoft-Refresh-Token",
            "X-Microsoft-Client-Id",
            "X-Microsoft-Client-Secret",
            "X-Microsoft-Tenant-Id",
        ],
    )
    async def delete_event(
        self,
        credentials: Dict[str, str],
        event_id: str,
    ) -> Dict[str, Any]:
        """Delete a calendar event."""
        await self._graph_request(
            credentials,
            "DELETE",
            f"/me/calendar/events/{event_id}",
        )

        return {"success": True, "deleted_event_id": event_id}


# Create server instance
server = OutlookCalendarServer()
app = server.app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server.run(host="0.0.0.0", port=port)

"""MCP Server Catalog - built-in server templates."""
import os
from typing import Dict, List, Optional

from .models import CredentialSpec, MCPServerTemplate

# MCP Server URLs - configurable via environment variables
# For local dev: http://localhost:800X/mcp
# For Docker: http://mcp-{service}:8000/mcp
MCP_GOOGLE_CALENDAR_URL = os.getenv("MCP_GOOGLE_CALENDAR_URL", "http://localhost:8001/mcp")
MCP_GOOGLE_GMAIL_URL = os.getenv("MCP_GOOGLE_GMAIL_URL", "http://localhost:8002/mcp")
MCP_GOOGLE_DRIVE_URL = os.getenv("MCP_GOOGLE_DRIVE_URL", "http://localhost:8003/mcp")
MCP_OUTLOOK_CALENDAR_URL = os.getenv("MCP_OUTLOOK_CALENDAR_URL", "http://localhost:8004/mcp")
MCP_OUTLOOK_EMAIL_URL = os.getenv("MCP_OUTLOOK_EMAIL_URL", "http://localhost:8005/mcp")
MCP_SHAREPOINT_URL = os.getenv("MCP_SHAREPOINT_URL", "http://localhost:8006/mcp")
MCP_ONEDRIVE_URL = os.getenv("MCP_ONEDRIVE_URL", "http://localhost:8007/mcp")
MCP_SLACK_URL = os.getenv("MCP_SLACK_URL", "http://localhost:8008/mcp")
MCP_FILESYSTEM_URL = os.getenv("MCP_FILESYSTEM_URL", "http://localhost:8007/mcp")

# Arada Real Estate Analytics
MCP_ARADA_SQL_URL = os.getenv("MCP_ARADA_SQL_URL", "http://localhost:8002/mcp")


def _google_refresh_token_spec() -> CredentialSpec:
    """Google refresh token credential spec."""
    return CredentialSpec(
        name="GOOGLE_REFRESH_TOKEN",
        description="OAuth refresh token from OAuth Playground",
        sensitive=True,
        header_name="X-Google-Refresh-Token",
    )


def _microsoft_refresh_token_spec() -> CredentialSpec:
    """Microsoft refresh token credential spec."""
    return CredentialSpec(
        name="MICROSOFT_REFRESH_TOKEN",
        description="OAuth refresh token from Graph Explorer or Azure AD",
        sensitive=True,
        header_name="X-Microsoft-Refresh-Token",
    )


# Server templates catalog
MCP_SERVER_CATALOG: Dict[str, MCPServerTemplate] = {
    # ========== GOOGLE SERVICES ==========
    "google-calendar": MCPServerTemplate(
        id="google-calendar",
        name="Google Calendar",
        url_template=MCP_GOOGLE_CALENDAR_URL,
        auth_type="oauth_token",
        token_guide_url="https://developers.google.com/oauthplayground/",
        scopes=["https://www.googleapis.com/auth/calendar"],
        credentials_required=[_google_refresh_token_spec()],
        credentials_optional=[
            CredentialSpec(
                name="GOOGLE_CLIENT_ID",
                description="Custom OAuth app client ID",
                sensitive=False,
                header_name="X-Google-Client-Id",
            ),
            CredentialSpec(
                name="GOOGLE_CLIENT_SECRET",
                description="Custom OAuth app client secret",
                sensitive=True,
                header_name="X-Google-Client-Secret",
            ),
        ],
        tools=["list_events", "create_event", "update_event", "delete_event"],
    ),
    "gmail": MCPServerTemplate(
        id="gmail",
        name="Gmail",
        url_template=MCP_GOOGLE_GMAIL_URL,
        auth_type="oauth_token",
        token_guide_url="https://developers.google.com/oauthplayground/",
        scopes=[
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.send",
        ],
        credentials_required=[_google_refresh_token_spec()],
        tools=["list_emails", "send_email", "search_emails", "get_email"],
    ),
    "google-drive": MCPServerTemplate(
        id="google-drive",
        name="Google Drive",
        url_template=MCP_GOOGLE_DRIVE_URL,
        auth_type="oauth_token",
        token_guide_url="https://developers.google.com/oauthplayground/",
        scopes=["https://www.googleapis.com/auth/drive"],
        credentials_required=[_google_refresh_token_spec()],
        tools=["list_files", "upload_file", "download_file", "search_files"],
    ),
    # ========== MICROSOFT SERVICES ==========
    "outlook-calendar": MCPServerTemplate(
        id="outlook-calendar",
        name="Outlook Calendar",
        url_template=MCP_OUTLOOK_CALENDAR_URL,
        auth_type="oauth_token",
        token_guide_url="https://developer.microsoft.com/en-us/graph/graph-explorer",
        scopes=["Calendars.ReadWrite", "offline_access"],
        credentials_required=[_microsoft_refresh_token_spec()],
        credentials_optional=[
            CredentialSpec(
                name="MICROSOFT_CLIENT_ID",
                description="Azure AD app client ID",
                sensitive=False,
                header_name="X-Microsoft-Client-Id",
            ),
            CredentialSpec(
                name="MICROSOFT_CLIENT_SECRET",
                description="Azure AD app client secret",
                sensitive=True,
                header_name="X-Microsoft-Client-Secret",
            ),
            CredentialSpec(
                name="MICROSOFT_TENANT_ID",
                description="Azure AD tenant ID",
                sensitive=False,
                header_name="X-Microsoft-Tenant-Id",
            ),
        ],
        tools=["list_events", "create_event", "update_event", "delete_event"],
    ),
    "outlook-email": MCPServerTemplate(
        id="outlook-email",
        name="Outlook Email",
        url_template=MCP_OUTLOOK_EMAIL_URL,
        auth_type="oauth_token",
        token_guide_url="https://developer.microsoft.com/en-us/graph/graph-explorer",
        scopes=["Mail.ReadWrite", "Mail.Send", "offline_access"],
        credentials_required=[_microsoft_refresh_token_spec()],
        credentials_optional=[
            CredentialSpec(
                name="MICROSOFT_CLIENT_ID",
                description="Azure AD app client ID",
                sensitive=False,
                header_name="X-Microsoft-Client-Id",
            ),
            CredentialSpec(
                name="MICROSOFT_CLIENT_SECRET",
                description="Azure AD app client secret",
                sensitive=True,
                header_name="X-Microsoft-Client-Secret",
            ),
            CredentialSpec(
                name="MICROSOFT_TENANT_ID",
                description="Azure AD tenant ID",
                sensitive=False,
                header_name="X-Microsoft-Tenant-Id",
            ),
        ],
        tools=["list_emails", "get_email", "send_email", "search_emails"],
    ),
    "sharepoint": MCPServerTemplate(
        id="sharepoint",
        name="SharePoint",
        url_template=MCP_SHAREPOINT_URL,
        auth_type="oauth_token",
        token_guide_url="https://developer.microsoft.com/en-us/graph/graph-explorer",
        scopes=["Sites.ReadWrite.All", "Files.ReadWrite.All", "offline_access"],
        credentials_required=[
            _microsoft_refresh_token_spec(),
            CredentialSpec(
                name="SHAREPOINT_SITE_URL",
                description="SharePoint site URL (e.g., contoso.sharepoint.com)",
                sensitive=False,
                header_name="X-SharePoint-Site-Url",
            ),
        ],
        tools=["list_sites", "list_files", "upload_file", "download_file"],
    ),
    "onedrive": MCPServerTemplate(
        id="onedrive",
        name="OneDrive",
        url_template=MCP_ONEDRIVE_URL,
        auth_type="oauth_token",
        token_guide_url="https://developer.microsoft.com/en-us/graph/graph-explorer",
        scopes=["Files.ReadWrite.All", "offline_access"],
        credentials_required=[_microsoft_refresh_token_spec()],
        tools=["list_files", "upload_file", "download_file", "search_files"],
    ),
    # ========== OTHER SERVICES ==========
    "slack": MCPServerTemplate(
        id="slack",
        name="Slack",
        url_template=MCP_SLACK_URL,
        auth_type="api_token",
        token_guide_url="https://api.slack.com/apps",
        scopes=[],
        credentials_required=[
            CredentialSpec(
                name="SLACK_BOT_TOKEN",
                description="Bot User OAuth Token (xoxb-...)",
                sensitive=True,
                header_name="X-Slack-Bot-Token",
            ),
        ],
        credentials_optional=[
            CredentialSpec(
                name="SLACK_TEAM_ID",
                description="Workspace team ID",
                sensitive=False,
                header_name="X-Slack-Team-Id",
            ),
        ],
        tools=["send_message", "list_channels", "search_messages"],
    ),
    # ========== ARADA REAL ESTATE ==========
    "arada-sql": MCPServerTemplate(
        id="arada-sql",
        name="Arada Real Estate Analytics",
        url_template=MCP_ARADA_SQL_URL,
        auth_type="none",
        scopes=[],
        credentials_required=[],  # No credentials needed - local database
        tools=["get_schema", "execute_sql", "get_portfolio_summary"],
    ),
    # ========== UTILITY SERVICES ==========
    "filesystem": MCPServerTemplate(
        id="filesystem",
        name="Filesystem",
        url_template=MCP_FILESYSTEM_URL,
        auth_type="none",
        scopes=[],
        credentials_required=[
            CredentialSpec(
                name="ALLOWED_PATHS",
                description="Comma-separated list of allowed directories",
                sensitive=False,
                header_name="X-Allowed-Paths",
            ),
        ],
        tools=["read_file", "write_file", "list_directory"],
    ),
}


def get_catalog() -> Dict[str, MCPServerTemplate]:
    """Get the full MCP server catalog."""
    return MCP_SERVER_CATALOG


def get_template(template_id: str) -> Optional[MCPServerTemplate]:
    """Get a specific template by ID."""
    return MCP_SERVER_CATALOG.get(template_id)


def list_templates() -> List[MCPServerTemplate]:
    """List all available templates."""
    return list(MCP_SERVER_CATALOG.values())

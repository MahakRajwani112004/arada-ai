# Magure AI Platform - API Reference

Base URL: `http://localhost:8000/api/v1`

---

## Overview

| Domain | Endpoints | Description |
|--------|-----------|-------------|
| Agents | 4 | Create, list, get, delete agents |
| Workflow | 2 | Execute workflows, check status |
| MCP | 6 | Manage MCP server connections |
| OAuth | 3 | Google OAuth flow |

**Total: 15 endpoints**

---

## 1. Agents API

### Create Agent
```
POST /agents
```

Create a new agent with full configuration.

**Request Body:**
```json
{
  "id": "meeting-scheduler",
  "name": "Meeting Scheduler",
  "description": "Schedules meetings based on calendar availability",
  "agent_type": "ToolAgent",
  "role": {
    "title": "Executive Assistant",
    "expertise": ["scheduling", "calendar management"],
    "personality": "Professional and efficient",
    "communication_style": "Concise and clear"
  },
  "goal": {
    "objective": "Schedule meetings efficiently",
    "success_criteria": ["Meeting scheduled", "No conflicts"],
    "constraints": ["Business hours only"]
  },
  "instructions": {
    "steps": ["Check calendar", "Find available slot", "Create event"],
    "rules": ["Always confirm with user"],
    "prohibited_actions": ["Double-booking"],
    "output_format": "Confirmation message"
  },
  "examples": [
    {
      "input": "Schedule a meeting with John tomorrow",
      "output": "Meeting scheduled with John for tomorrow at 10 AM"
    }
  ],
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7
  },
  "tools": [
    {"tool_id": "google-calendar:list_events"},
    {"tool_id": "google-calendar:create_event"}
  ],
  "safety": {
    "level": "STANDARD",
    "blocked_topics": [],
    "blocked_patterns": []
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "meeting-scheduler",
  "name": "Meeting Scheduler",
  "description": "Schedules meetings based on calendar availability",
  "agent_type": "ToolAgent",
  "created": true
}
```

---

### List Agents
```
GET /agents
```

**Response:** `200 OK`
```json
{
  "agents": [
    {
      "id": "meeting-scheduler",
      "name": "Meeting Scheduler",
      "description": "...",
      "agent_type": "ToolAgent",
      "created": true
    }
  ],
  "total": 1
}
```

---

### Get Agent
```
GET /agents/{agent_id}
```

**Response:** `200 OK`
```json
{
  "id": "meeting-scheduler",
  "name": "Meeting Scheduler",
  "description": "...",
  "agent_type": "ToolAgent",
  "created": true
}
```

---

### Delete Agent
```
DELETE /agents/{agent_id}
```

**Response:** `204 No Content`

---

## 2. Workflow API

### Execute Workflow
```
POST /workflow/execute
```

Execute an agent workflow via Temporal.

**Request Body:**
```json
{
  "agent_id": "meeting-scheduler",
  "user_input": "Schedule a meeting with John tomorrow at 2pm",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ],
  "session_id": "session_abc123"
}
```

**Response:** `200 OK`
```json
{
  "content": "I've scheduled a meeting with John for tomorrow at 2 PM.",
  "agent_id": "meeting-scheduler",
  "agent_type": "ToolAgent",
  "success": true,
  "error": null,
  "metadata": {
    "tools_used": ["google-calendar:create_event"],
    "execution_time_ms": 1234
  },
  "workflow_id": "workflow_xyz789"
}
```

---

### Get Workflow Status
```
GET /workflow/status/{workflow_id}
```

**Response:** `200 OK`
```json
{
  "workflow_id": "workflow_xyz789",
  "status": "COMPLETED",
  "result": {
    "content": "Meeting scheduled successfully",
    "success": true
  }
}
```

**Status Values:** `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`

---

## 3. MCP API

### List Catalog
```
GET /mcp/catalog
```

List available MCP server templates.

**Response:** `200 OK`
```json
{
  "servers": [
    {
      "id": "google-calendar",
      "name": "Google Calendar",
      "url_template": "http://localhost:8001/mcp",
      "auth_type": "oauth_token",
      "token_guide_url": "https://developers.google.com/oauthplayground/",
      "scopes": ["https://www.googleapis.com/auth/calendar"],
      "credentials_required": [
        {
          "name": "GOOGLE_REFRESH_TOKEN",
          "description": "OAuth refresh token",
          "sensitive": true,
          "header_name": "X-Google-Refresh-Token"
        }
      ],
      "credentials_optional": [],
      "tools": ["list_events", "create_event", "delete_event"]
    }
  ],
  "total": 6
}
```

---

### Get Catalog Template
```
GET /mcp/catalog/{template_id}
```

**Response:** `200 OK`
```json
{
  "id": "google-calendar",
  "name": "Google Calendar",
  "url_template": "http://localhost:8001/mcp",
  "auth_type": "oauth_token",
  "scopes": ["https://www.googleapis.com/auth/calendar"],
  "credentials_required": [...],
  "tools": ["list_events", "create_event", "delete_event"]
}
```

---

### Create MCP Server (from template)
```
POST /mcp/servers
```

**Request Body:**
```json
{
  "template": "google-calendar",
  "name": "My Work Calendar",
  "credentials": {
    "GOOGLE_REFRESH_TOKEN": "1//04xxx..."
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "srv_abc123",
  "name": "My Work Calendar",
  "template": "google-calendar",
  "url": "http://localhost:8001/mcp",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "last_used": null,
  "error_message": null
}
```

---

### Create MCP Server (custom)
```
POST /mcp/servers
```

**Request Body:**
```json
{
  "name": "My Custom MCP",
  "url": "https://my-mcp-server.example.com/mcp",
  "credentials": {},
  "headers": {
    "Authorization": "Bearer token123"
  }
}
```

---

### List MCP Servers
```
GET /mcp/servers
```

**Response:** `200 OK`
```json
{
  "servers": [
    {
      "id": "srv_abc123",
      "name": "My Work Calendar",
      "template": "google-calendar",
      "url": "http://localhost:8001/mcp",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### Get MCP Server Details
```
GET /mcp/servers/{server_id}
```

**Response:** `200 OK`
```json
{
  "id": "srv_abc123",
  "name": "My Work Calendar",
  "template": "google-calendar",
  "url": "http://localhost:8001/mcp",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "tools": [
    {
      "name": "list_events",
      "description": "List calendar events for a given date range",
      "input_schema": {...}
    },
    {
      "name": "create_event",
      "description": "Create a new calendar event",
      "input_schema": {...}
    }
  ]
}
```

---

### Delete MCP Server
```
DELETE /mcp/servers/{server_id}
```

**Response:** `204 No Content`

---

### MCP Health Check
```
GET /mcp/health
```

**Response:** `200 OK`
```json
{
  "servers": [
    {
      "id": "srv_abc123",
      "name": "My Work Calendar",
      "status": "active",
      "last_checked": "2024-01-15T10:35:00Z"
    }
  ],
  "total_active": 1,
  "total_error": 0,
  "total_disconnected": 0
}
```

---

## 4. OAuth API

### Start Google OAuth Flow
```
GET /oauth/google/authorize?service=calendar
```

Redirects to Google consent screen.

**Query Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| service | Yes | `calendar`, `gmail`, or `drive` |
| state | No | State to pass through OAuth |

**Response:** `302 Redirect` to Google OAuth

---

### OAuth Callback
```
GET /oauth/google/callback?code=xxx&state=yyy
```

Handles Google OAuth redirect.

**Response:** `200 OK`
```json
{
  "refresh_token": "1//04xxx...",
  "service": "calendar",
  "message": "Successfully authorized Google Calendar"
}
```

---

### Get Authorization URL
```
GET /oauth/google/authorize-url?service=calendar
```

Get OAuth URL without redirect (for SPAs).

**Response:** `200 OK`
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "service": "calendar"
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 500 | Internal Server Error |

---

## MCP Server Catalog

Available templates in the catalog:

| Template ID | Name | Tools |
|-------------|------|-------|
| google-calendar | Google Calendar | list_events, create_event, delete_event |
| google-gmail | Gmail | list_emails, get_email, send_email |
| google-drive | Google Drive | list_files, upload_file, download_file |
| outlook-calendar | Outlook Calendar | list_events, create_event, delete_event |
| outlook-email | Outlook Email | list_emails, send_email, search_emails |
| slack | Slack | send_message, list_channels, search_messages |

---

## Running MCP Servers Locally

```bash
# Terminal 1 - Calendar (port 8001)
cd mcp_servers/google-calendar
pip install -r requirements.txt
python server.py

# Terminal 2 - Gmail (port 8002)
cd mcp_servers/google-gmail
pip install -r requirements.txt
python server.py
```

---

## Authentication Flow

1. User calls `GET /oauth/google/authorize?service=calendar`
2. User is redirected to Google consent screen
3. After consent, Google redirects to `/oauth/google/callback`
4. Callback returns `refresh_token`
5. User creates MCP server with `POST /mcp/servers` including the refresh token
6. Refresh token is stored securely in vault
7. MCP tools are now available for agent workflows

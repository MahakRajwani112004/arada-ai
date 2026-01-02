# MagoneAI Platform - API Reference

Base URL: `http://localhost:8000/api/v1`

---

## Overview

| Domain | Endpoints | Description |
|--------|-----------|-------------|
| Agents | 5 | Create, list, get, update, delete agents |
| Skills | 6 | Create, list, get, update, delete skills + file upload |
| Workflows | 6 | Create, list, get, update, delete workflows + executions |
| Workflow Execution | 2 | Execute workflows, check status |
| MCP | 6 | Manage MCP server connections |
| OAuth | 3 | Google OAuth flow |
| Knowledge | 4 | Knowledge base management |
| Auth | 3 | Authentication endpoints |

**Total: 35+ endpoints**

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

## 2. Skills API

### List Skills
```
GET /skills
```

List all available skills.

**Query Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| category | No | Filter by category (e.g., `domain_expertise`) |
| status | No | Filter by status (`draft`, `published`) |
| limit | No | Pagination limit (default: 50) |
| offset | No | Pagination offset (default: 0) |

**Response:** `200 OK`
```json
{
  "skills": [
    {
      "id": "legal-contract-analysis",
      "name": "Legal Contract Analysis",
      "category": "domain_expertise",
      "version": 1,
      "status": "published",
      "rating_avg": 4.5,
      "install_count": 12
    }
  ],
  "total": 1
}
```

---

### Create Skill
```
POST /skills
```

Create a new skill with domain expertise.

**Request Body:**
```json
{
  "name": "Legal Contract Analysis",
  "category": "domain_expertise",
  "tags": ["legal", "contracts", "review"],
  "definition": {
    "capability": {
      "expertise": {
        "domain": "legal",
        "terminology": [
          {
            "term": "Force Majeure",
            "definition": "Unforeseeable circumstances preventing fulfillment",
            "aliases": ["act of god"]
          }
        ],
        "reasoning_patterns": [
          {
            "name": "Contract Review Process",
            "steps": [
              "Identify parties and dates",
              "Review key terms",
              "Analyze obligations",
              "Check liability limitations"
            ]
          }
        ],
        "examples": [
          {
            "input": "Review this NDA",
            "output": "Key findings: 1. Non-compete is 3 years..."
          }
        ]
      }
    },
    "resources": {
      "files": [],
      "code_snippets": []
    },
    "parameters": [
      {
        "name": "analysis_depth",
        "type": "select",
        "options": ["quick", "standard", "comprehensive"],
        "default_value": "standard"
      }
    ]
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "skill_abc123",
  "name": "Legal Contract Analysis",
  "category": "domain_expertise",
  "version": 1,
  "status": "draft"
}
```

---

### Get Skill
```
GET /skills/{skill_id}
```

Get complete skill definition.

**Response:** `200 OK`
```json
{
  "id": "legal-contract-analysis",
  "name": "Legal Contract Analysis",
  "category": "domain_expertise",
  "definition": {
    "capability": {...},
    "resources": {...},
    "parameters": [...]
  },
  "version": 1,
  "status": "published"
}
```

---

### Update Skill
```
PUT /skills/{skill_id}
```

Update an existing skill.

**Request Body:** Same as Create Skill

**Response:** `200 OK`

---

### Delete Skill
```
DELETE /skills/{skill_id}
```

**Response:** `204 No Content`

---

### Upload Skill File
```
POST /skills/{skill_id}/files
```

Upload a reference document or template.

**Content-Type:** `multipart/form-data`

**Form Data:**
| Field | Type | Description |
|-------|------|-------------|
| file | File | The file to upload |
| file_type | String | `reference` or `template` |
| description | String | File description |

**Response:** `201 Created`
```json
{
  "file_id": "file_xyz123",
  "filename": "contract-template.docx",
  "file_type": "template",
  "size_bytes": 45678
}
```

---

## 3. Workflows API

### List Workflows
```
GET /workflows
```

**Response:** `200 OK`
```json
{
  "workflows": [
    {
      "id": "customer-support-pipeline",
      "name": "Customer Support Pipeline",
      "description": "Multi-step customer support flow",
      "category": "support",
      "version": 2,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Create Workflow
```
POST /workflows
```

**Request Body:**
```json
{
  "name": "Customer Support Pipeline",
  "description": "Routes and handles customer requests",
  "category": "support",
  "steps": [
    {
      "id": "classify",
      "type": "agent",
      "agent_id": "intent-classifier",
      "input": "${user_input}"
    },
    {
      "id": "route",
      "type": "conditional",
      "condition_source": "${steps.classify.intent}",
      "conditional_branches": {
        "billing": "billing-agent-step",
        "technical": "tech-agent-step",
        "general": "general-agent-step"
      }
    }
  ],
  "entry_step": "classify",
  "connections": [
    {"from": "classify", "to": "route"}
  ]
}
```

**Response:** `201 Created`

---

### Get Workflow
```
GET /workflows/{workflow_id}
```

**Response:** `200 OK` with full workflow definition

---

### Update Workflow
```
PUT /workflows/{workflow_id}
```

**Request Body:** Same as Create Workflow

**Response:** `200 OK`

---

### Delete Workflow
```
DELETE /workflows/{workflow_id}
```

**Response:** `204 No Content`

---

### Get Workflow Executions
```
GET /workflows/{workflow_id}/executions
```

List execution history for a workflow.

**Query Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| status | No | Filter by status (`RUNNING`, `COMPLETED`, `FAILED`) |
| limit | No | Pagination limit |

**Response:** `200 OK`
```json
{
  "executions": [
    {
      "id": "exec_abc123",
      "workflow_id": "customer-support-pipeline",
      "status": "COMPLETED",
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:30:45Z",
      "steps_executed": ["classify", "route", "billing-agent-step"]
    }
  ],
  "total": 1
}
```

---

## 4. Workflow Execution API

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

## 5. MCP API

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

## 6. OAuth API

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

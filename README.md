# MagOneAI v2

A dynamic AI agent platform built with FastAPI, Temporal workflows, and MCP (Model Context Protocol) integration. Create, configure, and deploy AI agents with tools, RAG capabilities, and native LLM function calling.

## Features

- **Dynamic Agent Types**: Simple, LLM, RAG, Tool, Full, and Router agents
- **Native Tool Calling**: OpenAI and Anthropic function calling support
- **MCP Integration**: Connect to external services via Model Context Protocol
- **Temporal Workflows**: Durable, reliable agent execution with automatic retries
- **Multi-Provider LLM**: Support for OpenAI and Anthropic models
- **Built-in Tools**: Calculator, datetime, and extensible tool registry
- **OAuth Integration**: Google Calendar, Gmail, Drive support
- **Modern Web UI**: Next.js frontend for agent management

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js UI    │────▶│   FastAPI       │────▶│   Temporal      │
│   (Port 3000)   │     │   (Port 8000)   │     │   (Port 7233)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   PostgreSQL    │     │   Agent Worker  │
                        │   (Port 5432)   │     │                 │
                        └─────────────────┘     └─────────────────┘
                                                       │
                               ┌───────────────────────┼───────────────────────┐
                               ▼                       ▼                       ▼
                        ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
                        │ MCP Server  │         │ LLM Provider│         │ Tool        │
                        │ (Calendar)  │         │ (OpenAI)    │         │ Registry    │
                        └─────────────┘         └─────────────┘         └─────────────┘
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL (or use Docker)
- Temporal Server (or use Docker)

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd magoneai_v2

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required environment variables:
```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/magure

# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=agent-tasks

# LLM Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Google OAuth (optional, for calendar/gmail integration)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Secrets encryption
SECRETS_ENCRYPTION_KEY=your-32-byte-key-here
```

### 3. Start Infrastructure

```bash
# Start PostgreSQL and Temporal using Docker
cd docker
docker-compose up -d
cd ..

# Wait for services to be ready
sleep 10
```

### 4. Run the Application

You need 3 terminals:

**Terminal 1 - API Server:**
```bash
source .venv/bin/activate
PYTHONPATH=. python -c "
from dotenv import load_dotenv
load_dotenv()
import uvicorn
uvicorn.run('src.api.app:app', host='0.0.0.0', port=8000, reload=True)
"
```

**Terminal 2 - Temporal Worker:**
```bash
source .venv/bin/activate
PYTHONPATH=. python workers/agent_worker.py
```

**Terminal 3 - MCP Server (optional, for Google Calendar):**
```bash
source .venv/bin/activate
cd mcp_servers/google-calendar
python server.py
```

**Terminal 4 - Web UI:**
```bash
cd web
npm install
npm run dev
```

### 5. Access the Application

- **Web UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Agents
- `GET /api/v1/agents` - List all agents
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/agents/{id}` - Get agent
- `DELETE /api/v1/agents/{id}` - Delete agent

### Workflows
- `POST /api/v1/workflow/execute` - Execute agent workflow

### MCP Servers
- `GET /api/v1/mcp/servers` - List MCP servers
- `POST /api/v1/mcp/servers` - Add MCP server
- `DELETE /api/v1/mcp/servers/{id}` - Remove MCP server
- `GET /api/v1/mcp/catalog` - List available templates

### OAuth
- `GET /api/v1/oauth/google/authorize?service=calendar` - Start Google OAuth
- `GET /api/v1/oauth/google/callback` - OAuth callback

## Creating an Agent

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-assistant",
    "name": "My Assistant",
    "description": "A helpful assistant",
    "agent_type": "ToolAgent",
    "role": {
      "title": "Assistant",
      "expertise": ["general"],
      "personality": ["helpful"],
      "communication_style": "friendly"
    },
    "goal": {
      "objective": "Help users with their tasks"
    },
    "llm_config": {
      "provider": "openai",
      "model": "gpt-4o-mini"
    },
    "tools": [
      {"tool_id": "datetime", "enabled": true},
      {"tool_id": "calculator", "enabled": true}
    ]
  }'
```

### Execute Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-assistant",
    "user_input": "What time is it?",
    "conversation_history": []
  }'
```

## Project Structure

```
magoneai_v2/
├── src/
│   ├── api/              # FastAPI application
│   │   ├── routers/      # API endpoints
│   │   └── app.py        # Main app
│   ├── agents/           # Agent definitions
│   ├── activities/       # Temporal activities
│   ├── workflows/        # Temporal workflows
│   ├── llm/              # LLM providers
│   ├── mcp/              # MCP client & manager
│   ├── tools/            # Tool registry & builtins
│   ├── storage/          # Database models & repos
│   └── secrets/          # Secrets management
├── workers/
│   └── agent_worker.py   # Temporal worker
├── mcp_servers/
│   ├── google-calendar/  # Google Calendar MCP
│   └── google-gmail/     # Gmail MCP
├── web/                  # Next.js frontend
├── docker/               # Docker configs
├── docs/                 # Documentation
└── tests/                # Test suite
```

## Agent Types

| Type | Description | Features |
|------|-------------|----------|
| Simple | Pattern matching | No LLM, rule-based |
| LLM | Single LLM call | Basic chat |
| RAG | Retrieval + LLM | Knowledge base |
| Tool | LLM + Tools | Function calling |
| Full | RAG + Tools | Complete agent |
| Router | Classification | Route to other agents |

## Adding Custom Tools

```python
# src/tools/custom/my_tool.py
from src.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult

class MyTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="my_tool",
            description="Does something useful",
            parameters=[
                ToolParameter(
                    name="input",
                    type="string",
                    description="Input value",
                    required=True,
                ),
            ],
        )

    async def execute(self, input: str) -> ToolResult:
        result = f"Processed: {input}"
        return ToolResult(success=True, output=result)
```

Register in `src/tools/builtin/__init__.py`:
```python
from src.tools.custom.my_tool import MyTool
registry.register(MyTool())
```

## Troubleshooting

### Temporal Connection Error
```bash
# Ensure Temporal is running
docker-compose -f docker/docker-compose.yml ps

# Check Temporal UI at http://localhost:8080
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose -f docker/docker-compose.yml logs postgres
```

### MCP Tool Not Found
```bash
# Ensure worker has MCP tools registered
# Check worker logs for "mcp_tools_registered"
```

### OAuth "unauthorized_client" Error
The refresh token was created with different OAuth credentials. Re-authorize:
```
http://localhost:8000/api/v1/oauth/google/authorize?service=calendar
```

## License

MIT

# MagoneAI Multi-Tenant Workflow Deployment
## External API for Custom Frontend Integration

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Options](#architecture-options)
   - [Option 1: Single Backend API (Recommended)](#option-1-single-backend-api-recommended)
   - [Option 2: Separate Gateway Service](#option-2-separate-gateway-service)
3. [Data Model](#data-model)
4. [API Design](#api-design)
5. [Database Schema](#database-schema)
6. [Implementation - Option 1](#implementation---option-1-single-backend)
7. [Implementation - Option 2](#implementation---option-2-separate-gateway)
8. [Docker Compose - Option 1](#docker-compose---option-1)
9. [Docker Compose - Option 2](#docker-compose---option-2)
10. [Monitoring](#monitoring)
11. [Tenant Management](#tenant-management)
12. [Frontend Integration](#frontend-integration)

---

## Overview

This document describes two deployment options for exposing MagoneAI workflows to external frontends (like Magure) with multi-tenant support.

### Use Case

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TENANT: MAGURE                                                               │
│                                                                              │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                │
│ │ Workflow 1      │ │ Workflow 2      │ │ Workflow 3      │                │
│ │ kpi-sales       │ │ kpi-ops         │ │ analytics       │                │
│ │ (3 agents)      │ │ (2 agents)      │ │ (5 agents)      │                │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘                │
│                                                                              │
│ API Key: magure_live_abc123...                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              External FE calls → POST /api/v1/external/execute/kpi-sales
```

---

## Architecture Options

### Option 1: Single Backend API (Recommended)

**Add external endpoints to your existing Backend API. Simplest approach.**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL FRONTENDS                                   │
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│   │  Magure FE   │    │  Client B FE │    │  Client C FE │                 │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                 │
│          │                   │                   │                          │
└──────────┼───────────────────┼───────────────────┼──────────────────────────┘
           │                   │                   │
           │         X-API-Key: tenant_live_xxx    │
           └───────────────────┼───────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRAEFIK (TLS + Routing)                               │
│                           Ports: 80, 443                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Admin Web UI  │  │   Backend API   │  │   Temporal UI   │
│   (:3000)       │  │   (:8000)       │  │   (:8080)       │
│                 │  │                 │  │                 │
│   admin.domain  │  │   api.domain    │  │  temporal.domain│
└─────────────────┘  └────────┬────────┘  └─────────────────┘
                              │
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        │           BACKEND API (:8000)             │
        │                                           │
        │  INTERNAL ENDPOINTS (existing):           │
        │  ├── POST /api/v1/workflow/execute        │
        │  ├── GET  /api/v1/agents                  │
        │  ├── POST /api/v1/agents                  │
        │  └── ...                                  │
        │                                           │
        │  EXTERNAL ENDPOINTS (new):                │
        │  ├── POST /api/v1/external/execute/{slug} │ ← Tenant API Key Auth
        │  ├── GET  /api/v1/external/workflows      │ ← Tenant API Key Auth
        │  ├── GET  /api/v1/external/executions/{id}│ ← Tenant API Key Auth
        │  └── GET  /health                         │ ← No auth
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              │ Temporal Client (gRPC)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEMPORAL SERVER (:7233)                               │
│                       Workflow Orchestration                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Task Queue: "agent-tasks"
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEMPORAL WORKERS (2-10 replicas)                      │
│                                                                              │
│   Activities:                                                                │
│   • llm_completion() → OpenAI/Anthropic                                     │
│   • execute_tool() → MCP servers, built-in tools                            │
│   • retrieve_knowledge() → Qdrant RAG                                       │
│   • execute_agent_as_tool() → Sub-agents                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │     Qdrant      │  │      Redis      │
│    (:5432)      │  │    (:6333)      │  │    (:6379)      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Pros:**
- Single service to maintain
- No extra network hop
- Simpler deployment
- Shared database connection pool

**Cons:**
- Mixes internal and external concerns in one codebase

---

### Option 2: Separate Gateway Service

**Gateway handles tenant auth, then calls Backend API internally.**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL FRONTENDS                                   │
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│   │  Magure FE   │    │  Client B FE │    │  Client C FE │                 │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                 │
│          │                   │                   │                          │
└──────────┼───────────────────┼───────────────────┼──────────────────────────┘
           │                   │                   │
           │         X-API-Key: tenant_live_xxx    │
           └───────────────────┼───────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRAEFIK (TLS + Routing)                               │
│                           Ports: 80, 443                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Admin Web UI  │  │ WORKFLOW GATEWAY│  │   Temporal UI   │
│   (:3000)       │  │   (:5005)       │  │   (:8080)       │
│                 │  │                 │  │                 │
│   admin.domain  │  │ workflows.domain│  │  temporal.domain│
└─────────────────┘  └────────┬────────┘  └─────────────────┘
                              │
                              │ POST /api/v1/execute/{slug}
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        │         WORKFLOW GATEWAY (:5005)          │
        │                                           │
        │  • Tenant authentication (API keys)       │
        │  • Rate limiting per tenant               │
        │  • Maps tenant slug → workflow            │
        │  • Execution tracking                     │
        │                                           │
        │  Endpoints:                               │
        │  ├── POST /api/v1/execute/{slug}          │
        │  ├── POST /api/v1/execute/{slug}/async    │
        │  ├── GET  /api/v1/workflows               │
        │  ├── GET  /api/v1/executions/{id}         │
        │  └── GET  /health                         │
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              │ HTTP: POST http://api:8000/api/v1/workflow/execute
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND API (:8000)                                   │
│                       (Your Existing FastAPI)                                │
│                                                                              │
│   • Agent management (CRUD)                                                  │
│   • Workflow definitions                                                     │
│   • MCP server management                                                    │
│   • Tool registry                                                            │
│                                                                              │
│   POST /api/v1/workflow/execute  ←── Gateway calls this                      │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Temporal Client (gRPC)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEMPORAL SERVER (:7233)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEMPORAL WORKERS                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │     Qdrant      │  │      Redis      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Pros:**
- Clean separation of external vs internal
- Gateway can be scaled independently
- External API changes don't affect internal API

**Cons:**
- Extra network hop (Gateway → Backend)
- Two services to maintain
- Slightly higher latency

---

## Comparison Table

| Aspect | Option 1 (Single API) | Option 2 (Gateway) |
|--------|----------------------|-------------------|
| **Services** | 1 | 2 |
| **Latency** | Lower | Higher (+1 hop) |
| **Complexity** | Lower | Medium |
| **Separation** | Mixed | Clean |
| **Scaling** | Together | Independent |
| **Deployment** | Simpler | More containers |
| **Recommended for** | Most cases | Large teams, strict separation |

---

## Data Model

### Tenant → Workflows → Executions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TENANT: magure                                                               │
│ API Key: mgr_live_abc123...                                                 │
│ Rate Limit: 60/min                                                          │
│                                                                              │
│ ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐    │
│ │ WORKFLOW: kpi-sales │ │ WORKFLOW: kpi-ops   │ │ WORKFLOW: analytics │    │
│ │ Agents: [analyzer,  │ │ Agents: [ops-agent, │ │ Agents: [data-agent,│    │
│ │  formatter, kpi]    │ │  calculator]        │ │  chart-gen]         │    │
│ │                     │ │                     │ │                     │    │
│ │ Executions:         │ │ Executions:         │ │ Executions:         │    │
│ │ • exec_001 ✓        │ │ • exec_101 ✓        │ │ • exec_201 ⏳       │    │
│ │ • exec_002 ✓        │ │ • exec_102 ✗        │ │ • exec_202 ✓        │    │
│ └─────────────────────┘ └─────────────────────┘ └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## API Design

### External Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/external/execute/{workflow_slug}` | Execute workflow (sync) | API Key |
| `POST` | `/api/v1/external/execute/{workflow_slug}/async` | Execute workflow (async) | API Key |
| `GET` | `/api/v1/external/workflows` | List tenant's workflows | API Key |
| `GET` | `/api/v1/external/workflows/{workflow_slug}` | Get workflow details | API Key |
| `GET` | `/api/v1/external/executions/{execution_id}` | Get execution status/result | API Key |
| `GET` | `/health` | Health check | None |

### Authentication

Simple API key in header:
```
X-API-Key: magure_live_abc123xyz...
```

### Example Requests

**Execute KPI Workflow (Sync)**
```bash
curl -X POST https://api.magoneai.com/api/v1/external/execute/kpi-sales \
  -H "X-API-Key: magure_live_abc123xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Show me Q4 sales KPIs for Dubai region",
    "context": {
      "region": "dubai",
      "quarter": "Q4",
      "year": 2024
    }
  }'
```

**Response**
```json
{
  "execution_id": "exec_abc123",
  "status": "completed",
  "workflow_slug": "kpi-sales",
  "result": {
    "kpis": [
      {"name": "Total Sales", "value": 12500000, "unit": "AED", "change": "+15%"},
      {"name": "Units Sold", "value": 45, "unit": "units", "change": "+8%"},
      {"name": "Avg Price", "value": 277778, "unit": "AED/unit", "change": "+6%"}
    ],
    "summary": "Q4 2024 shows strong performance...",
    "chart_data": {...}
  },
  "metadata": {
    "duration_ms": 2340,
    "agents_used": ["data-analyzer", "kpi-calculator", "formatter"]
  }
}
```

**Execute Async (for long-running workflows)**
```bash
curl -X POST https://api.magoneai.com/api/v1/external/execute/analytics/async \
  -H "X-API-Key: magure_live_abc123xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Generate full portfolio analysis report",
    "webhook_url": "https://magure.com/webhooks/workflow-complete"
  }'
```

**Response**
```json
{
  "execution_id": "exec_xyz789",
  "status": "running",
  "status_url": "/api/v1/external/executions/exec_xyz789"
}
```

---

## Database Schema

### New Tables (Same for Both Options)

```sql
-- Tenants table
CREATE TABLE tenants (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    api_key_prefix VARCHAR(50) NOT NULL,  -- For display: "mgr_live_abc..."
    settings JSONB DEFAULT '{}',
    rate_limit_per_minute INT DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenant workflows (links tenant to workflow definitions)
CREATE TABLE tenant_workflows (
    id VARCHAR(100) PRIMARY KEY,
    tenant_id VARCHAR(100) REFERENCES tenants(id) ON DELETE CASCADE,
    workflow_definition_id VARCHAR(100) REFERENCES workflow_definitions(id),
    slug VARCHAR(100) NOT NULL,  -- tenant-specific slug
    name VARCHAR(255),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    config_overrides JSONB DEFAULT '{}',  -- tenant-specific config
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, slug)
);

-- Workflow executions
CREATE TABLE workflow_executions (
    id VARCHAR(100) PRIMARY KEY,
    tenant_id VARCHAR(100) REFERENCES tenants(id),
    tenant_workflow_id VARCHAR(100) REFERENCES tenant_workflows(id),
    temporal_workflow_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
    input JSONB,
    result JSONB,
    error TEXT,
    webhook_url TEXT,
    webhook_sent BOOLEAN DEFAULT false,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tenant_workflows_tenant ON tenant_workflows(tenant_id);
CREATE INDEX idx_tenant_workflows_slug ON tenant_workflows(tenant_id, slug);
CREATE INDEX idx_executions_tenant ON workflow_executions(tenant_id);
CREATE INDEX idx_executions_status ON workflow_executions(status);
CREATE INDEX idx_tenants_api_key ON tenants(api_key_hash);
```

---

## Implementation - Option 1 (Single Backend)

### Project Structure Changes

```
src/
├── api/
│   ├── app.py                    # Existing - add external router
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── agents.py             # Existing
│   │   ├── workflow.py           # Existing
│   │   ├── external.py           # NEW: External tenant endpoints
│   │   └── ...
│   └── dependencies.py           # Add tenant auth dependency
│
├── storage/
│   ├── models.py                 # Add Tenant, TenantWorkflow, Execution models
│   └── tenant_repository.py      # NEW: Tenant data access
```

### 1. Tenant Authentication (`src/api/auth/tenant_auth.py`)

```python
"""Tenant API Key authentication."""
import hashlib
from typing import Optional

from fastapi import Header, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.database import get_session
from src.storage.models import TenantModel


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage/comparison."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_current_tenant(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    session: AsyncSession = Depends(get_session),
) -> TenantModel:
    """Validate API key and return tenant."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key_hash = hash_api_key(x_api_key)

    result = await session.execute(
        select(TenantModel).where(
            TenantModel.api_key_hash == key_hash,
            TenantModel.is_active == True,
        )
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return tenant
```

### 2. External Router (`src/api/routers/external.py`)

```python
"""External API endpoints for tenant workflow execution."""
from datetime import timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio.client import Client

from src.api.auth.tenant_auth import get_current_tenant
from src.config.logging import get_logger
from src.storage.database import get_session
from src.storage.models import TenantModel, TenantWorkflowModel, WorkflowExecutionModel
from src.workflows.agent_workflow import AgentWorkflow, AgentWorkflowInput
from src.api.routers.workflow import get_temporal_client, TASK_QUEUE

logger = get_logger(__name__)
router = APIRouter(prefix="/external", tags=["external"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ExecuteRequest(BaseModel):
    """Request to execute a workflow."""
    input: str = Field(..., description="User input/query")
    context: Optional[Dict[str, Any]] = Field(default=None)
    session_id: Optional[str] = Field(default=None)


class ExecuteAsyncRequest(ExecuteRequest):
    """Request to execute workflow asynchronously."""
    webhook_url: Optional[str] = Field(default=None)


class ExecuteResponse(BaseModel):
    """Response from workflow execution."""
    execution_id: str
    status: str
    workflow_slug: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AsyncExecuteResponse(BaseModel):
    """Response from async workflow execution."""
    execution_id: str
    status: str
    status_url: str


class WorkflowInfo(BaseModel):
    """Workflow information for listing."""
    slug: str
    name: Optional[str]
    description: Optional[str]


class WorkflowListResponse(BaseModel):
    """List of tenant workflows."""
    workflows: List[WorkflowInfo]
    total: int


class ExecutionStatusResponse(BaseModel):
    """Execution status response."""
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    tenant: TenantModel = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """List all workflows available to the tenant."""
    result = await session.execute(
        select(TenantWorkflowModel).where(
            TenantWorkflowModel.tenant_id == tenant.id,
            TenantWorkflowModel.is_active == True,
        )
    )
    workflows = result.scalars().all()

    return WorkflowListResponse(
        workflows=[
            WorkflowInfo(
                slug=w.slug,
                name=w.name,
                description=w.description,
            )
            for w in workflows
        ],
        total=len(workflows),
    )


@router.get("/workflows/{workflow_slug}", response_model=WorkflowInfo)
async def get_workflow(
    workflow_slug: str,
    tenant: TenantModel = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """Get workflow details."""
    result = await session.execute(
        select(TenantWorkflowModel).where(
            TenantWorkflowModel.tenant_id == tenant.id,
            TenantWorkflowModel.slug == workflow_slug,
            TenantWorkflowModel.is_active == True,
        )
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_slug}' not found",
        )

    return WorkflowInfo(
        slug=workflow.slug,
        name=workflow.name,
        description=workflow.description,
    )


@router.post("/execute/{workflow_slug}", response_model=ExecuteResponse)
async def execute_workflow(
    workflow_slug: str,
    request: ExecuteRequest,
    tenant: TenantModel = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """Execute a workflow synchronously."""
    # Get tenant workflow
    result = await session.execute(
        select(TenantWorkflowModel).where(
            TenantWorkflowModel.tenant_id == tenant.id,
            TenantWorkflowModel.slug == workflow_slug,
            TenantWorkflowModel.is_active == True,
        )
    )
    tenant_workflow = result.scalar_one_or_none()

    if not tenant_workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_slug}' not found",
        )

    execution_id = f"exec_{uuid4().hex[:12]}"
    temporal_workflow_id = f"tenant-{tenant.slug}-{execution_id}"

    # Build workflow input
    workflow_input = _build_workflow_input(
        tenant_workflow=tenant_workflow,
        user_input=request.input,
        context=request.context,
        session_id=request.session_id,
    )

    try:
        # Execute via Temporal
        client = await get_temporal_client()
        result = await client.execute_workflow(
            AgentWorkflow.run,
            workflow_input,
            id=temporal_workflow_id,
            task_queue=TASK_QUEUE,
            execution_timeout=timedelta(seconds=300),
        )

        # Save execution record
        execution = WorkflowExecutionModel(
            id=execution_id,
            tenant_id=tenant.id,
            tenant_workflow_id=tenant_workflow.id,
            temporal_workflow_id=temporal_workflow_id,
            status="completed" if result.success else "failed",
            input={"user_input": request.input, "context": request.context},
            result={"content": result.content, "metadata": result.metadata},
            error=result.error,
        )
        session.add(execution)
        await session.commit()

        return ExecuteResponse(
            execution_id=execution_id,
            status="completed" if result.success else "failed",
            workflow_slug=workflow_slug,
            result={
                "content": result.content,
                "data": result.metadata.get("structured_data") if result.metadata else None,
            },
            error=result.error,
            metadata={
                "duration_ms": result.metadata.get("duration_ms") if result.metadata else None,
                "agents_used": result.metadata.get("agents_used", []) if result.metadata else [],
            },
        )

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)

        # Save failed execution
        execution = WorkflowExecutionModel(
            id=execution_id,
            tenant_id=tenant.id,
            tenant_workflow_id=tenant_workflow.id,
            temporal_workflow_id=temporal_workflow_id,
            status="failed",
            input={"user_input": request.input, "context": request.context},
            error=str(e),
        )
        session.add(execution)
        await session.commit()

        return ExecuteResponse(
            execution_id=execution_id,
            status="failed",
            workflow_slug=workflow_slug,
            error=str(e),
        )


@router.post("/execute/{workflow_slug}/async", response_model=AsyncExecuteResponse)
async def execute_workflow_async(
    workflow_slug: str,
    request: ExecuteAsyncRequest,
    background_tasks: BackgroundTasks,
    tenant: TenantModel = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """Execute a workflow asynchronously."""
    # Get tenant workflow
    result = await session.execute(
        select(TenantWorkflowModel).where(
            TenantWorkflowModel.tenant_id == tenant.id,
            TenantWorkflowModel.slug == workflow_slug,
            TenantWorkflowModel.is_active == True,
        )
    )
    tenant_workflow = result.scalar_one_or_none()

    if not tenant_workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_slug}' not found",
        )

    execution_id = f"exec_{uuid4().hex[:12]}"

    # Create pending execution record
    execution = WorkflowExecutionModel(
        id=execution_id,
        tenant_id=tenant.id,
        tenant_workflow_id=tenant_workflow.id,
        status="pending",
        input={"user_input": request.input, "context": request.context},
        webhook_url=request.webhook_url,
    )
    session.add(execution)
    await session.commit()

    # Start execution in background
    background_tasks.add_task(
        _execute_async_workflow,
        tenant=tenant,
        tenant_workflow=tenant_workflow,
        execution_id=execution_id,
        user_input=request.input,
        context=request.context,
        session_id=request.session_id,
        webhook_url=request.webhook_url,
    )

    return AsyncExecuteResponse(
        execution_id=execution_id,
        status="running",
        status_url=f"/api/v1/external/executions/{execution_id}",
    )


@router.get("/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    tenant: TenantModel = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """Get execution status and result."""
    result = await session.execute(
        select(WorkflowExecutionModel).where(
            WorkflowExecutionModel.id == execution_id,
            WorkflowExecutionModel.tenant_id == tenant.id,
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found",
        )

    return ExecutionStatusResponse(
        execution_id=execution.id,
        status=execution.status,
        result=execution.result,
        error=execution.error,
        started_at=execution.started_at.isoformat() if execution.started_at else None,
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
    )


# =============================================================================
# Helper Functions
# =============================================================================

def _build_workflow_input(
    tenant_workflow: TenantWorkflowModel,
    user_input: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> AgentWorkflowInput:
    """Build AgentWorkflowInput from tenant workflow config."""
    config = tenant_workflow.workflow_definition
    overrides = tenant_workflow.config_overrides or {}

    # Merge context
    merged_context = {**(config.context or {}), **(context or {})}

    return AgentWorkflowInput(
        agent_id=overrides.get("entry_agent_id") or config.id,
        agent_type="orchestrator",
        user_input=user_input,
        session_id=session_id or f"session_{uuid4().hex[:8]}",
        workflow_definition={
            "steps": [s.model_dump() if hasattr(s, 'model_dump') else s for s in config.steps],
            "entry_step": config.entry_step,
            "context": merged_context,
        },
        orchestrator_mode="workflow",
    )


async def _execute_async_workflow(
    tenant: TenantModel,
    tenant_workflow: TenantWorkflowModel,
    execution_id: str,
    user_input: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    webhook_url: Optional[str] = None,
):
    """Execute workflow in background and update status."""
    from src.storage.database import async_session_factory
    from datetime import datetime, timezone
    import httpx

    temporal_workflow_id = f"tenant-{tenant.slug}-{execution_id}"

    async with async_session_factory() as session:
        try:
            # Update status to running
            result = await session.execute(
                select(WorkflowExecutionModel).where(
                    WorkflowExecutionModel.id == execution_id
                )
            )
            execution = result.scalar_one()
            execution.status = "running"
            execution.started_at = datetime.now(timezone.utc)
            execution.temporal_workflow_id = temporal_workflow_id
            await session.commit()

            # Build and execute workflow
            workflow_input = _build_workflow_input(
                tenant_workflow=tenant_workflow,
                user_input=user_input,
                context=context,
                session_id=session_id,
            )

            client = await get_temporal_client()
            result = await client.execute_workflow(
                AgentWorkflow.run,
                workflow_input,
                id=temporal_workflow_id,
                task_queue=TASK_QUEUE,
                execution_timeout=timedelta(seconds=600),
            )

            # Update with result
            db_result = await session.execute(
                select(WorkflowExecutionModel).where(
                    WorkflowExecutionModel.id == execution_id
                )
            )
            execution = db_result.scalar_one()
            execution.status = "completed" if result.success else "failed"
            execution.result = {"content": result.content, "metadata": result.metadata}
            execution.error = result.error
            execution.completed_at = datetime.now(timezone.utc)
            await session.commit()

            # Send webhook if configured
            if webhook_url:
                async with httpx.AsyncClient() as http_client:
                    await http_client.post(
                        webhook_url,
                        json={
                            "execution_id": execution_id,
                            "status": execution.status,
                            "result": execution.result,
                        },
                        timeout=30,
                    )
                execution.webhook_sent = True
                await session.commit()

        except Exception as e:
            logger.error(f"Async workflow failed: {e}", exc_info=True)

            db_result = await session.execute(
                select(WorkflowExecutionModel).where(
                    WorkflowExecutionModel.id == execution_id
                )
            )
            execution = db_result.scalar_one()
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            await session.commit()

            if webhook_url:
                try:
                    async with httpx.AsyncClient() as http_client:
                        await http_client.post(
                            webhook_url,
                            json={
                                "execution_id": execution_id,
                                "status": "failed",
                                "error": str(e),
                            },
                            timeout=30,
                        )
                except Exception:
                    pass
```

### 3. Register Router (`src/api/app.py`)

Add to your existing app.py:

```python
# Add import
from src.api.routers import external

# Add router (after existing routers)
app.include_router(external.router, prefix="/api/v1")
```

### 4. Database Models (`src/storage/models.py`)

Add these models to your existing models.py:

```python
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class TenantModel(Base):
    """Tenant for multi-tenant workflow access."""
    __tablename__ = "tenants"

    id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    api_key_hash = Column(String(255), nullable=False)
    api_key_prefix = Column(String(50), nullable=False)
    settings = Column(JSONB, default={})
    rate_limit_per_minute = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workflows = relationship("TenantWorkflowModel", back_populates="tenant")
    executions = relationship("WorkflowExecutionModel", back_populates="tenant")


class TenantWorkflowModel(Base):
    """Links tenants to workflow definitions."""
    __tablename__ = "tenant_workflows"

    id = Column(String(100), primary_key=True)
    tenant_id = Column(String(100), ForeignKey("tenants.id", ondelete="CASCADE"))
    workflow_definition_id = Column(String(100), ForeignKey("workflow_definitions.id"))
    slug = Column(String(100), nullable=False)
    name = Column(String(255))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    config_overrides = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_tenant_workflow_slug"),
    )

    tenant = relationship("TenantModel", back_populates="workflows")
    workflow_definition = relationship("WorkflowDefinitionModel")
    executions = relationship("WorkflowExecutionModel", back_populates="tenant_workflow")


class WorkflowExecutionModel(Base):
    """Tracks workflow executions."""
    __tablename__ = "workflow_executions"

    id = Column(String(100), primary_key=True)
    tenant_id = Column(String(100), ForeignKey("tenants.id"))
    tenant_workflow_id = Column(String(100), ForeignKey("tenant_workflows.id"))
    temporal_workflow_id = Column(String(255))
    status = Column(String(50), default="pending")
    input = Column(JSONB)
    result = Column(JSONB)
    error = Column(Text)
    webhook_url = Column(Text)
    webhook_sent = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("TenantModel", back_populates="executions")
    tenant_workflow = relationship("TenantWorkflowModel", back_populates="executions")
```

---

## Implementation - Option 2 (Separate Gateway)

### Project Structure

```
src/
├── gateway/                      # NEW: Separate Gateway Service
│   ├── __init__.py
│   ├── app.py                    # FastAPI app for :5005
│   ├── auth.py                   # API key authentication
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── execute.py
│   │   ├── workflows.py
│   │   └── executions.py
│   └── services/
│       ├── __init__.py
│       ├── backend_client.py     # HTTP client to call Backend API
│       └── webhook_service.py
│
├── api/                          # Existing Backend API
│   └── ...
```

### Gateway App (`src/gateway/app.py`)

```python
"""Workflow Gateway - External API for multi-tenant workflow execution."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.gateway.routers import execute, workflows, executions
from src.gateway.middleware import tenant_rate_limit_key
from src.storage.database import init_database, close_database
from src.config.logging import get_logger

logger = get_logger(__name__)

limiter = Limiter(key_func=tenant_rate_limit_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Workflow Gateway...")
    await init_database()
    yield
    logger.info("Shutting down Workflow Gateway...")
    await close_database()


app = FastAPI(
    title="MagoneAI Workflow Gateway",
    description="External API for tenant workflow execution",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

app.include_router(execute.router, prefix="/api/v1", tags=["execute"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
app.include_router(executions.router, prefix="/api/v1", tags=["executions"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "workflow-gateway"}
```

### Backend Client (`src/gateway/services/backend_client.py`)

```python
"""HTTP client for calling Backend API."""
import os
from typing import Any, Dict, Optional

import httpx

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://api:8000")


class BackendClient:
    """Client for calling internal Backend API."""

    def __init__(self):
        self.base_url = BACKEND_API_URL
        self.timeout = httpx.Timeout(300.0)  # 5 min timeout

    async def execute_workflow(
        self,
        agent_id: str,
        user_input: str,
        workflow_definition: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call Backend API to execute workflow."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/workflow/execute",
                json={
                    "agent_id": agent_id,
                    "user_input": user_input,
                    "workflow_definition": workflow_definition,
                    "session_id": session_id,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status from Backend API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/workflow/status/{workflow_id}"
            )
            response.raise_for_status()
            return response.json()
```

### Gateway Execute Router (`src/gateway/routers/execute.py`)

```python
"""Workflow execution endpoints for Gateway."""
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gateway.auth import get_current_tenant
from src.gateway.services.backend_client import BackendClient
from src.storage.database import get_session
from src.storage.models import TenantModel, TenantWorkflowModel, WorkflowExecutionModel

router = APIRouter()
backend_client = BackendClient()


class ExecuteRequest(BaseModel):
    input: str = Field(...)
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class ExecuteResponse(BaseModel):
    execution_id: str
    status: str
    workflow_slug: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/execute/{workflow_slug}", response_model=ExecuteResponse)
async def execute_workflow(
    workflow_slug: str,
    request: ExecuteRequest,
    tenant: TenantModel = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_session),
):
    """Execute workflow via Backend API."""
    # Get tenant workflow
    result = await session.execute(
        select(TenantWorkflowModel).where(
            TenantWorkflowModel.tenant_id == tenant.id,
            TenantWorkflowModel.slug == workflow_slug,
            TenantWorkflowModel.is_active == True,
        )
    )
    tenant_workflow = result.scalar_one_or_none()

    if not tenant_workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_slug}' not found",
        )

    execution_id = f"exec_{uuid4().hex[:12]}"

    try:
        # Call Backend API
        backend_result = await backend_client.execute_workflow(
            agent_id=tenant_workflow.workflow_definition_id,
            user_input=request.input,
            workflow_definition={
                "steps": tenant_workflow.workflow_definition.steps,
                "entry_step": tenant_workflow.workflow_definition.entry_step,
                "context": {
                    **(tenant_workflow.workflow_definition.context or {}),
                    **(request.context or {}),
                },
            },
            session_id=request.session_id,
        )

        # Save execution record
        execution = WorkflowExecutionModel(
            id=execution_id,
            tenant_id=tenant.id,
            tenant_workflow_id=tenant_workflow.id,
            temporal_workflow_id=backend_result.get("workflow_id"),
            status="completed" if backend_result.get("success") else "failed",
            input={"user_input": request.input, "context": request.context},
            result=backend_result,
        )
        session.add(execution)
        await session.commit()

        return ExecuteResponse(
            execution_id=execution_id,
            status="completed" if backend_result.get("success") else "failed",
            workflow_slug=workflow_slug,
            result=backend_result,
        )

    except Exception as e:
        return ExecuteResponse(
            execution_id=execution_id,
            status="failed",
            workflow_slug=workflow_slug,
            error=str(e),
        )
```

---

## Docker Compose - Option 1

### Single Backend API (No Separate Gateway)

```yaml
version: "3.9"

services:
  # ==========================================================================
  # EDGE - Traefik
  # ==========================================================================
  traefik:
    image: traefik:v3.2
    container_name: magoneai-traefik
    restart: always
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--metrics.prometheus=true"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_letsencrypt:/letsencrypt
    networks:
      - magoneai-public
      - magoneai-internal

  # ==========================================================================
  # BACKEND API (Handles both internal and external endpoints)
  # ==========================================================================
  api:
    image: ${DOCKER_REGISTRY}/magoneai-api:${IMAGE_TAG:-latest}
    container_name: magoneai-api
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      temporal:
        condition: service_started
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      DATABASE_POOL_SIZE: 20
      TEMPORAL_HOST: temporal:7233
      TEMPORAL_TASK_QUEUE: agent-tasks
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      QDRANT_HOST: qdrant
      QDRANT_PORT: 6333
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
      SECRETS_ENCRYPTION_KEY: ${SECRETS_ENCRYPTION_KEY}
      CORS_ORIGINS: "https://${DOMAIN},https://magure.com"
    networks:
      - magoneai-public
      - magoneai-internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
    labels:
      - "traefik.enable=true"
      # External API route
      - "traefik.http.routers.api.rule=Host(`api.${DOMAIN}`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
      - "traefik.http.services.api.loadbalancer.server.port=8000"

  # ==========================================================================
  # TEMPORAL WORKERS
  # ==========================================================================
  worker:
    image: ${DOCKER_REGISTRY}/magoneai-worker:${IMAGE_TAG:-latest}
    restart: always
    depends_on:
      - temporal
      - postgres
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      TEMPORAL_HOST: temporal:7233
      TEMPORAL_TASK_QUEUE: agent-tasks
      QDRANT_HOST: qdrant
      QDRANT_PORT: 6333
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      SECRETS_ENCRYPTION_KEY: ${SECRETS_ENCRYPTION_KEY}
    networks:
      - magoneai-internal
    deploy:
      replicas: 3

  # ==========================================================================
  # ADMIN WEB UI
  # ==========================================================================
  web:
    image: ${DOCKER_REGISTRY}/magoneai-web:${IMAGE_TAG:-latest}
    container_name: magoneai-web
    restart: always
    environment:
      NEXT_PUBLIC_API_URL: https://api.${DOMAIN}
    networks:
      - magoneai-public
      - magoneai-internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`admin.${DOMAIN}`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.routers.web.middlewares=admin-auth"
      - "traefik.http.middlewares.admin-auth.basicauth.users=${ADMIN_AUTH}"
      - "traefik.http.services.web.loadbalancer.server.port=3000"

  # ==========================================================================
  # DATA LAYER
  # ==========================================================================
  postgres:
    image: postgres:16-alpine
    container_name: magoneai-postgres
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: magoneai-redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: magoneai-qdrant
    restart: always
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/readiness"]
      interval: 30s
      timeout: 10s
      retries: 3

  temporal:
    image: temporalio/auto-setup:1.22
    container_name: magoneai-temporal
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PWD=${DB_PASSWORD}
      - POSTGRES_SEEDS=postgres
    networks:
      - magoneai-internal

  temporal-ui:
    image: temporalio/ui:2.22.3
    container_name: magoneai-temporal-ui
    restart: always
    depends_on:
      - temporal
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
    networks:
      - magoneai-internal
      - magoneai-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.temporal.rule=Host(`temporal.${DOMAIN}`)"
      - "traefik.http.routers.temporal.entrypoints=websecure"
      - "traefik.http.routers.temporal.tls.certresolver=letsencrypt"
      - "traefik.http.routers.temporal.middlewares=admin-auth"
      - "traefik.http.services.temporal.loadbalancer.server.port=8080"

  # ==========================================================================
  # MONITORING
  # ==========================================================================
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: magoneai-prometheus
    restart: always
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=15d"
    networks:
      - magoneai-internal

  grafana:
    image: grafana/grafana:10.2.2
    container_name: magoneai-grafana
    restart: always
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_USER}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - magoneai-internal
      - magoneai-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.${DOMAIN}`)"
      - "traefik.http.routers.grafana.entrypoints=websecure"
      - "traefik.http.routers.grafana.tls.certresolver=letsencrypt"
      - "traefik.http.services.grafana.loadbalancer.server.port=3000"

networks:
  magoneai-public:
    driver: bridge
  magoneai-internal:
    driver: bridge
    internal: true

volumes:
  traefik_letsencrypt:
  postgres_data:
  redis_data:
  qdrant_storage:
  prometheus_data:
  grafana_data:
```

---

## Docker Compose - Option 2

### With Separate Gateway Service

```yaml
version: "3.9"

services:
  # ==========================================================================
  # EDGE - Traefik
  # ==========================================================================
  traefik:
    image: traefik:v3.2
    container_name: magoneai-traefik
    restart: always
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_letsencrypt:/letsencrypt
    networks:
      - magoneai-public
      - magoneai-internal

  # ==========================================================================
  # WORKFLOW GATEWAY - External API (:5005)
  # ==========================================================================
  gateway:
    image: ${DOCKER_REGISTRY}/magoneai-gateway:${IMAGE_TAG:-latest}
    container_name: magoneai-gateway
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      api:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      BACKEND_API_URL: http://api:8000
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      LOG_LEVEL: INFO
    networks:
      - magoneai-public
      - magoneai-internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gateway.rule=Host(`workflows.${DOMAIN}`)"
      - "traefik.http.routers.gateway.entrypoints=websecure"
      - "traefik.http.routers.gateway.tls.certresolver=letsencrypt"
      - "traefik.http.services.gateway.loadbalancer.server.port=5005"

  # ==========================================================================
  # BACKEND API (Internal only)
  # ==========================================================================
  api:
    image: ${DOCKER_REGISTRY}/magoneai-api:${IMAGE_TAG:-latest}
    container_name: magoneai-api
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      temporal:
        condition: service_started
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      DATABASE_POOL_SIZE: 20
      TEMPORAL_HOST: temporal:7233
      TEMPORAL_TASK_QUEUE: agent-tasks
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      QDRANT_HOST: qdrant
      QDRANT_PORT: 6333
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
      SECRETS_ENCRYPTION_KEY: ${SECRETS_ENCRYPTION_KEY}
    networks:
      - magoneai-internal  # Internal only, not exposed
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2

  # ==========================================================================
  # TEMPORAL WORKERS
  # ==========================================================================
  worker:
    image: ${DOCKER_REGISTRY}/magoneai-worker:${IMAGE_TAG:-latest}
    restart: always
    depends_on:
      - temporal
      - postgres
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      TEMPORAL_HOST: temporal:7233
      TEMPORAL_TASK_QUEUE: agent-tasks
      QDRANT_HOST: qdrant
      QDRANT_PORT: 6333
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      SECRETS_ENCRYPTION_KEY: ${SECRETS_ENCRYPTION_KEY}
    networks:
      - magoneai-internal
    deploy:
      replicas: 3

  # ==========================================================================
  # ADMIN WEB UI
  # ==========================================================================
  web:
    image: ${DOCKER_REGISTRY}/magoneai-web:${IMAGE_TAG:-latest}
    container_name: magoneai-web
    restart: always
    environment:
      NEXT_PUBLIC_API_URL: http://api:8000
    networks:
      - magoneai-public
      - magoneai-internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`admin.${DOMAIN}`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.routers.web.middlewares=admin-auth"
      - "traefik.http.middlewares.admin-auth.basicauth.users=${ADMIN_AUTH}"
      - "traefik.http.services.web.loadbalancer.server.port=3000"

  # ==========================================================================
  # DATA LAYER (same as Option 1)
  # ==========================================================================
  postgres:
    image: postgres:16-alpine
    container_name: magoneai-postgres
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: magoneai-redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - magoneai-internal
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: magoneai-qdrant
    restart: always
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - magoneai-internal

  temporal:
    image: temporalio/auto-setup:1.22
    container_name: magoneai-temporal
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PWD=${DB_PASSWORD}
      - POSTGRES_SEEDS=postgres
    networks:
      - magoneai-internal

  temporal-ui:
    image: temporalio/ui:2.22.3
    container_name: magoneai-temporal-ui
    restart: always
    depends_on:
      - temporal
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
    networks:
      - magoneai-internal
      - magoneai-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.temporal.rule=Host(`temporal.${DOMAIN}`)"
      - "traefik.http.routers.temporal.entrypoints=websecure"
      - "traefik.http.routers.temporal.tls.certresolver=letsencrypt"
      - "traefik.http.routers.temporal.middlewares=admin-auth"
      - "traefik.http.services.temporal.loadbalancer.server.port=8080"

  # ==========================================================================
  # MONITORING
  # ==========================================================================
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: magoneai-prometheus
    restart: always
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - magoneai-internal

  grafana:
    image: grafana/grafana:10.2.2
    container_name: magoneai-grafana
    restart: always
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_USER}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - magoneai-internal
      - magoneai-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.${DOMAIN}`)"
      - "traefik.http.routers.grafana.entrypoints=websecure"
      - "traefik.http.routers.grafana.tls.certresolver=letsencrypt"
      - "traefik.http.services.grafana.loadbalancer.server.port=3000"

networks:
  magoneai-public:
    driver: bridge
  magoneai-internal:
    driver: bridge
    internal: true

volumes:
  traefik_letsencrypt:
  postgres_data:
  redis_data:
  qdrant_storage:
  prometheus_data:
  grafana_data:
```

---

## Monitoring

### Prometheus Configuration

Create `deploy/monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "traefik"
    static_configs:
      - targets: ["traefik:8082"]

  - job_name: "api"
    static_configs:
      - targets: ["api:8000"]

  - job_name: "gateway"  # Only for Option 2
    static_configs:
      - targets: ["gateway:5005"]

  - job_name: "temporal"
    static_configs:
      - targets: ["temporal:9090"]
```

---

## Tenant Management

### Create Tenant Script

```bash
#!/bin/bash
# scripts/create_tenant.sh

TENANT_NAME=$1
TENANT_SLUG=$2

if [ -z "$TENANT_NAME" ] || [ -z "$TENANT_SLUG" ]; then
    echo "Usage: ./create_tenant.sh <name> <slug>"
    echo "Example: ./create_tenant.sh 'Magure Real Estate' magure"
    exit 1
fi

API_KEY="${TENANT_SLUG}_live_$(openssl rand -hex 24)"

echo "Creating tenant: $TENANT_NAME ($TENANT_SLUG)"
echo ""
echo "API Key (save this - shown only once):"
echo "$API_KEY"
echo ""

docker exec -i magoneai-postgres psql -U magoneai -d magoneai << EOF
INSERT INTO tenants (id, name, slug, api_key_hash, api_key_prefix, is_active)
VALUES (
    '$(uuidgen | tr '[:upper:]' '[:lower:]')',
    '$TENANT_NAME',
    '$TENANT_SLUG',
    encode(sha256('$API_KEY'::bytea), 'hex'),
    '${TENANT_SLUG}_live_$(echo $API_KEY | cut -c1-20)...',
    true
);
EOF

echo "Tenant created!"
```

### Assign Workflow to Tenant

```bash
#!/bin/bash
# scripts/assign_workflow.sh

TENANT_SLUG=$1
WORKFLOW_DEF_ID=$2
WORKFLOW_SLUG=$3
WORKFLOW_NAME=$4

docker exec -i magoneai-postgres psql -U magoneai -d magoneai << EOF
INSERT INTO tenant_workflows (id, tenant_id, workflow_definition_id, slug, name, is_active)
SELECT
    '$(uuidgen | tr '[:upper:]' '[:lower:]')',
    t.id,
    '$WORKFLOW_DEF_ID',
    '$WORKFLOW_SLUG',
    '$WORKFLOW_NAME',
    true
FROM tenants t
WHERE t.slug = '$TENANT_SLUG';
EOF

echo "Workflow '$WORKFLOW_SLUG' assigned to '$TENANT_SLUG'"
```

---

## Frontend Integration

### React Hook

```typescript
// hooks/useMagoneWorkflow.ts
import { useState, useCallback } from 'react';

interface WorkflowResult {
  execution_id: string;
  status: 'completed' | 'failed' | 'running';
  result?: any;
  error?: string;
}

export function useMagoneWorkflow(apiKey: string, baseUrl: string) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkflowResult | null>(null);

  const execute = useCallback(async (
    workflowSlug: string,
    input: string,
    context?: Record<string, any>
  ) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${baseUrl}/api/v1/external/execute/${workflowSlug}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey,
          },
          body: JSON.stringify({ input, context }),
        }
      );
      const data = await response.json();
      setResult(data);
      return data;
    } finally {
      setLoading(false);
    }
  }, [apiKey, baseUrl]);

  return { execute, loading, result };
}
```

### Usage

```tsx
const { execute, loading, result } = useMagoneWorkflow(
  'magure_live_abc123...',
  'https://api.magoneai.com'
);

const handleQuery = async () => {
  await execute('kpi-sales', 'Show Q4 sales KPIs', { region: 'dubai' });
};
```

---

## Summary

| Aspect | Option 1 | Option 2 |
|--------|----------|----------|
| **URL** | `api.domain.com/api/v1/external/...` | `workflows.domain.com/api/v1/...` |
| **Services** | 1 (Backend API) | 2 (Gateway + Backend) |
| **Dockerfile** | Existing | + New Gateway Dockerfile |
| **Complexity** | Lower | Higher |
| **Recommended** | Most cases | Large scale, strict separation |

---

*Choose Option 1 for simplicity. Choose Option 2 if you need strict separation between external and internal APIs.*

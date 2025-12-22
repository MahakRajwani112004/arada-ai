# Multi-Tenant Architecture Plan for MagOneAI

> **Status:** Planned (not yet implemented)
> **Created:** 2025-12-21

## Overview

Add multi-tenant support with:
1. **Org → Workspaces → Users** hierarchy
2. **Per-user MCP credentials** for shared templates
3. **Visibility model** (private, workspace, org)

---

## Phase 1: Database Models

### New Tables

**File:** `src/storage/models.py`

| Table | Purpose |
|-------|---------|
| `organizations` | Top-level tenant (id, name, slug, settings) |
| `workspaces` | Teams within org (id, org_id, name, slug) |
| `users` | User accounts (id, email, name, auth_provider) |
| `org_memberships` | User ↔ Org with role (owner, admin, member) |
| `workspace_memberships` | User ↔ Workspace with role |
| `user_mcp_credentials` | Per-user credentials for MCP servers |

### Modified Tables

**agents** - Add columns:
- `org_id` (FK to organizations)
- `workspace_id` (FK to workspaces, nullable)
- `owner_id` (FK to users)
- `visibility` (private/workspace/org)

**mcp_servers** - Add columns:
- `org_id`, `workspace_id`, `owner_id`, `visibility`
- `credential_mode` (shared/per_user)
- `shared_secret_ref` (for shared mode)

---

## Phase 2: Credential Resolution

### New File: `src/mcp/credential_resolver.py`

```python
@dataclass
class ExecutionContext:
    user_id: str
    org_id: str
    workspace_id: Optional[str] = None

class MCPCredentialResolver:
    async def resolve_credentials(mcp_server_id, context) -> Dict[str, str]:
        # 1. If credential_mode == "shared": use shared_secret_ref
        # 2. If credential_mode == "per_user": lookup user_mcp_credentials
        # 3. Raise error if user has no credentials

    async def store_user_credentials(mcp_server_id, user_id, credentials):
        # Store in vault at: mcp/user/{user_id}/{mcp_server_id}
```

---

## Phase 3: Workflow Changes

### Modified: `src/workflows/agent_workflow.py`

**AgentWorkflowInput** - Add fields:
```python
user_id: str = ""
org_id: str = ""
workspace_id: Optional[str] = None
enabled_mcp_servers: List[str] = []      # MCP server IDs
enabled_builtin_tools: List[str] = []    # Non-MCP tools
```

### New Activity: `src/activities/mcp_tool_activity.py`

```python
@activity.defn
async def execute_mcp_tool(input: MCPToolExecutionInput):
    # 1. Resolve credentials via MCPCredentialResolver
    # 2. Create ephemeral MCP client with user's credentials
    # 3. Execute tool
    # 4. Disconnect
```

---

## Phase 4: API Changes

### New File: `src/api/auth.py`

```python
@dataclass
class AuthContext:
    user_id: str
    org_id: str
    workspace_id: Optional[str]
    org_role: str
    workspace_role: Optional[str]

async def get_current_user(request, session) -> AuthContext:
    # Extract from headers (X-User-Id, X-Org-Id, X-Workspace-Id)
    # Validate memberships
```

### New File: `src/storage/multi_tenant_repository.py`

```python
class MultiTenantAgentRepository:
    async def list_visible() -> List[AgentConfig]:
        # Filter by visibility rules:
        # - private: owner_id == user_id
        # - workspace: workspace_id == user's workspace
        # - org: org_id == user's org
```

### New Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /mcp/servers/{id}/credentials` | User configures their credentials |
| `GET /mcp/servers/{id}/credentials/status` | Check if user has credentials |

---

## Phase 5: Agent Config Changes

### Modified: `src/models/agent_config.py`

```python
class MCPBinding(BaseModel):
    mcp_server_id: str
    enabled_tools: List[str] = []  # Empty = all tools
    requires_confirmation: bool = False

class AgentConfig(BaseModel):
    # NEW - separate builtin from MCP
    builtin_tools: List[ToolConfig] = []
    mcp_bindings: List[MCPBinding] = []

    # DEPRECATED
    tools: List[ToolConfig] = []  # For migration
```

---

## Implementation Order

1. **Database migrations** (non-breaking)
   - Create new tables
   - Add nullable columns to existing tables
   - Create default org/workspace for migration

2. **Core multi-tenant models**
   - `src/storage/models.py` - Add all new models
   - `src/models/enums.py` - Add Visibility enum

3. **Credential resolver**
   - `src/mcp/credential_resolver.py`
   - `src/activities/mcp_tool_activity.py`

4. **Auth layer**
   - `src/api/auth.py`
   - `src/storage/multi_tenant_repository.py`

5. **Workflow updates**
   - Modify `AgentWorkflowInput`
   - Update `_handle_tool` and `_handle_full`

6. **API updates**
   - Add auth dependency to all routes
   - Add user credential endpoints
   - Update workflow execution to pass context

---

## Critical Files to Modify

| File | Changes |
|------|---------|
| `src/storage/models.py` | Add 6 new models, modify 2 existing |
| `src/models/agent_config.py` | Add MCPBinding, split tools |
| `src/models/enums.py` | Add Visibility enum |
| `src/workflows/agent_workflow.py` | Add user context, modify tool execution |
| `src/activities/tool_activity.py` | Split MCP and builtin tool execution |
| `src/api/routers/workflow.py` | Pass auth context to workflows |
| `src/api/routers/agents.py` | Add visibility filtering |
| `src/api/routers/mcp.py` | Add user credential endpoints |
| `src/mcp/repository.py` | Update for multi-tenant |

## New Files to Create

| File | Purpose |
|------|---------|
| `src/api/auth.py` | Auth context and middleware |
| `src/mcp/credential_resolver.py` | Runtime credential resolution |
| `src/activities/mcp_tool_activity.py` | MCP tool execution with user context |
| `src/storage/multi_tenant_repository.py` | Visibility-aware queries |
| `alembic/versions/xxx_add_multitenancy.py` | Database migration |

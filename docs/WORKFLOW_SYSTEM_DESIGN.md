# Workflow System - Persistence, Templates & AI Generation

## Build Order Recommendation

### API First (Recommended)

**Why API before UI:**

1. **Contract-Driven Development** - UI team knows exactly what data they'll get
2. **Testable Backend** - Can verify logic with scripts before UI complicates debugging
3. **Parallel Work** - Once API is stable, UI can be built independently
4. **Iterate Faster** - API changes are cheaper than UI changes

**Suggested Order:**
```
Week 1: API (MVP)
├── Day 1-2: Workflow persistence (models, repository, CRUD)
├── Day 2-3: Execution history + resource discovery
└── Day 3-4: AI generation endpoints

Week 2: UI
├── Day 1-2: Workflow list/detail pages
├── Day 2-3: Create/edit workflow form
└── Day 3-4: AI generation UI + execution viewer
```

---

## Overview

Design a comprehensive workflow system that includes:
1. **Workflow Persistence** - Store workflows independently in database
2. **Workflow Templates** - Reusable templates that can be copied and customized
3. **AI-Powered Workflow Generation** - Generate complete workflows (agents + MCPs + steps) from natural language prompts
4. **Custom Workflow Builder** - Create workflows from existing agents/MCPs (drag-and-drop ready)

## Workflow Creation Sources

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW CREATION METHODS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐ │
│  │  From Scratch  │  │  From Template │  │   AI Generated             │ │
│  │  (Drag & Drop) │  │  (Copy & Edit) │  │   (Prompt → Workflow)      │ │
│  └───────┬────────┘  └───────┬────────┘  └─────────────┬──────────────┘ │
│          │                   │                         │                 │
│          │                   │                         │                 │
│          ▼                   ▼                         ▼                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     WORKFLOW DEFINITION                            │  │
│  │  - References EXISTING agents (by ID)                              │  │
│  │  - References EXISTING MCP tools (by ID)                           │  │
│  │  - OR creates NEW agents inline                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW SYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │  Workflows   │    │  Templates   │    │   AI Workflow Generator  │  │
│  │  (User's)    │◄───│  (System)    │    │   (Prompt → Workflow)    │  │
│  └──────┬───────┘    └──────────────┘    └────────────┬─────────────┘  │
│         │                                              │                 │
│         │  references                                  │ creates         │
│         ▼                                              ▼                 │
│  ┌──────────────┐                           ┌──────────────────────┐   │
│  │   Agents     │◄──────────────────────────│  Generated Agents    │   │
│  └──────────────┘                           └──────────────────────┘   │
│         │                                              │                 │
│         │  uses                                        │ suggests        │
│         ▼                                              ▼                 │
│  ┌──────────────┐                           ┌──────────────────────┐   │
│  │ MCP Servers  │◄──────────────────────────│  Suggested MCPs      │   │
│  └──────────────┘                           └──────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Workflow Persistence

### Database Model

**File:** `src/storage/models.py`

```python
class WorkflowModel(Base):
    __tablename__ = "workflows"

    # Identity
    id: str (PK, pattern: [a-zA-Z][a-zA-Z0-9_-]{0,99})
    name: str (indexed, max 200)
    description: str (max 1000)

    # Categorization
    category: str (indexed) # e.g., "customer-support", "data-processing"
    tags: List[str] (JSONB)

    # Template relationship
    is_template: bool (indexed, default=False)
    source_template_id: Optional[str] (FK to workflows.id)

    # The actual definition
    definition_json: Dict (JSONB) # Full WorkflowDefinition

    # Version tracking
    version: int (default=1)

    # Status
    is_active: bool (indexed, default=True)
    is_published: bool (default=False) # For templates

    # Metadata
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### Execution History Model

```python
class WorkflowExecutionModel(Base):
    __tablename__ = "workflow_executions"

    id: str (PK)                    # execution-{uuid}
    workflow_id: str (FK, indexed)  # Reference to workflow
    temporal_workflow_id: str       # Temporal's workflow ID

    # Execution details
    status: str (indexed)           # RUNNING, COMPLETED, FAILED, CANCELLED
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]

    # Input/Output
    input_json: Dict (JSONB)        # User input + context
    output_json: Optional[Dict]     # Final result
    error: Optional[str]

    # Step tracking
    steps_executed: List[str] (JSONB)
    step_results: Dict (JSONB)      # All step outputs

    # Metadata
    triggered_by: Optional[str]     # user, api, schedule
    created_at: datetime
```

### Repository Interface

**File:** `src/storage/workflow_repository.py`

```python
class WorkflowRepository:
    # Core CRUD
    async def save(workflow: WorkflowDefinition, metadata: WorkflowMetadata) -> str
    async def get(workflow_id: str) -> Optional[WorkflowWithMetadata]
    async def list(filters: WorkflowFilters) -> List[WorkflowSummary]
    async def delete(workflow_id: str) -> bool
    async def exists(workflow_id: str) -> bool

    # Template operations
    async def list_templates(category: Optional[str]) -> List[WorkflowSummary]
    async def copy_template(template_id: str, new_id: str, new_name: str) -> str

    # Version operations
    async def increment_version(workflow_id: str) -> int

    # Execution tracking
    async def create_execution(workflow_id: str, input_data: Dict) -> str
    async def update_execution(execution_id: str, status: str, result: Optional[Dict]) -> None
    async def get_executions(workflow_id: str) -> List[WorkflowExecution]
    async def get_execution(execution_id: str) -> Optional[WorkflowExecution]
```

---

## Part 2: AI-Powered Workflow Generation

### Generation Flow

The AI generator receives **existing resources** to reuse when possible:

```python
GENERATE_WORKFLOW_PROMPT = """You are an AI workflow architect. Given a user's description,
design a complete workflow system.

## EXISTING RESOURCES (PREFER REUSING THESE)

### Existing Agents:
{existing_agents_json}

### Existing MCP Servers (already configured):
{existing_mcps_json}

## YOUR TASK

1. PREFER using existing agents/MCPs when they fit the requirement
2. Only suggest NEW agents if existing ones don't cover the need
3. Only suggest NEW MCPs if they're not already configured

## OUTPUT FORMAT

You must output a JSON object with:

1. "workflow": A workflow definition with:
   - id: unique workflow identifier
   - name: descriptive name
   - description: what the workflow does
   - steps: array of workflow steps (use existing agent IDs when possible!)
   - entry_step: first step ID

2. "agents_to_create": Array of NEW agent configurations (ONLY if needed)
3. "existing_agents_used": List of existing agent IDs used in the workflow
4. "mcps_suggested": Array of NEW MCP server suggestions (ONLY if not already configured)
5. "existing_mcps_used": List of existing MCP IDs used in the workflow
6. "explanation": Brief explanation of the workflow design

Step types available:
- "agent": Execute an agent (existing or new)
- "tool": Execute an MCP tool directly (e.g., "gmail-server:send_email")
- "parallel": Execute multiple agents concurrently
- "conditional": Route based on conditions
- "loop": Iterate until condition met

Template variables: Use ${user_input}, ${steps.STEP_ID.output}, ${context.KEY}

Respond ONLY with valid JSON."""
```

---

## Part 3: Resource Discovery (for Drag & Drop UI)

### APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/workflows/resources/agents` | List available agents for steps |
| `GET` | `/workflows/resources/mcps` | List available MCP servers + tools |
| `GET` | `/workflows/resources/tools` | List all available tools (native + MCP) |

---

## MVP vs Future Roadmap

### CURRENT PLAN (MVP) - Building Now

**Scope:** Core workflow system with AI generation

| Category | Feature | Status |
|----------|---------|--------|
| Persistence | Workflow CRUD (create, list, get, update, delete) | MVP |
| Persistence | Execution history tracking | MVP |
| Discovery | List available agents | MVP |
| Discovery | List available MCPs + tools | MVP |
| AI | Generate workflow from prompt | MVP |
| AI | Apply generated workflow (create all) | MVP |

**API Endpoints (12 total):**
```
POST   /api/v1/workflows                    # Create workflow
GET    /api/v1/workflows                    # List workflows
GET    /api/v1/workflows/{id}               # Get workflow
PUT    /api/v1/workflows/{id}               # Update workflow
DELETE /api/v1/workflows/{id}               # Delete workflow
GET    /api/v1/workflows/{id}/executions    # List executions
GET    /api/v1/workflows/executions/{id}    # Get execution details
GET    /api/v1/workflows/resources/agents   # List agents for palette
GET    /api/v1/workflows/resources/mcps     # List MCPs + tools
GET    /api/v1/workflows/resources/tools    # List all tools
POST   /api/v1/workflows/generate           # AI generate workflow
POST   /api/v1/workflows/generate/apply     # Apply generated workflow
```

---

### FUTURE PLAN - Add When Building UI

**Phase 2: Visual Workflow Builder**

| Category | Feature | Trigger |
|----------|---------|---------|
| Builder | Add/update/delete/reorder steps | When drag-and-drop UI starts |
| Builder | Connect steps (branching) | When drag-and-drop UI starts |
| Canvas | Get workflow as nodes + edges | When visual editor starts |
| Canvas | Update node positions | When visual editor starts |

**Future Endpoints (+11):**
```
POST   /api/v1/workflows/{id}/steps                    # Add step
PUT    /api/v1/workflows/{id}/steps/{step_id}          # Update step
DELETE /api/v1/workflows/{id}/steps/{step_id}          # Delete step
POST   /api/v1/workflows/{id}/steps/reorder            # Reorder
POST   /api/v1/workflows/{id}/steps/{id}/connect       # Connect
GET    /api/v1/workflows/{id}/canvas                   # Get canvas
PUT    /api/v1/workflows/{id}/canvas                   # Update canvas
PUT    /api/v1/workflows/{id}/nodes/{id}/position      # Position
POST   /api/v1/workflows/{id}/copy                     # Copy workflow
POST   /api/v1/workflows/{id}/validate                 # Validate
GET    /api/v1/workflows/{id}/stats                    # Statistics
```

**Phase 3: Templates**

```
GET    /api/v1/workflows/templates                     # List templates
GET    /api/v1/workflows/templates/{id}                # Get template
POST   /api/v1/workflows/templates/{id}/instantiate    # Create from template
```

---

## Files to Create/Modify (MVP)

### New Files
| File | Purpose |
|------|---------|
| `src/storage/workflow_repository.py` | Repository for workflows + executions |
| `src/api/routers/workflows.py` | CRUD + resource discovery + AI generation |
| `src/api/schemas/workflows.py` | Request/response Pydantic models |
| `src/workflows/generator.py` | AI workflow generation with GPT-4o |
| `tests/test_workflow_repository.py` | Repository unit tests |
| `scripts/test_workflow_generation.py` | Integration test script |

### Modified Files
| File | Changes |
|------|---------|
| `src/storage/models.py` | Add `WorkflowModel`, `WorkflowExecutionModel` |
| `src/storage/__init__.py` | Export `WorkflowRepository` |
| `src/api/dependencies.py` | Add `get_workflow_repository` |
| `src/api/app.py` | Register `/workflows` router |
| `src/api/routers/workflow.py` | Save execution history on execute |

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Template Storage | JSON files only | Simple, version-controlled, no DB seeding needed |
| Versioning | Version number only | Simpler, covers most use cases |
| AI Model | GPT-4o | Best quality for complex workflow design |
| Execution History | Database | Enable analytics and debugging |

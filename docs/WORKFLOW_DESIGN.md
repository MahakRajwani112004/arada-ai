# Multi-Agent Workflow Design

## Overview

This document outlines the design for multi-agent workflow support in Magure AI Platform.

---

## Current State

### What We Have

```
POST /api/v1/workflow/execute
├── Takes: agent_id, user_input
├── Runs: Single agent via Temporal
└── Returns: Agent response
```

**Limitation:** Only executes ONE agent per request. No saved workflow definitions.

---

## Future State

### What We Need

```
┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   User creates workflow definition (UI/API)                     │
│                    │                                            │
│                    ▼                                            │
│   ┌─────────────────────────────────────────┐                   │
│   │         Workflow Definition             │                   │
│   │   - Name, Description                   │                   │
│   │   - Steps (agents in sequence/parallel) │                   │
│   │   - Trigger (manual/scheduled/event)    │                   │
│   └─────────────────────────────────────────┘                   │
│                    │                                            │
│                    ▼                                            │
│   ┌─────────────────────────────────────────┐                   │
│   │         Temporal Workflow               │                   │
│   │   - Orchestrates agent execution        │                   │
│   │   - Handles sequential/parallel         │                   │
│   │   - Manages state between steps         │                   │
│   └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Workflow Types

### 1. Single Agent
```
User Input → Agent A → Output
```
- Existing behavior
- One agent handles everything

### 2. Sequential (Pipeline)
```
User Input → Agent A → Agent B → Agent C → Output
                 │          │
                 └──────────┴── Output passes to next
```
- Agents run in order
- Each agent receives previous agent's output
- Use case: Data gathering → Processing → Summary

### 3. Parallel (Fan-out/Fan-in)
```
              ┌→ Agent A ─┐
User Input ───┼→ Agent B ─┼→ Merge → Output
              └→ Agent C ─┘
```
- Agents run simultaneously
- Results merged at the end
- Use case: Gather from multiple sources at once

### 4. Conditional (Routed)
```
                    ┌→ Agent A (if calendar)
User Input → Router ┼→ Agent B (if email)
                    └→ Agent C (default)
```
- Dynamic routing based on input
- Already supported via RoutedAgent

### 5. Hybrid (Complex)
```
                    ┌→ Agent A ─┐
User Input → Agent X ┼→ Agent B ─┼→ Agent Y → Output
                    └→ Agent C ─┘
```
- Combination of sequential and parallel
- For complex multi-stage workflows

---

## Data Models

### WorkflowDefinition

```python
class WorkflowType(str, Enum):
    SINGLE = "single"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class TriggerType(str, Enum):
    MANUAL = "manual"        # API/Chat triggered
    SCHEDULED = "scheduled"  # Cron-based
    EVENT = "event"          # MCP event (calendar end, email received)
    WEBHOOK = "webhook"      # External webhook


class WorkflowStep(BaseModel):
    """A single step in the workflow."""

    step_id: str                      # "step_1"
    agent_id: str                     # "meeting-scheduler"
    input_mapping: Optional[str]      # "{{previous.output}}" or "{{user_input}}"
    timeout_seconds: int = 300        # 5 min default
    retry_count: int = 3

    # For conditional steps
    condition: Optional[str]          # "{{previous.output.type}} == 'calendar'"


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""

    id: str                           # "wf_daily_briefing"
    name: str                         # "Daily Briefing"
    description: str
    workflow_type: WorkflowType

    # Steps configuration
    steps: List[WorkflowStep]         # Ordered list of steps
    parallel_groups: Optional[List[List[str]]]  # Groups of step_ids to run in parallel

    # Merge configuration (for parallel)
    merge_strategy: str = "concatenate"  # concatenate, summary_agent, template
    merge_agent_id: Optional[str]     # Agent to summarize parallel results
    merge_template: Optional[str]     # Custom merge template

    # Trigger configuration
    trigger_type: TriggerType
    trigger_config: Optional[Dict]    # Cron expression, event filter, etc.

    # Metadata
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class ScheduledTriggerConfig(BaseModel):
    """Configuration for scheduled triggers."""

    cron_expression: str              # "0 8 * * 1-5" (8am weekdays)
    timezone: str = "UTC"
    skip_weekends: bool = False
    skip_holidays: bool = False


class EventTriggerConfig(BaseModel):
    """Configuration for event-based triggers."""

    mcp_server_id: str                # "srv_calendar_123"
    event_type: str                   # "event_ended", "email_received"
    filter: Optional[Dict]            # {"attendees_min": 3}


class WebhookTriggerConfig(BaseModel):
    """Configuration for webhook triggers."""

    webhook_id: str                   # Auto-generated
    webhook_url: str                  # Full URL
    secret: str                       # For validation
```

### Database Model

```python
class WorkflowModel(Base):
    """SQLAlchemy model for workflows."""

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    workflow_type: Mapped[str] = mapped_column(String(50))

    # JSON columns for complex data
    steps: Mapped[dict] = mapped_column(JSON)
    parallel_groups: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    merge_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    trigger_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    trigger_type: Mapped[str] = mapped_column(String(50), default="manual")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow)


class WorkflowRunModel(Base):
    """SQLAlchemy model for workflow execution history."""

    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(100), ForeignKey("workflows.id"))
    temporal_workflow_id: Mapped[str] = mapped_column(String(200))

    status: Mapped[str] = mapped_column(String(50))  # pending, running, completed, failed
    trigger_type: Mapped[str] = mapped_column(String(50))

    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
```

---

## API Design

### Workflow CRUD

```yaml
# List workflows
GET /api/v1/workflows
Response:
  workflows: List[WorkflowSummary]
  total: int

# Create workflow
POST /api/v1/workflows
Request:
  name: str
  description: str
  workflow_type: "single" | "sequential" | "parallel" | "conditional"
  steps: List[WorkflowStep]
  parallel_groups?: List[List[str]]  # For parallel
  merge_strategy?: str
  trigger_type: "manual" | "scheduled" | "event" | "webhook"
  trigger_config?: Dict
Response:
  id: str
  name: str
  status: str
  webhook_url?: str  # If webhook trigger

# Get workflow details
GET /api/v1/workflows/{workflow_id}
Response:
  id: str
  name: str
  description: str
  workflow_type: str
  steps: List[WorkflowStep]
  trigger_type: str
  trigger_config: Dict
  is_active: bool
  stats:
    total_runs: int
    success_rate: float
    avg_duration_ms: int

# Update workflow
PATCH /api/v1/workflows/{workflow_id}
Request:
  name?: str
  description?: str
  steps?: List[WorkflowStep]
  trigger_config?: Dict
  is_active?: bool

# Delete workflow
DELETE /api/v1/workflows/{workflow_id}
Response: 204 No Content
```

### Workflow Execution

```yaml
# Run workflow manually
POST /api/v1/workflows/{workflow_id}/run
Request:
  user_input: str
  variables?: Dict[str, Any]  # Custom variables to pass
Response:
  run_id: str
  workflow_id: str
  temporal_workflow_id: str
  status: "pending" | "running"

# Get run status
GET /api/v1/workflows/runs/{run_id}
Response:
  run_id: str
  workflow_id: str
  status: "pending" | "running" | "completed" | "failed"
  current_step?: str
  steps_completed: List[StepResult]
  output?: Any
  error?: str
  started_at: datetime
  completed_at?: datetime
  duration_ms?: int

# List workflow runs
GET /api/v1/workflows/{workflow_id}/runs
Query:
  status?: str
  limit?: int
  offset?: int
Response:
  runs: List[WorkflowRunSummary]
  total: int

# Cancel running workflow
POST /api/v1/workflows/runs/{run_id}/cancel
Response:
  run_id: str
  status: "cancelled"
```

### Trigger Management

```yaml
# Update trigger
PATCH /api/v1/workflows/{workflow_id}/trigger
Request:
  trigger_type: str
  trigger_config: Dict
Response:
  workflow_id: str
  trigger_type: str
  trigger_config: Dict
  next_run?: datetime  # For scheduled

# Pause/Resume scheduled workflow
POST /api/v1/workflows/{workflow_id}/pause
POST /api/v1/workflows/{workflow_id}/resume

# Webhook endpoint (auto-generated)
POST /api/v1/webhooks/{webhook_id}
Headers:
  X-Webhook-Secret: str
Request:
  <any payload>
Response:
  run_id: str
```

---

## Temporal Workflow Implementation

### Sequential Workflow

```python
@workflow.defn
class SequentialWorkflow:
    """Execute agents in sequence, passing output forward."""

    @workflow.run
    async def run(self, input: SequentialWorkflowInput) -> WorkflowResult:
        results = []
        current_input = input.user_input

        for step in input.steps:
            # Execute each agent
            step_result = await workflow.execute_activity(
                execute_agent_step,
                ExecuteStepInput(
                    agent_id=step.agent_id,
                    user_input=current_input,
                    context=results,  # Previous results for context
                ),
                start_to_close_timeout=timedelta(seconds=step.timeout_seconds),
                retry_policy=RetryPolicy(maximum_attempts=step.retry_count),
            )

            results.append(step_result)

            # Pass output to next step
            current_input = step_result.output

        return WorkflowResult(
            success=True,
            steps=results,
            final_output=results[-1].output if results else None,
        )
```

### Parallel Workflow

```python
@workflow.defn
class ParallelWorkflow:
    """Execute agents in parallel, merge results."""

    @workflow.run
    async def run(self, input: ParallelWorkflowInput) -> WorkflowResult:
        # Start all agents in parallel
        tasks = []
        for step in input.steps:
            task = workflow.execute_activity(
                execute_agent_step,
                ExecuteStepInput(
                    agent_id=step.agent_id,
                    user_input=input.user_input,
                ),
                start_to_close_timeout=timedelta(seconds=step.timeout_seconds),
            )
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle failures
        successful_results = []
        failed_steps = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_steps.append({"step": input.steps[i].step_id, "error": str(result)})
            else:
                successful_results.append(result)

        # Merge results
        if input.merge_strategy == "concatenate":
            merged = self._concatenate_results(successful_results)
        elif input.merge_strategy == "summary_agent":
            merged = await workflow.execute_activity(
                execute_agent_step,
                ExecuteStepInput(
                    agent_id=input.merge_agent_id,
                    user_input=f"Summarize these results:\n{successful_results}",
                ),
                start_to_close_timeout=timedelta(seconds=60),
            )
        else:
            merged = self._apply_template(input.merge_template, successful_results)

        return WorkflowResult(
            success=len(failed_steps) == 0,
            steps=successful_results,
            failed_steps=failed_steps,
            final_output=merged,
        )

    def _concatenate_results(self, results: List) -> str:
        return "\n\n---\n\n".join([r.output for r in results])
```

### Hybrid Workflow

```python
@workflow.defn
class HybridWorkflow:
    """Complex workflow with sequential and parallel sections."""

    @workflow.run
    async def run(self, input: HybridWorkflowInput) -> WorkflowResult:
        all_results = []
        current_input = input.user_input

        for section in input.sections:
            if section.type == "sequential":
                # Run steps in sequence
                for step in section.steps:
                    result = await self._execute_step(step, current_input)
                    all_results.append(result)
                    current_input = result.output

            elif section.type == "parallel":
                # Run steps in parallel
                tasks = [self._execute_step(step, current_input) for step in section.steps]
                results = await asyncio.gather(*tasks)
                all_results.extend(results)

                # Merge parallel results
                current_input = self._merge_results(results, section.merge_strategy)

        return WorkflowResult(
            success=True,
            steps=all_results,
            final_output=current_input,
        )
```

---

## Trigger Implementation

### Scheduled Triggers (Temporal Schedules)

```python
async def create_scheduled_workflow(
    workflow_id: str,
    cron_expression: str,
    timezone: str,
) -> str:
    """Create a Temporal schedule for the workflow."""

    client = await get_temporal_client()

    schedule = await client.create_schedule(
        id=f"schedule-{workflow_id}",
        schedule=Schedule(
            action=ScheduleActionStartWorkflow(
                workflow=ScheduledWorkflowRunner.run,
                args=[ScheduledInput(workflow_id=workflow_id)],
                id=f"scheduled-{workflow_id}-{{{{.ScheduledTime}}}}",
                task_queue=TASK_QUEUE,
            ),
            spec=ScheduleSpec(
                cron_expressions=[cron_expression],
                timezone=timezone,
            ),
        ),
    )

    return schedule.id


@workflow.defn
class ScheduledWorkflowRunner:
    """Runner for scheduled workflows."""

    @workflow.run
    async def run(self, input: ScheduledInput) -> WorkflowResult:
        # Load workflow definition
        definition = await workflow.execute_activity(
            load_workflow_definition,
            input.workflow_id,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Execute based on type
        if definition.workflow_type == "sequential":
            return await SequentialWorkflow().run(...)
        elif definition.workflow_type == "parallel":
            return await ParallelWorkflow().run(...)
```

### Event Triggers (MCP Events)

```python
# Future: MCP servers emit events to a message queue
# Worker listens and triggers workflows

class MCPEventListener:
    """Listen for MCP events and trigger workflows."""

    async def on_event(self, event: MCPEvent):
        # Find workflows subscribed to this event
        workflows = await self.repository.find_by_trigger(
            trigger_type="event",
            mcp_server_id=event.server_id,
            event_type=event.type,
        )

        for workflow in workflows:
            # Check filter
            if self._matches_filter(event, workflow.trigger_config.filter):
                await self._trigger_workflow(workflow.id, event.data)
```

### Webhook Triggers

```python
@router.post("/webhooks/{webhook_id}")
async def handle_webhook(
    webhook_id: str,
    request: Request,
    x_webhook_secret: str = Header(...),
):
    """Handle incoming webhook and trigger workflow."""

    # Validate webhook
    webhook = await repository.get_webhook(webhook_id)
    if not webhook or webhook.secret != x_webhook_secret:
        raise HTTPException(status_code=401)

    # Get payload
    payload = await request.json()

    # Trigger workflow
    run_id = await trigger_workflow(
        workflow_id=webhook.workflow_id,
        trigger_type="webhook",
        input_data=payload,
    )

    return {"run_id": run_id}
```

---

## File Structure

```
src/
├── workflows/
│   ├── __init__.py
│   ├── agent_workflow.py       # Existing single-agent
│   ├── sequential_workflow.py  # NEW: Sequential multi-agent
│   ├── parallel_workflow.py    # NEW: Parallel multi-agent
│   ├── hybrid_workflow.py      # NEW: Complex hybrid
│   ├── scheduled_runner.py     # NEW: Scheduled workflow runner
│   └── models.py               # NEW: Workflow dataclasses
│
├── api/
│   ├── routers/
│   │   ├── workflow.py         # UPDATE: Add new endpoints
│   │   └── webhooks.py         # NEW: Webhook handlers
│   └── schemas/
│       └── workflow.py         # UPDATE: Add new schemas
│
├── storage/
│   └── models.py               # UPDATE: Add WorkflowModel
│
└── triggers/
    ├── __init__.py             # NEW
    ├── scheduler.py            # NEW: Temporal schedules
    ├── event_listener.py       # NEW: MCP event handling
    └── webhook_manager.py      # NEW: Webhook management
```

---

## Implementation Phases

### Phase 1: Foundation (After Agents + MCP stable)
1. Add `WorkflowModel` to database
2. Create Workflow CRUD API endpoints
3. Create workflow repository

### Phase 2: Sequential Workflows
1. Implement `SequentialWorkflow` in Temporal
2. Add `/workflows/{id}/run` endpoint
3. Add run history tracking

### Phase 3: Parallel Workflows
1. Implement `ParallelWorkflow` in Temporal
2. Add merge strategies
3. Handle partial failures

### Phase 4: Triggers
1. Implement scheduled triggers (Temporal Schedules)
2. Add webhook triggers
3. Event triggers (requires MCP event system)

### Phase 5: UI Integration
1. Workflow builder UI
2. Run history/monitoring
3. Trigger configuration UI

---

## Dependencies

| Component | Dependency | Status |
|-----------|------------|--------|
| Workflow execution | Agents working | Required |
| Tool execution | MCP servers working | Required |
| Scheduled triggers | Temporal Schedules | Built-in |
| Event triggers | MCP event system | Future |
| Persistence | PostgreSQL | Existing |

---

## Example Workflow Definitions

### Daily Briefing (Sequential)

```json
{
  "id": "wf_daily_briefing",
  "name": "Daily Briefing",
  "workflow_type": "sequential",
  "steps": [
    {
      "step_id": "step_calendar",
      "agent_id": "calendar-agent",
      "input_mapping": "Get today's calendar events"
    },
    {
      "step_id": "step_email",
      "agent_id": "email-agent",
      "input_mapping": "Get unread emails from today"
    },
    {
      "step_id": "step_summary",
      "agent_id": "summary-agent",
      "input_mapping": "{{previous.all}}"
    }
  ],
  "trigger_type": "scheduled",
  "trigger_config": {
    "cron_expression": "0 8 * * 1-5",
    "timezone": "America/New_York"
  }
}
```

### Multi-Source Research (Parallel)

```json
{
  "id": "wf_research",
  "name": "Multi-Source Research",
  "workflow_type": "parallel",
  "steps": [
    {"step_id": "web", "agent_id": "web-researcher"},
    {"step_id": "docs", "agent_id": "doc-searcher"},
    {"step_id": "db", "agent_id": "data-analyst"}
  ],
  "merge_strategy": "summary_agent",
  "merge_agent_id": "research-synthesizer",
  "trigger_type": "manual"
}
```

### Meeting Follow-up (Event-triggered)

```json
{
  "id": "wf_meeting_followup",
  "name": "Meeting Follow-up",
  "workflow_type": "single",
  "steps": [
    {"step_id": "followup", "agent_id": "meeting-followup-agent"}
  ],
  "trigger_type": "event",
  "trigger_config": {
    "mcp_server_id": "srv_calendar_123",
    "event_type": "event_ended",
    "filter": {"attendees_min": 2}
  }
}
```

# Agent Overview Tab - Implementation Specification

**Version:** 1.0
**Date:** January 2026
**Status:** Ready for Implementation

---

## Table of Contents

1. [Overview](#1-overview)
2. [Design Goals](#2-design-goals)
3. [UI/UX Design](#3-uiux-design)
4. [Data Model Changes](#4-data-model-changes)
5. [API Endpoints](#5-api-endpoints)
6. [Frontend Components](#6-frontend-components)
7. [Type-Specific Sections](#7-type-specific-sections)
8. [Implementation Phases](#8-implementation-phases)
9. [File Changes Summary](#9-file-changes-summary)

---

## 1. Overview

### Problem Statement

The current Agent Detail page only shows:
- Chat mode (interact with agent)
- Edit mode (configure agent)

Users cannot see:
- How their agent is performing
- What resources it's using (MCPs, skills, knowledge bases)
- Execution history and traces
- Common user queries
- Error patterns and suggestions

### Solution

Add an **Overview tab** to the Agent Detail page that provides comprehensive insights into agent performance, resource usage, and execution history.

---

## 2. Design Goals

### 2.1 User Personas

| Persona | Primary Needs |
|---------|---------------|
| **Developer** | Debug issues, trace executions, understand errors |
| **Product Manager** | Usage trends, top asks, success rates |
| **Operations** | Cost tracking, performance metrics, error rates |

### 2.2 Design Principles

1. **Glanceable**: Key metrics visible in under 3 seconds
2. **Actionable**: Every insight suggests a next step
3. **Minimal**: Show 4-5 prominent metrics, not 50
4. **Contextual**: Compare to baselines with trend arrows
5. **Delightful**: Animations and celebrations for milestones

---

## 3. UI/UX Design

### 3.1 Page Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ← Back              [Agent Name]                         [Edit] [Delete]    │
│                      [Avatar] [Type Badge] · "Personality"                   │
├──────────────────────────────────────────────────────────────────────────────┤
│  [Overview]  [Chat]  [Configuration]                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                              │
│  ┌─ MILESTONE BANNER (conditional) ────────────────────────────────────────┐ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ PERFORMANCE STATS ─────────────────────────────────────────────────────┐ │
│  │  [Executions] [Success Rate] [Avg Latency] [Cost] [Tokens]              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ USAGE CHART ───────────────────────────────────────────────────────────┐ │
│  │  Bar chart showing executions over time                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ TYPE-SPECIFIC SECTIONS ────────────────────────────────────────────────┐ │
│  │  Sub-Agents (Orchestrator) | Tools (ToolAgent) | KB (RAGAgent) | etc.   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ MCP SERVERS ───────────────────────────────────────────────────────────┐ │
│  │  Connected MCPs with tool usage stats                                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ SKILLS ────────────────────────────────────────────────────────────────┐ │
│  │  Attached skills with invocation stats                                  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ KNOWLEDGE BASES ───────────────────────────────────────────────────────┐ │
│  │  Connected KBs with query stats and top topics                          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ TOP ASKS ──────────────────┐  ┌─ RECENT EXECUTIONS ────────────────────┐ │
│  │  Most common user queries   │  │  Execution list with trace preview     │ │
│  └─────────────────────────────┘  └────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ ERROR BREAKDOWN (conditional) ─────────────────────────────────────────┐ │
│  │  Error types with counts and suggestions                                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Stats Cards Design

```
┌──────────────────┐
│ ⚡ Tasks         │
│   Conquered      │
│                  │
│     156          │  ← Animated counter
│   ↑ +12%         │  ← Trend vs last period
│   vs last week   │
└──────────────────┘
```

**Card Variations by Status:**
- **Excellent** (green glow): Success rate > 95%
- **Good** (emerald): Success rate 90-95%
- **Warning** (amber): Success rate 80-90%
- **Critical** (red): Success rate < 80%

### 3.3 Execution Trace View (Modal)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Execution #exec-abc123                                    [✕]               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Input: "Help me draft an email to John about rescheduling our meeting"     │
│  Status: ✓ Completed | Duration: 1.2s | Cost: $0.02 | Tokens: 1,456         │
│                                                                              │
│  ┌─ Execution Trace ────────────────────────────────────────────────────┐   │
│  │                                                                       │   │
│  │  1. 🎯 Orchestrator                                          0.1s   │   │
│  │     └─ Decision: Route to Email Agent                                │   │
│  │                                                                       │   │
│  │  2. 📧 Email Agent                                           0.8s   │   │
│  │     ├─ 🎯 Skill: Email Drafting                                      │   │
│  │     ├─ 📚 KB Query: "email etiquette" → 3 chunks                     │   │
│  │     ├─ 🤖 LLM Call: gpt-4o (892/245 tokens)                  0.5s   │   │
│  │     └─ 🔧 Tool: gmail:draft_email                            0.2s   │   │
│  │                                                                       │   │
│  │  3. 🎯 Orchestrator                                          0.1s   │   │
│  │     └─ Aggregated response                                           │   │
│  │                                                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Output: "I've drafted an email to John..."                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Empty States

| State | Icon | Message |
|-------|------|---------|
| No executions | 🚀 (floating) | "Ready for launch! Send your first message" |
| No top asks | ❓ (bouncing) | "Once users start chatting, their top questions appear here" |
| Zero errors | ✨ | "Clean slate! Let's keep this streak going" |
| No MCPs | 🔌 | "Connect an MCP server to extend your agent's capabilities" |
| No skills | 🎯 | "Add skills to give your agent superpowers" |
| No KBs | 📚 | "Connect a knowledge base to make your agent smarter" |

### 3.5 Micro-interactions

| Element | Interaction |
|---------|-------------|
| Stats cards | Numbers animate counting up with spring physics |
| Card hover | Subtle lift (y: -2px) with shadow increase |
| Chart bars | Staggered entrance animation from bottom |
| Milestone hit | Confetti burst + celebration banner |
| Success streak | Badge appears after 5 consecutive successes |
| Loading | Shimmer animation with playful messages |

---

## 4. Data Model Changes

### 4.1 Update AgentExecutionModel

**File:** `src/monitoring/analytics/models.py`

```python
class AgentExecutionModel(Base):
    """SQLAlchemy model for agent execution tracking."""

    __tablename__ = "agent_executions"

    # === Existing Fields ===
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_calls_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tool_calls_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # === NEW Fields ===

    # Input tracking for "Top Asks"
    input_preview: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="First 200 chars of sanitized user input"
    )
    input_intent: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True,
        comment="Classified intent: draft_email, schedule_meeting, etc."
    )

    # Resource usage tracking (JSON for flexibility)
    tools_called: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment='{"gmail:send": 2, "calendar:create": 1}'
    )
    skills_invoked: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment='{"email-drafting": 1, "sentiment": 1}'
    )
    kb_queries: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment='{"company-docs": 3, "faqs": 2}'
    )
    sub_agents_called: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment='{"email-agent": 1, "calendar-agent": 1}'
    )
    mcp_servers_used: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True,
        comment='["gmail-mcp", "calendar-mcp"]'
    )

    # Execution tracing
    parent_execution_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True,
        comment="Parent execution ID for nested agent calls"
    )
    execution_trace: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="Full execution trace tree for debugging"
    )

    # Token/cost tracking at execution level
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Output tracking
    output_preview: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="First 500 chars of agent output"
    )
```

### 4.2 Migration Script

**File:** `alembic/versions/xxxx_add_agent_execution_tracking.py`

```python
"""Add agent execution tracking fields

Revision ID: xxxx
Revises: previous_revision
Create Date: 2026-01-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

def upgrade():
    op.add_column('agent_executions', sa.Column('input_preview', sa.String(200), nullable=True))
    op.add_column('agent_executions', sa.Column('input_intent', sa.String(50), nullable=True))
    op.add_column('agent_executions', sa.Column('tools_called', JSON, nullable=True))
    op.add_column('agent_executions', sa.Column('skills_invoked', JSON, nullable=True))
    op.add_column('agent_executions', sa.Column('kb_queries', JSON, nullable=True))
    op.add_column('agent_executions', sa.Column('sub_agents_called', JSON, nullable=True))
    op.add_column('agent_executions', sa.Column('mcp_servers_used', JSON, nullable=True))
    op.add_column('agent_executions', sa.Column('parent_execution_id', sa.String(36), nullable=True))
    op.add_column('agent_executions', sa.Column('execution_trace', JSON, nullable=True))
    op.add_column('agent_executions', sa.Column('total_tokens', sa.Integer, nullable=False, server_default='0'))
    op.add_column('agent_executions', sa.Column('total_cost_cents', sa.Integer, nullable=False, server_default='0'))
    op.add_column('agent_executions', sa.Column('output_preview', sa.String(500), nullable=True))

    # Add indexes
    op.create_index('ix_agent_executions_input_intent', 'agent_executions', ['input_intent'])
    op.create_index('ix_agent_executions_parent_execution_id', 'agent_executions', ['parent_execution_id'])

def downgrade():
    op.drop_index('ix_agent_executions_parent_execution_id')
    op.drop_index('ix_agent_executions_input_intent')
    op.drop_column('agent_executions', 'output_preview')
    op.drop_column('agent_executions', 'total_cost_cents')
    op.drop_column('agent_executions', 'total_tokens')
    op.drop_column('agent_executions', 'execution_trace')
    op.drop_column('agent_executions', 'parent_execution_id')
    op.drop_column('agent_executions', 'mcp_servers_used')
    op.drop_column('agent_executions', 'sub_agents_called')
    op.drop_column('agent_executions', 'kb_queries')
    op.drop_column('agent_executions', 'skills_invoked')
    op.drop_column('agent_executions', 'tools_called')
    op.drop_column('agent_executions', 'input_intent')
    op.drop_column('agent_executions', 'input_preview')
```

---

## 5. API Endpoints

### 5.1 Endpoint Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents/{agent_id}/stats` | GET | Performance stats for cards |
| `/agents/{agent_id}/executions` | GET | Recent executions list |
| `/agents/{agent_id}/executions/{execution_id}` | GET | Full execution trace |
| `/agents/{agent_id}/usage-history` | GET | Chart data (daily/hourly) |
| `/agents/{agent_id}/mcp-usage` | GET | MCP servers + tool stats |
| `/agents/{agent_id}/skill-usage` | GET | Skills invocation stats |
| `/agents/{agent_id}/kb-usage` | GET | Knowledge base query stats |
| `/agents/{agent_id}/sub-agent-usage` | GET | Sub-agent delegation stats |
| `/agents/{agent_id}/top-asks` | GET | Most common user queries |
| `/agents/{agent_id}/error-breakdown` | GET | Error analysis |

### 5.2 Common Query Parameters

```
time_range: str = "7d"  # Options: "24h", "7d", "30d", "90d"
```

### 5.3 Response Schemas

#### AgentStatsResponse

```python
class AgentStatsResponse(BaseModel):
    agent_id: str
    time_range: str

    # Performance metrics
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float          # 0.0 to 1.0
    avg_latency_ms: float
    p95_latency_ms: float

    # Cost metrics
    total_cost_cents: int
    total_tokens: int

    # Trends (percentage change vs previous period)
    executions_trend: float      # +12.5 means 12.5% increase
    success_trend: float
    latency_trend: float
    cost_trend: float
```

#### AgentExecutionsResponse

```python
class ExecutionSummary(BaseModel):
    id: str
    status: str                  # "completed", "failed", "running"
    timestamp: datetime
    duration_ms: Optional[int]
    input_preview: Optional[str]
    output_preview: Optional[str]
    error_type: Optional[str]
    error_message: Optional[str]
    tools_called: Optional[List[str]]
    sub_agents_called: Optional[List[str]]
    total_tokens: int
    total_cost_cents: int

class AgentExecutionsResponse(BaseModel):
    executions: List[ExecutionSummary]
    total: int
    has_more: bool
```

#### ExecutionTraceResponse

```python
class TraceStep(BaseModel):
    step_id: str
    step_type: str               # "orchestrator", "agent", "tool", "skill", "kb_query", "llm_call"
    name: str
    started_at: datetime
    duration_ms: int
    status: str                  # "completed", "failed", "running"
    input_preview: Optional[str]
    output_preview: Optional[str]
    metadata: Optional[dict]     # tokens, model, relevance score, etc.
    children: List["TraceStep"] = []

class ExecutionTraceResponse(BaseModel):
    id: str
    agent_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: int
    input: str
    output: Optional[str]
    error: Optional[str]
    trace: TraceStep             # Root of trace tree
    total_tokens: int
    total_cost_cents: int
```

#### AgentMCPUsageResponse

```python
class MCPToolUsage(BaseModel):
    tool_name: str
    call_count: int
    success_rate: float
    avg_latency_ms: float

class MCPServerUsage(BaseModel):
    server_id: str
    server_name: str
    template: str
    status: str                  # "connected", "disconnected", "error"
    tools: List[MCPToolUsage]
    total_calls: int
    total_errors: int

class AgentMCPUsageResponse(BaseModel):
    servers: List[MCPServerUsage]
    total_tool_calls: int
    time_range: str
```

#### AgentSkillUsageResponse

```python
class SkillUsage(BaseModel):
    skill_id: str
    skill_name: str
    description: str
    invocation_count: int
    success_rate: float
    avg_contribution_score: Optional[float]  # If we track skill effectiveness
    enabled: bool

class AgentSkillUsageResponse(BaseModel):
    skills: List[SkillUsage]
    total_invocations: int
    time_range: str
```

#### AgentKBUsageResponse

```python
class KBTopTopic(BaseModel):
    topic: str                   # Extracted/clustered topic
    query_count: int

class KBUsage(BaseModel):
    kb_id: str
    kb_name: str
    chunk_count: int
    query_count: int
    avg_relevance_score: float   # Average relevance of retrieved chunks
    avg_chunks_retrieved: float  # Avg chunks per query
    top_topics: List[KBTopTopic]

class AgentKBUsageResponse(BaseModel):
    knowledge_bases: List[KBUsage]
    total_queries: int
    time_range: str
```

#### AgentSubAgentUsageResponse

```python
class SubAgentUsage(BaseModel):
    agent_id: str
    agent_name: str
    agent_type: str
    delegation_count: int
    success_rate: float
    avg_latency_ms: float
    total_cost_cents: int

class AgentSubAgentUsageResponse(BaseModel):
    sub_agents: List[SubAgentUsage]
    total_delegations: int
    delegation_flow: Optional[dict]  # For visualization
    time_range: str
```

#### AgentTopAsksResponse

```python
class TopAsk(BaseModel):
    intent: str                  # Classified intent ID
    display_text: str            # Human-readable example
    count: int
    trend: str                   # "up", "down", "new", "stable"
    trend_percent: Optional[float]

class AgentTopAsksResponse(BaseModel):
    asks: List[TopAsk]
    total_unique_intents: int
    time_range: str
```

#### AgentErrorBreakdownResponse

```python
class ErrorTypeBreakdown(BaseModel):
    error_type: str
    count: int
    percentage: float
    last_occurred: datetime
    suggestion: Optional[str]    # Actionable fix suggestion
    affected_resource: Optional[str]  # e.g., "gmail-mcp"

class AgentErrorBreakdownResponse(BaseModel):
    errors: List[ErrorTypeBreakdown]
    total_errors: int
    error_rate: float            # errors / total executions
    time_range: str
```

#### AgentUsageHistoryResponse

```python
class UsageDataPoint(BaseModel):
    timestamp: str               # ISO format
    executions: int
    successful: int
    failed: int
    avg_latency_ms: float
    total_cost_cents: int

class AgentUsageHistoryResponse(BaseModel):
    data: List[UsageDataPoint]
    granularity: str             # "hour" or "day"
    time_range: str
```

---

## 6. Frontend Components

### 6.1 Component Tree

```
web/components/agents/
├── agent-overview/
│   ├── index.tsx                      # Main overview container
│   ├── time-range-selector.tsx        # 24h | 7d | 30d | 90d toggle
│   ├── stats-cards.tsx                # Performance stats grid (5 cards)
│   ├── usage-chart.tsx                # Bar chart with tooltips
│   ├── sub-agents-section.tsx         # Sub-agent cards + flow diagram
│   ├── mcp-servers-section.tsx        # MCP cards with tool breakdown
│   ├── skills-section.tsx             # Skills with invocation stats
│   ├── knowledge-bases-section.tsx    # KB cards with top topics
│   ├── top-asks-section.tsx           # Ranked list with trends
│   ├── recent-executions.tsx          # Execution list with click-to-expand
│   ├── execution-trace-modal.tsx      # Full trace tree modal
│   ├── error-breakdown-section.tsx    # Error bars with suggestions
│   ├── milestone-banner.tsx           # Celebration banner
│   ├── empty-states.tsx               # All empty state variants
│   └── overview-skeleton.tsx          # Loading skeleton with shimmer
├── agent-avatar.tsx                   # Type-based avatar with glow/pulse
└── delightful-stats-card.tsx          # Animated stat card component
```

### 6.2 Hooks

**File:** `web/lib/hooks/use-agent-stats.ts`

```typescript
// Query key factory
export const agentStatsKeys = {
  all: ["agent-stats"] as const,
  stats: (agentId: string, timeRange: string) =>
    [...agentStatsKeys.all, "stats", agentId, timeRange] as const,
  executions: (agentId: string, filters?: ExecutionFilters) =>
    [...agentStatsKeys.all, "executions", agentId, filters] as const,
  executionTrace: (agentId: string, executionId: string) =>
    [...agentStatsKeys.all, "trace", agentId, executionId] as const,
  usageHistory: (agentId: string, timeRange: string, granularity: string) =>
    [...agentStatsKeys.all, "history", agentId, timeRange, granularity] as const,
  mcpUsage: (agentId: string, timeRange: string) =>
    [...agentStatsKeys.all, "mcp", agentId, timeRange] as const,
  skillUsage: (agentId: string, timeRange: string) =>
    [...agentStatsKeys.all, "skills", agentId, timeRange] as const,
  kbUsage: (agentId: string, timeRange: string) =>
    [...agentStatsKeys.all, "kb", agentId, timeRange] as const,
  subAgentUsage: (agentId: string, timeRange: string) =>
    [...agentStatsKeys.all, "sub-agents", agentId, timeRange] as const,
  topAsks: (agentId: string, timeRange: string) =>
    [...agentStatsKeys.all, "top-asks", agentId, timeRange] as const,
  errorBreakdown: (agentId: string, timeRange: string) =>
    [...agentStatsKeys.all, "errors", agentId, timeRange] as const,
};

// Hooks
export function useAgentStats(agentId: string, timeRange = "7d");
export function useAgentExecutions(agentId: string, options?: ExecutionFilters);
export function useExecutionTrace(agentId: string, executionId: string);
export function useAgentUsageHistory(agentId: string, timeRange = "7d", granularity = "day");
export function useAgentMCPUsage(agentId: string, timeRange = "7d");
export function useAgentSkillUsage(agentId: string, timeRange = "7d");
export function useAgentKBUsage(agentId: string, timeRange = "7d");
export function useAgentSubAgentUsage(agentId: string, timeRange = "7d");
export function useAgentTopAsks(agentId: string, timeRange = "7d");
export function useAgentErrorBreakdown(agentId: string, timeRange = "7d");
```

### 6.3 Main Overview Component

```typescript
// web/components/agents/agent-overview/index.tsx

export function AgentOverview({ agent }: { agent: AgentDetail }) {
  const [timeRange, setTimeRange] = useState("7d");

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <TimeRangeSelector value={timeRange} onChange={setTimeRange} />

      {/* Milestone Banner (conditional) */}
      <MilestoneBanner agentId={agent.id} />

      {/* Performance Stats */}
      <StatsCards agentId={agent.id} timeRange={timeRange} />

      {/* Usage Chart */}
      <UsageChart agentId={agent.id} timeRange={timeRange} />

      {/* Type-Specific Sections */}
      {agent.agent_type === "OrchestratorAgent" && (
        <SubAgentsSection agentId={agent.id} timeRange={timeRange} />
      )}

      {/* MCP Servers (if any connected) */}
      <MCPServersSection agentId={agent.id} timeRange={timeRange} />

      {/* Skills (if any attached) */}
      <SkillsSection agentId={agent.id} timeRange={timeRange} />

      {/* Knowledge Bases (for RAG/Full agents) */}
      {["RAGAgent", "FullAgent"].includes(agent.agent_type) && (
        <KnowledgeBasesSection agentId={agent.id} timeRange={timeRange} />
      )}

      {/* Two-column layout for Top Asks + Recent Executions */}
      <div className="grid gap-6 lg:grid-cols-2">
        <TopAsksSection agentId={agent.id} timeRange={timeRange} />
        <RecentExecutions agentId={agent.id} />
      </div>

      {/* Error Breakdown (conditional - only if errors exist) */}
      <ErrorBreakdownSection agentId={agent.id} timeRange={timeRange} />
    </div>
  );
}
```

---

## 7. Type-Specific Sections

### 7.1 Section Visibility by Agent Type

| Section | Simple | LLM | RAG | Tool | Full | Router | Orchestrator |
|---------|--------|-----|-----|------|------|--------|--------------|
| Stats Cards | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Usage Chart | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Sub-Agents | - | - | - | - | - | - | ✓✓ |
| MCP Servers | ○ | ○ | ○ | ✓ | ✓ | ○ | ✓ |
| Skills | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| Knowledge Bases | - | - | ✓✓ | - | ✓✓ | - | ○ |
| Routing Distribution | - | - | - | - | - | ✓✓ | - |
| Token Usage Detail | - | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Top Asks | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Recent Executions | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Error Breakdown | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Legend:**
- ✓✓ = Prominent/expanded
- ✓ = Shown
- ○ = Shown if configured (has MCPs/skills/etc.)
- - = Not shown

### 7.2 Orchestrator-Specific: Sub-Agent Section

```
┌─ SUB-AGENTS (4 connected) ──────────────────────────────────────────────────┐
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ 📧 Email Agent   │  │ 📅 Calendar Agent│  │ 🔍 FAQ Agent     │          │
│  │ ToolAgent        │  │ ToolAgent        │  │ RAGAgent         │          │
│  │                  │  │                  │  │                  │          │
│  │ 52 delegations   │  │ 38 delegations   │  │ 45 delegations   │          │
│  │ ✓ 98% success    │  │ ✓ 94% success    │  │ ✓ 91% success    │          │
│  │ ⚡ 1.2s avg      │  │ ⚡ 0.8s avg      │  │ ⚡ 0.6s avg      │          │
│  │ $4.20 cost       │  │ $3.10 cost       │  │ $2.80 cost       │          │
│  │                  │  │                  │  │                  │          │
│  │ [View →]         │  │ [View →]         │  │ [View →]         │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                              │
│  Delegation Flow:                                                           │
│       ┌──────────────┐                                                      │
│       │ Orchestrator │                                                      │
│       └──────┬───────┘                                                      │
│      ┌───┬───┴───┬───┐                                                      │
│      ▼   ▼       ▼   ▼                                                      │
│   [Email][Cal] [FAQ][Esc]                                                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Router-Specific: Routing Distribution

```
┌─ ROUTING DISTRIBUTION ──────────────────────────────────────────────────────┐
│                                                                              │
│  Where queries were routed:                                                 │
│                                                                              │
│  Sales Agent        ████████████████████░░░░░░  45%  (52 queries)          │
│  Support Agent      ████████████░░░░░░░░░░░░░░  28%  (32 queries)          │
│  Technical Agent    ████████░░░░░░░░░░░░░░░░░░  18%  (21 queries)          │
│  Fallback (self)    ████░░░░░░░░░░░░░░░░░░░░░░   9%  (10 queries)          │
│                                                                              │
│  Routing confidence: Avg 0.89 | Low confidence (<0.7): 8 queries           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Implementation Phases

### Phase 1: Database & Models (Day 1)

| Task | File | Action |
|------|------|--------|
| 1.1 | `src/monitoring/analytics/models.py` | Add new columns to AgentExecutionModel |
| 1.2 | `alembic/versions/xxx_*.py` | Create migration |
| 1.3 | Run migration | `alembic upgrade head` |

### Phase 2: Backend APIs (Days 2-3)

| Task | File | Action |
|------|------|--------|
| 2.1 | `src/api/schemas/agent.py` | Add all response schemas |
| 2.2 | `src/api/routers/agents.py` | Add `/stats` endpoint |
| 2.3 | `src/api/routers/agents.py` | Add `/executions` endpoint |
| 2.4 | `src/api/routers/agents.py` | Add `/executions/{id}` endpoint |
| 2.5 | `src/api/routers/agents.py` | Add `/usage-history` endpoint |
| 2.6 | `src/api/routers/agents.py` | Add `/mcp-usage` endpoint |
| 2.7 | `src/api/routers/agents.py` | Add `/skill-usage` endpoint |
| 2.8 | `src/api/routers/agents.py` | Add `/kb-usage` endpoint |
| 2.9 | `src/api/routers/agents.py` | Add `/sub-agent-usage` endpoint |
| 2.10 | `src/api/routers/agents.py` | Add `/top-asks` endpoint |
| 2.11 | `src/api/routers/agents.py` | Add `/error-breakdown` endpoint |
| 2.12 | Test with curl | Verify all endpoints return correct data |

### Phase 3: Frontend Types & Hooks (Day 4)

| Task | File | Action |
|------|------|--------|
| 3.1 | `web/types/agent-stats.ts` | Create TypeScript types |
| 3.2 | `web/lib/api/agent-stats.ts` | Create API client functions |
| 3.3 | `web/lib/hooks/use-agent-stats.ts` | Create React Query hooks |

### Phase 4: UI Components (Days 5-7)

| Task | File | Action |
|------|------|--------|
| 4.1 | `agent-overview/empty-states.tsx` | Empty state components |
| 4.2 | `agent-overview/overview-skeleton.tsx` | Loading skeleton |
| 4.3 | `delightful-stats-card.tsx` | Animated stat card |
| 4.4 | `agent-avatar.tsx` | Type-based avatar |
| 4.5 | `agent-overview/stats-cards.tsx` | Stats cards grid |
| 4.6 | `agent-overview/usage-chart.tsx` | Bar chart |
| 4.7 | `agent-overview/mcp-servers-section.tsx` | MCP section |
| 4.8 | `agent-overview/skills-section.tsx` | Skills section |
| 4.9 | `agent-overview/knowledge-bases-section.tsx` | KB section |
| 4.10 | `agent-overview/sub-agents-section.tsx` | Sub-agents section |
| 4.11 | `agent-overview/top-asks-section.tsx` | Top asks |
| 4.12 | `agent-overview/recent-executions.tsx` | Executions list |
| 4.13 | `agent-overview/execution-trace-modal.tsx` | Trace modal |
| 4.14 | `agent-overview/error-breakdown-section.tsx` | Error breakdown |
| 4.15 | `agent-overview/milestone-banner.tsx` | Celebration banner |
| 4.16 | `agent-overview/time-range-selector.tsx` | Time range toggle |
| 4.17 | `agent-overview/index.tsx` | Main container |

### Phase 5: Page Integration (Day 8)

| Task | File | Action |
|------|------|--------|
| 5.1 | `web/app/(protected)/agents/[id]/page.tsx` | Add tabs |
| 5.2 | `web/app/(protected)/agents/[id]/page.tsx` | Integrate AgentOverview |
| 5.3 | End-to-end testing | Test full flow |

---

## 9. File Changes Summary

### Backend Files

| File | Action | Changes |
|------|--------|---------|
| `src/monitoring/analytics/models.py` | Modify | Add 12 new columns |
| `alembic/versions/xxx_add_tracking.py` | Create | Migration script |
| `src/api/schemas/agent.py` | Modify | Add 12 response schemas |
| `src/api/routers/agents.py` | Modify | Add 10 endpoints |

### Frontend Files

| File | Action | Changes |
|------|--------|---------|
| `web/types/agent-stats.ts` | Create | TypeScript types |
| `web/lib/api/agent-stats.ts` | Create | API client (10 functions) |
| `web/lib/hooks/use-agent-stats.ts` | Create | React Query hooks (10 hooks) |
| `web/components/agents/agent-avatar.tsx` | Create | Avatar component |
| `web/components/agents/delightful-stats-card.tsx` | Create | Stats card component |
| `web/components/agents/agent-overview/index.tsx` | Create | Main container |
| `web/components/agents/agent-overview/time-range-selector.tsx` | Create | Time selector |
| `web/components/agents/agent-overview/stats-cards.tsx` | Create | Stats grid |
| `web/components/agents/agent-overview/usage-chart.tsx` | Create | Bar chart |
| `web/components/agents/agent-overview/sub-agents-section.tsx` | Create | Sub-agents |
| `web/components/agents/agent-overview/mcp-servers-section.tsx` | Create | MCP section |
| `web/components/agents/agent-overview/skills-section.tsx` | Create | Skills section |
| `web/components/agents/agent-overview/knowledge-bases-section.tsx` | Create | KB section |
| `web/components/agents/agent-overview/top-asks-section.tsx` | Create | Top asks |
| `web/components/agents/agent-overview/recent-executions.tsx` | Create | Executions list |
| `web/components/agents/agent-overview/execution-trace-modal.tsx` | Create | Trace modal |
| `web/components/agents/agent-overview/error-breakdown-section.tsx` | Create | Errors |
| `web/components/agents/agent-overview/milestone-banner.tsx` | Create | Celebrations |
| `web/components/agents/agent-overview/empty-states.tsx` | Create | Empty states |
| `web/components/agents/agent-overview/overview-skeleton.tsx` | Create | Loading |
| `web/app/(protected)/agents/[id]/page.tsx` | Modify | Add tabs + overview |

### Dependencies

```bash
npm install canvas-confetti
npm install -D @types/canvas-confetti
```

---

## Appendix A: Error Suggestions Mapping

| Error Type | Suggestion | Affected Resource |
|------------|------------|-------------------|
| `rate_limit` | "Add retry with exponential backoff" | MCP server name |
| `auth_expired` | "[Reconnect Integration]" button | MCP server name |
| `timeout` | "Consider increasing timeout or simplifying request" | - |
| `invalid_input` | "Check input validation in agent configuration" | - |
| `kb_not_found` | "Verify knowledge base is indexed" | KB name |
| `tool_not_available` | "Check MCP server connection" | MCP server name |

---

## Appendix B: Milestone Thresholds

| Milestone | Threshold | Message |
|-----------|-----------|---------|
| First execution | 1 | "First blood! Your agent completed its first task" |
| Century club | 100 | "Triple digits! Your agent hit 100 executions" |
| Power user | 500 | "Power User! 500 executions and counting" |
| Legendary | 1000 | "Legendary! 1K executions milestone" |
| High success | 95% (min 50 exec) | "Precision Master! 95%+ success rate" |
| Near perfect | 99% (min 100 exec) | "Near Perfect! 99%+ success rate" |
| Perfect | 100% (min 50 exec) | "Flawless Victory! 100% success rate" |
| Hot streak | 10 consecutive | "Hot Streak! 10 successes in a row" |
| On fire | 25 consecutive | "On Fire! 25 consecutive wins" |

---

**Document Version:** 1.0
**Last Updated:** January 2026
**Author:** MagOneAI Engineering Team

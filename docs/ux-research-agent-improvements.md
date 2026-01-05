# UX Research: Agent Management UI Improvements

## MagOneAI v2 Agent Dashboard Enhancement Study

**Version:** 1.0
**Date:** January 2026
**Research Type:** Rapid UX Research (6-Day Sprint Compatible)
**Status:** Ready for Implementation Planning

---

## Executive Summary

This research document addresses critical usability gaps in the MagOneAI v2 agent management interface. The current UI presents agents as a flat list without relationship hierarchy, lacks agent-specific dashboards, and disperses logs across generic monitoring pages.

### Key Findings

| Problem | Severity | Impact |
|---------|----------|--------|
| Flat agent list obscures orchestrator/sub-agent relationships | Critical | Users cannot understand agent architecture |
| No agent-specific dashboard | High | Debugging requires cross-referencing multiple views |
| Workflow-to-agent mapping unclear | High | Unable to trace execution paths |
| Generic monitoring page for all logs | Medium | Context switching slows debugging |
| No visual hierarchy for multi-agent executions | Critical | Complex executions are opaque |

### Recommended Priority Actions

1. **Implement hierarchical agent tree view** (Week 1-2)
2. **Create agent-specific dashboard with execution history** (Week 2-3)
3. **Add execution trace visualization with call hierarchy** (Week 3-4)
4. **Integrate contextual logs within agent views** (Week 4)

---

## 1. User Journey Analysis

### 1.1 Current User Journey: Understanding Agent Relationships

```
User Goal: Understand how agents work together in an orchestration

CURRENT JOURNEY (Pain Points Highlighted)
=========================================

Step 1: Navigate to Agents List
       [Friction: Flat list shows all agents equally]
       |
       v
Step 2: Scan list for orchestrator agent
       [Friction: No visual distinction between orchestrator and sub-agents]
       [Cognitive Load: Must remember agent types from configuration]
       |
       v
Step 3: Click into orchestrator agent
       [Friction: Configuration view, not relationship view]
       |
       v
Step 4: Find "available_agents" in config JSON
       [Friction: Technical JSON parsing required]
       [Cognitive Load: Must cross-reference agent IDs manually]
       |
       v
Step 5: Navigate back to list, find each sub-agent
       [Friction: Multiple navigation steps]
       [Cognitive Load: Mental model building required]
       |
       v
Step 6: Repeat for nested orchestrators
       [Friction: No visual map of full hierarchy]
       [Time: 5-10 minutes for simple orchestrations]
```

**Expected Experience:**
- Single view showing orchestrator with connected sub-agents
- Visual tree or graph representation
- Click-to-expand for details
- Time expectation: Under 30 seconds

**Actual Experience:**
- Multiple navigation steps required
- Manual JSON parsing
- Mental model construction
- Time actual: 5-10+ minutes

### 1.2 Current User Journey: Debugging Agent Execution

```
User Goal: Understand why an agent execution failed

CURRENT JOURNEY (Pain Points Highlighted)
=========================================

Step 1: Notice unexpected behavior in chat/output
       |
       v
Step 2: Navigate to Monitoring page
       [Friction: Context switch from agent view]
       |
       v
Step 3: Search/filter logs for relevant execution
       [Friction: Generic log stream, no agent context]
       |
       v
Step 4: Find relevant log entries
       [Friction: Logs from all agents mixed together]
       |
       v
Step 5: Cross-reference with Temporal workflow UI
       [Friction: Second tool/context switch]
       |
       v
Step 6: Piece together execution flow manually
       [Friction: No unified trace view]
       [Time: 15-30 minutes for complex executions]
```

**Expected Experience:**
- Click on execution from agent view
- See full trace with all nested agent calls
- Logs inline with each step
- Time expectation: Under 2 minutes

### 1.3 Cognitive Load Analysis

| User Task | Current Cognitive Load | Ideal Cognitive Load |
|-----------|----------------------|---------------------|
| Understand agent hierarchy | High (mental model building) | Low (visual representation) |
| Find specific agent logs | High (search + filter) | Low (contextual logs) |
| Trace multi-agent execution | Very High (cross-tool correlation) | Low (unified trace view) |
| Identify performance bottlenecks | High (manual analysis) | Low (visual timeline) |
| Understand agent capabilities | Medium (JSON parsing) | Low (visual capability list) |

---

## 2. User Personas and Needs

### 2.1 Persona: Developer (Primary User)

```
Name: Alex Chen
Role: Full-Stack Developer / AI Engineer
Tech Savviness: Expert
Primary Goal: Build and debug multi-agent systems efficiently
```

**Key Needs from Agent Dashboard:**

| Need | Priority | Current Gap |
|------|----------|-------------|
| See agent relationships at a glance | Critical | No visual hierarchy |
| Quick access to execution history | Critical | Buried in monitoring |
| Trace multi-agent call chains | Critical | Not available |
| View logs in execution context | High | Generic monitoring page |
| Understand LLM token usage per agent | High | Aggregated only |
| Compare execution performance | Medium | Manual analysis required |

**Frustration Quote:**
> "I spend more time navigating between the agent list, monitoring page, and Temporal UI than actually debugging. I need everything in one place."

---

### 2.2 Persona: Operations / Platform Engineer

```
Name: Jordan Williams
Role: Platform Operations Engineer
Tech Savviness: High
Primary Goal: Ensure agent platform reliability and performance
```

**Key Needs from Agent Dashboard:**

| Need | Priority | Current Gap |
|------|----------|-------------|
| Real-time health overview of all agents | Critical | Not available |
| Error rate trends by agent | Critical | Aggregated only |
| Latency percentiles per agent | High | Not available |
| Token cost breakdown by agent | High | Not available |
| Execution queue depth | High | Only in Temporal UI |

**Frustration Quote:**
> "When something goes wrong at 2 AM, I don't have time to click through multiple pages. I need a single pane of glass showing me exactly which agent is failing."

---

### 2.3 Persona: Product Manager / Business User

```
Name: Sarah Kim
Role: Product Manager
Tech Savviness: Medium
Primary Goal: Understand agent behavior and usage for product decisions
```

**Key Needs from Agent Dashboard:**

| Need | Priority | Current Gap |
|------|----------|-------------|
| High-level agent usage analytics | Critical | Not available |
| User satisfaction metrics per agent | High | Not available |
| Simple agent relationship visualization | High | No visual representation |
| Task success/failure rates | High | Requires log analysis |

**Frustration Quote:**
> "I can't show the agent architecture to executives because there's no visual diagram. The flat list doesn't tell a story."

---

## 3. Competitive Analysis Insights

### 3.1 LangSmith Patterns (LangChain)

| Feature | Implementation | Applicability to MagOneAI |
|---------|---------------|-----------------------------|
| Trace Tree View | Hierarchical visualization of LLM calls | Direct apply for agent call chains |
| Run Details | Input/output at each step visible | Essential for debugging |
| Latency Breakdown | Visual timeline showing step duration | Critical for performance |
| Cost Tracking | Per-run token and cost attribution | Important for operations |

**Key UX Pattern: Trace-First Navigation**
- Every execution has a unique trace
- Traces show full call hierarchy
- Each node expandable for details
- Logs attached to specific trace steps

---

### 3.2 Langfuse Patterns

| Feature | Implementation | Applicability to MagOneAI |
|---------|---------------|-----------------------------|
| Graph View for Traces | Visual DAG of agent execution | Direct apply for multi-agent |
| Span Hierarchy | Parent-child relationship visualization | Perfect for orchestrator pattern |
| Observation Types | Distinguish LLM calls, retrievals, tools | Map to agent types |
| Session Tracking | Group related executions | Useful for conversation context |

**Key UX Pattern: Event Groups**
- Related events grouped automatically
- Color coding by status (success/failure/pending)
- Timeline view for temporal understanding

---

### 3.3 n8n Workflow Patterns

| Feature | Implementation | Applicability to MagOneAI |
|---------|---------------|-----------------------------|
| Visual Workflow Canvas | Drag-drop node-based editor | Agent relationship visualization |
| Execution Highlighting | Active nodes highlighted during run | Real-time execution trace |
| Node Status Indicators | Visual success/failure per node | Agent status at a glance |
| Parallel Path Visualization | Multiple branches shown clearly | Multi-agent parallel execution |

---

### 3.4 Temporal UI Patterns

| Feature | Implementation | Applicability to MagOneAI |
|---------|---------------|-----------------------------|
| Timeline View | Temporal progression of events | Execution trace timeline |
| Compact View | Simplified linear progression | Quick scanning |
| Event Grouping | Related events collapsed | Reduce visual noise |
| Full History | Complete event details | Deep debugging |

**Key UX Pattern: Three View Modes**
1. **Compact View:** Simplest, linear progression
2. **Timeline View:** Clock-time aware, shows gaps and parallelism
3. **Full History:** All event details, connected by relationship lines

---

### 3.5 Industry Pattern Summary

| Pattern | Recommendation for MagOneAI |
|---------|----------------------------|
| Hierarchical trace tree | Must have for agent calls |
| Visual DAG/Graph view | Must have for relationships |
| Color-coded status | Must have for quick scanning |
| Timeline view | Should have for performance |
| Contextual log panels | Must have for debugging |
| Multiple view modes | Should have for different users |
| Cost/token tracking | Should have for operations |

---

## 4. Proposed Information Architecture

### 4.1 Agent Hierarchy Model

```
                    [ROOT ORCHESTRATOR]
                    Mode: Hybrid | Active
                            |
         +------------------+------------------+
         |                  |                  |
    [EMAIL AGENT]    [CALENDAR AGENT]   [RESEARCH AGENT]
    Type: Tool       Type: Tool         Type: Orchestrator
                                               |
                                    +----------+----------+
                                    |                     |
                               [WEB SEARCH]         [SUMMARIZER]
                               Type: Tool           Type: LLM
```

### 4.2 Proposed Navigation Structure

```
Agents (Enhanced)
|
+-- [Tree View] / [List View] Toggle
|
+-- Agent Hierarchy View (NEW - Default)
|   - Visual tree of orchestrator -> sub-agents
|   - Color-coded by status
|   - Click to expand/collapse
|
+-- Agent Detail Page (Enhanced)
    |
    +-- Overview Tab
    |   - Agent info, mini hierarchy, capabilities, quick stats
    |
    +-- Executions Tab (NEW)
    |   - Execution history, filters, click to trace
    |
    +-- Traces Tab (NEW)
    |   - Visual trace tree, input/output, latency breakdown
    |
    +-- Logs Tab (NEW - Agent-Specific)
    |   - Filtered to this agent, linked to traces
    |
    +-- Performance Tab (NEW)
    |   - Latency charts, success rates, token usage
    |
    +-- Configuration Tab (Current)
```

### 4.3 New Top-Level: Executions

```
Executions (NEW)
|
+-- All Executions View
|   - Global timeline, filter by agent/status/workflow
|
+-- Execution Detail View
    +-- Summary (input/output, duration, agents involved)
    +-- Trace Visualization (tree view, timeline view, sequence diagram)
    +-- Step Details (expandable, input/output, inline logs)
    +-- Debug Tools (copy payload, replay, export)
```

---

## 5. Key UX Recommendations

### Priority 1: Critical

#### R1: Implement Hierarchical Agent Tree View

**Rationale:** The flat list is the root cause of users' inability to understand agent relationships.

**Specification:**
- Default view showing orchestrator → sub-agent relationships
- Collapsible nodes for large hierarchies
- Color coding: Green (active), Gray (idle), Red (error)
- Hover for quick stats (last run, success rate)
- Click to navigate to agent detail

**Success Metric:** Time to understand agent hierarchy < 30 seconds (vs current 5-10 minutes)

---

#### R2: Create Agent-Specific Dashboard

**Rationale:** Users need a single view for all agent-related information.

**Specification:**
- Overview tab with quick stats and mini hierarchy
- Executions tab with filtered history
- Traces tab with visual call tree
- Logs tab filtered to this agent
- Performance tab with charts

**Success Metric:** Time to access agent execution history < 10 seconds

---

#### R3: Add Execution Trace Visualization

**Rationale:** Multi-agent executions are currently opaque.

**Specification:**
- Tree view showing nested agent calls
- Each node shows: agent name, duration, status
- Expandable to show input/output
- Color coding by status
- Timeline toggle for temporal view

**Success Metric:** Time to identify failing agent in multi-agent execution < 2 minutes

---

### Priority 2: High

#### R4: Integrate Contextual Logs Within Agent Views

- Logs tab on agent detail page
- Filter to this agent's executions only
- Link logs to specific trace steps
- Real-time streaming for active executions

#### R5: Add Agent Health Overview to Dashboard

- Grid of agent cards on home dashboard
- Status indicator (healthy, degraded, error)
- Sparkline for recent execution trends

#### R6: Implement Workflow-to-Agent Mapping

- Workflow detail page shows triggered agents
- Agent execution shows triggering workflow
- Bi-directional linking in UI

---

### Priority 3: Medium

- **R7:** Add Multiple View Modes (Compact, Timeline, Full)
- **R8:** Implement Cost/Token Tracking Per Agent
- **R9:** Add Search and Filter for Traces

---

## 6. Implementation Roadmap

### Sprint 1 (Week 1-2): Foundation

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Design hierarchical tree component | Component spec |
| 3-4 | Implement tree view | Working tree view |
| 5 | API: Agent relationship endpoint | GET /agents/hierarchy |
| 6 | Integration and testing | Tree view live |

### Sprint 2 (Week 3-4): Agent Dashboard

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Design agent detail page layout | Wireframes |
| 3-5 | Implement Overview and Executions tabs | Dashboard v1 |
| 6 | API: Agent executions endpoint | GET /agents/{id}/executions |
| 7-8 | Implement Traces tab with tree view | Trace visualization |
| 9-10 | API: Trace collection and endpoint | GET /executions/{id}/trace |
| 11-12 | Integration and testing | Agent dashboard live |

### Sprint 3 (Week 5-6): Logs and Polish

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Implement Logs tab with filtering | Agent-specific logs |
| 3-4 | Implement Performance tab with charts | Performance metrics |
| 5-6 | Agent health overview on home dashboard | Health grid |
| 7 | Workflow-to-agent linking | Bi-directional links |
| 8-10 | User testing and polish | Production ready |

---

## 7. Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time to understand agent hierarchy | 5-10 min | < 30 sec |
| Time to find agent execution logs | 2-5 min | < 10 sec |
| Time to identify failing agent | 10-15 min | < 2 min |
| Context switches for debugging | 3-5 tools | 1 view |

---

## 8. Research Sources

- [LangSmith Observability](https://www.langchain.com/langsmith/observability)
- [Langfuse Graph View](https://langfuse.com/changelog/2025-02-14-trace-graph-view)
- [n8n AI Agentic Workflows](https://blog.n8n.io/ai-agentic-workflows/)
- [Temporal Timeline View](https://temporal.io/blog/lets-visualize-a-workflow)
- [Argo Workflows DAG](https://argo-workflows.readthedocs.io/en/latest/walk-through/dag/)

---

## Appendix A: Component Specifications

### A.1 Agent Tree Component

```typescript
interface AgentTreeNode {
  id: string;
  name: string;
  type: 'orchestrator' | 'tool' | 'llm' | 'rag' | 'full' | 'router';
  status: 'active' | 'idle' | 'error';
  children: AgentTreeNode[];
  metrics: {
    lastRun: Date | null;
    successRate: number;
    avgLatency: number;
  };
}

interface AgentTreeProps {
  root: AgentTreeNode;
  onNodeClick: (nodeId: string) => void;
  onNodeHover: (nodeId: string) => void;
  expandedNodes: Set<string>;
  selectedNode: string | null;
}
```

### A.2 Trace Tree Component

```typescript
interface TraceNode {
  id: string;
  agentId: string;
  agentName: string;
  type: 'agent_call' | 'tool_call' | 'llm_call' | 'skill_call';
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime: Date;
  endTime: Date | null;
  duration: number | null;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  error: string | null;
  children: TraceNode[];
  logs: LogEntry[];
}
```

---

## Appendix B: API Endpoint Specifications

### B.1 Agent Hierarchy Endpoint

```yaml
GET /api/v1/agents/hierarchy:
  summary: Get agent hierarchy tree
  parameters:
    - name: root_id
      in: query
      description: Optional root agent ID (defaults to all roots)
      type: string
  responses:
    200:
      schema:
        type: array
        items:
          $ref: '#/definitions/AgentTreeNode'
```

### B.2 Agent Executions Endpoint

```yaml
GET /api/v1/agents/{agent_id}/executions:
  summary: Get execution history for an agent
  parameters:
    - name: status
      in: query
      enum: [completed, failed, running, all]
    - name: from
      in: query
      format: date-time
    - name: limit
      in: query
      default: 50
```

### B.3 Execution Trace Endpoint

```yaml
GET /api/v1/executions/{execution_id}/trace:
  summary: Get full trace tree for an execution
  parameters:
    - name: include_logs
      in: query
      default: false
```

---

**Document Author:** UX Research Team
**Review Status:** Ready for Engineering Review
**Next Steps:** Schedule implementation planning meeting

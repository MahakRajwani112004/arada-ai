# MagOneAI v2 - Agent Management UI Improvements

## Design Document v1.0
**Date:** January 2026
**Status:** Proposed
**Tech Stack:** React/Next.js, shadcn/ui, Tailwind CSS, React Flow

---

## Executive Summary

This document outlines UI improvements to address five critical pain points in MagOneAI's agent management system:

| Pain Point | Solution |
|------------|----------|
| Flat agent list, unclear relationships | Hierarchy visualization + relationship graph |
| No agent-specific dashboard | Dedicated agent detail page with metrics |
| Unclear workflow-agent mapping | Execution trace with agent attribution |
| Generic monitoring, not agent-specific | Agent-scoped logs and analytics |
| No visual call traces | Interactive execution timeline with call tree |

---

## Design Principles

### Visual Hierarchy
- **Primary Actions:** Violet/Purple (#8B5CF6) - matches Orchestrator badge
- **Secondary:** Slate grays for supporting UI
- **Status Colors:** Consistent across all views
  - Success: Emerald (#10B981)
  - Warning: Amber (#F59E0B)
  - Error: Red (#EF4444)
  - Running: Blue (#3B82F6)

### Agent Type Color System (Existing)
```
Orchestrator: violet-500 (#8B5CF6)
Router:       orange-500 (#F97316)
Worker:       blue-500   (#3B82F6)
Tool:         emerald-500(#10B981)
Memory:       pink-500   (#EC4899)
```

---

## 1. Agent-Specific Dashboard

### Route Structure
```
/agents                    - Agent list (existing)
/agents/[agentId]          - Agent dashboard (NEW)
/agents/[agentId]/logs     - Agent logs (NEW)
/agents/[agentId]/config   - Agent configuration
```

### Dashboard Layout

```
+------------------------------------------------------------------+
|  < Back to Agents    [Agent Name]    [Type Badge]    [Edit] [...]|
+------------------------------------------------------------------+
|                                                                   |
|  +------------------+  +------------------+  +------------------+ |
|  | Total Executions |  | Success Rate     |  | Avg Duration     | |
|  |     1,247        |  |     94.2%        |  |     2.3s         | |
|  | +12% vs last wk  |  | -0.8% vs last wk |  | -0.4s vs last wk | |
|  +------------------+  +------------------+  +------------------+ |
|                                                                   |
|  +------------------+  +------------------+  +------------------+ |
|  | Tokens Used      |  | Avg Cost/Run     |  | Active Workflows | |
|  |    842.5K        |  |    $0.024        |  |       8          | |
|  | This month       |  | -15% vs avg      |  | Using this agent | |
|  +------------------+  +------------------+  +------------------+ |
|                                                                   |
+------------------------------------------------------------------+
|                                                                   |
|  [Executions] [Logs] [Performance] [Sub-Agents*]                 |
|  ----------------------------------------------------------------|
|                                                                   |
|  Execution History                            [Filter] [Export]  |
|  +--------------------------------------------------------------+|
|  | Status | Workflow      | Duration | Tokens | Cost   | Time   ||
|  |--------|---------------|----------|--------|--------|--------|
|  | [ok]   | Order Process | 1.8s     | 2,340  | $0.02  | 2m ago ||
|  | [ok]   | Customer Sup. | 3.2s     | 4,120  | $0.03  | 5m ago ||
|  | [err]  | Data Extract  | 0.4s     | 890    | $0.01  | 8m ago ||
|  +--------------------------------------------------------------+|
|                                                                   |
+------------------------------------------------------------------+

* Sub-Agents tab only visible for Orchestrator type agents
```

### Key Metrics Definitions

| Metric | Calculation | Display |
|--------|-------------|---------|
| Total Executions | COUNT(executions WHERE agent_id = X) | Number with period selector |
| Success Rate | (successful / total) * 100 | Percentage with trend |
| Avg Duration | AVG(end_time - start_time) | Seconds with trend |
| Tokens Used | SUM(input_tokens + output_tokens) | Formatted number (K/M) |
| Avg Cost/Run | AVG(cost) per execution | Currency |
| Active Workflows | COUNT(DISTINCT workflows using agent) | Number with link |

---

## 2. Orchestrator Hierarchy Visualization

### Sub-Agent Relationship View

```
+------------------------------------------------------------------+
|  Sub-Agents Managed by [Orchestrator Name]                       |
+------------------------------------------------------------------+
|                                                                   |
|  Hierarchy View                                [Tree] [List]     |
|                                                                   |
|                    +---------------------+                        |
|                    |   Order Processor   |                        |
|                    |   [Orchestrator]    |                        |
|                    +---------------------+                        |
|                             |                                     |
|           +-----------------+------------------+                  |
|           |                 |                  |                  |
|   +---------------+ +---------------+ +----------------+          |
|   | Validator     | | Price Calc    | | Inventory      |          |
|   | [Worker]      | | [Worker]      | | [Tool]         |          |
|   +---------------+ +---------------+ +----------------+          |
|                                                                   |
+------------------------------------------------------------------+
|  Sub-Agent Details                                                |
|  +--------------------------------------------------------------+|
|  | Agent           | Type     | Calls (24h) | Success | Avg Time||
|  |-----------------|----------|-------------|---------|---------|
|  | Validator       | Worker   | 1,247       | 98.2%   | 0.8s    ||
|  | Price Calc      | Worker   | 1,102       | 99.1%   | 1.2s    ||
|  | Inventory       | Tool     | 892         | 97.8%   | 0.3s    ||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

### Router Agent Routing Paths

```
+------------------------------------------------------------------+
|  Routing Configuration - [Router Name]                           |
+------------------------------------------------------------------+
|                                                                   |
|                    +---------------------+                        |
|                    |   Intent Router     |                        |
|                    |   [Router]          |                        |
|                    +---------------------+                        |
|                             |                                     |
|     +-----------------------+------------------------+            |
|     |                       |                        |            |
|  [order_*]            [support_*]              [billing_*]        |
|     |                       |                        |            |
|     v                       v                        v            |
| +-----------+        +-----------+           +-----------+        |
| | Order     |        | Support   |           | Billing   |        |
| | Handler   |        | Handler   |           | Handler   |        |
| +-----------+        +-----------+           +-----------+        |
|                                                                   |
|  Routing Statistics (Last 7 days)                                |
|  +--------------------------------------------------------------+|
|  | Route Pattern  | Target Agent   | Matches | % of Total       ||
|  |----------------|----------------|---------|------------------|
|  | order_*        | Order Handler  | 4,521   | 42%  [========]  ||
|  | support_*      | Support Handler| 3,892   | 36%  [=======]   ||
|  | billing_*      | Billing Handler| 2,341   | 22%  [====]      ||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

### Type-Specific Border Colors

```tsx
const typeColors = {
  orchestrator: {
    border: 'border-violet-400',
    badge: 'bg-violet-100 text-violet-700',
    bg: 'bg-violet-50'
  },
  router: {
    border: 'border-orange-400',
    badge: 'bg-orange-100 text-orange-700',
    bg: 'bg-orange-50'
  },
  worker: {
    border: 'border-blue-400',
    badge: 'bg-blue-100 text-blue-700',
    bg: 'bg-blue-50'
  },
  tool: {
    border: 'border-emerald-400',
    badge: 'bg-emerald-100 text-emerald-700',
    bg: 'bg-emerald-50'
  },
  memory: {
    border: 'border-pink-400',
    badge: 'bg-pink-100 text-pink-700',
    bg: 'bg-pink-50'
  }
};
```

---

## 3. Execution Trace Improvements

### Execution Detail View

```
+------------------------------------------------------------------+
|  Execution: exec_a1b2c3d4                      [Copy ID] [Export]|
|  Workflow: Order Processing Pipeline                              |
|  Started: Jan 2, 2026 14:23:45 | Duration: 3.2s | Status: Success|
+------------------------------------------------------------------+
|                                                                   |
|  [Timeline] [Call Tree] [Data Flow] [Costs]                      |
|  ----------------------------------------------------------------|
|                                                                   |
|  TIMELINE VIEW                                                    |
|  ----------------------------------------------------------------|
|  0s         1s         2s         3s         3.2s                |
|  |----------|----------|----------|----------|                   |
|                                                                   |
|  Order Processor (Orchestrator)                                   |
|  [================================================] 3.2s          |
|    |                                                              |
|    +-- Validator (Worker)                                         |
|        [=======] 0.8s                                             |
|    |                                                              |
|    +-- Price Calculator (Worker)    Inventory Check (Tool)        |
|        [============] 1.2s          [====] 0.4s     <- parallel   |
|    |                                                              |
|    +-- Format Output (Tool)                                       |
|        [===] 0.3s                                                 |
|                                                                   |
+------------------------------------------------------------------+
```

### Call Tree View

```
+------------------------------------------------------------------+
|  CALL TREE VIEW                                                   |
|  ----------------------------------------------------------------|
|                                                                   |
|  [v] Order Processor (Orchestrator)              3.2s    $0.031  |
|      |                                                            |
|      +-- [v] Validator (Worker)                  0.8s    $0.008  |
|      |       Input: { order_id: "4521", items: [...] }            |
|      |       Output: { valid: true, warnings: [] }                |
|      |                                                            |
|      +-- [>] Price Calculator (Worker)           1.2s    $0.012  |
|      |       (click to expand)                                    |
|      |                                                            |
|      +-- [>] Inventory Check (Tool)              0.4s    $0.004  |
|      |       (click to expand)                                    |
|      |                                                            |
|      +-- [v] Format Output (Tool)                0.3s    $0.007  |
|              Input: { order: {...}, pricing: {...} }              |
|              Output: { formatted_order: "..." }                   |
|                                                                   |
+------------------------------------------------------------------+
|  Legend: [v] Expanded  [>] Collapsed  | Click to toggle          |
+------------------------------------------------------------------+
```

### Cost Attribution View

```
+------------------------------------------------------------------+
|  COST BREAKDOWN                                                   |
|  ----------------------------------------------------------------|
|                                                                   |
|  Total Cost: $0.031              Total Tokens: 4,892              |
|                                                                   |
|  By Agent:                                                        |
|  +--------------------------------------------------------------+|
|  | Agent              | Input Tk | Output Tk | Cost    | %      ||
|  |--------------------|----------|-----------|---------|--------|
|  | Order Processor    | 1,240    | 380       | $0.012  | 39%    ||
|  | Price Calculator   | 890      | 520       | $0.008  | 26%    ||
|  | Validator          | 650      | 290       | $0.006  | 19%    ||
|  | Format Output      | 420      | 380       | $0.005  | 16%    ||
|  | Inventory Check    | 82       | 40        | $0.000  | <1%    ||
|  |--------------------|----------|-----------|---------|--------|
|  | TOTAL              | 3,282    | 1,610     | $0.031  | 100%   ||
|  +--------------------------------------------------------------+|
|                                                                   |
+------------------------------------------------------------------+
```

---

## 4. Agent Relationship Graph

### Global Agent Network View

```
+------------------------------------------------------------------+
|  Agent Relationship Graph                    [Fullscreen] [Reset]|
+------------------------------------------------------------------+
|  Filters: [Type v] [Workflow v] [Connected to v]    [Search...]  |
+------------------------------------------------------------------+
|                                                                   |
|                     +-------------+                               |
|                     | Main Orch   |                               |
|                     | [violet]    |                               |
|                     +-------------+                               |
|                    /       |       \                              |
|                   /        |        \                             |
|      +-----------+   +-----------+   +-----------+                |
|      | Router A  |   | Router B  |   | Worker 1  |                |
|      | [orange]  |   | [orange]  |   | [blue]    |                |
|      +-----------+   +-----------+   +-----------+                |
|       /    |    \          |              |                       |
|      /     |     \         |              |                       |
| +------+ +------+ +------+ +------+  +--------+                   |
| |Wrk 2 | |Wrk 3 | |Wrk 4 | |Wrk 5 |  |Tool A  |                   |
| |[blue]| |[blue]| |[blue]| |[blue]|  |[green] |                   |
| +------+ +------+ +------+ +------+  +--------+                   |
|                                                                   |
+------------------------------------------------------------------+
|  Selected: Router A                                               |
|  Type: Router | Workflows: 3 | Connections: 5 | Executions: 2.4K |
|  [View Dashboard] [View in Workflow Canvas] [Configure]          |
+------------------------------------------------------------------+
```

### Graph Interaction Patterns

```
INTERACTIONS:
- Click node: Select and show details panel
- Double-click node: Navigate to agent dashboard
- Drag node: Reposition in graph
- Scroll: Zoom in/out
- Click + drag canvas: Pan view
- Right-click node: Context menu (View, Edit, Duplicate, Delete)

VISUAL INDICATORS:
- Node size: Based on execution volume
- Edge thickness: Based on call frequency
- Edge style:
  - Solid: Direct orchestration
  - Dashed: Routing path
  - Dotted: Tool usage
- Glow effect: Currently executing
- Pulse animation: Recent activity
```

---

## 5. Component Specifications

### A. Agent Dashboard Page Component

```tsx
// File: components/agents/agent-dashboard.tsx

interface AgentDashboardProps {
  agentId: string;
}

export function AgentDashboard({ agentId }: AgentDashboardProps) {
  const { agent, isLoading } = useAgent(agentId);
  const { metrics } = useAgentMetrics(agentId);
  const { executions } = useAgentExecutions(agentId);

  if (isLoading) return <AgentDashboardSkeleton />;

  return (
    <div className="flex flex-col gap-8 p-6">
      {/* Header */}
      <AgentHeader agent={agent} />

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard
          title="Total Executions"
          value={metrics.totalExecutions}
          trend={metrics.executionsTrend}
          icon={<ActivityIcon />}
        />
        <MetricCard
          title="Success Rate"
          value={`${metrics.successRate}%`}
          trend={metrics.successRateTrend}
          icon={<CheckCircleIcon />}
        />
        <MetricCard
          title="Avg Duration"
          value={formatDuration(metrics.avgDuration)}
          trend={metrics.durationTrend}
          icon={<ClockIcon />}
        />
        <MetricCard
          title="Tokens Used"
          value={formatNumber(metrics.tokensUsed)}
          subtitle="This month"
          icon={<CoinsIcon />}
        />
        <MetricCard
          title="Avg Cost/Run"
          value={formatCurrency(metrics.avgCost)}
          trend={metrics.costTrend}
          icon={<DollarSignIcon />}
        />
        <MetricCard
          title="Active Workflows"
          value={metrics.activeWorkflows}
          icon={<WorkflowIcon />}
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="executions">
        <TabsList>
          <TabsTrigger value="executions">Executions</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          {agent.type === 'orchestrator' && (
            <TabsTrigger value="sub-agents">Sub-Agents</TabsTrigger>
          )}
          {agent.type === 'router' && (
            <TabsTrigger value="routing">Routing</TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="executions">
          <ExecutionHistoryTable agentId={agentId} />
        </TabsContent>

        <TabsContent value="logs">
          <AgentLogsViewer agentId={agentId} />
        </TabsContent>

        <TabsContent value="performance">
          <AgentPerformanceCharts agentId={agentId} />
        </TabsContent>

        {agent.type === 'orchestrator' && (
          <TabsContent value="sub-agents">
            <SubAgentHierarchy orchestratorId={agentId} />
          </TabsContent>
        )}

        {agent.type === 'router' && (
          <TabsContent value="routing">
            <RouterPathsVisualization routerId={agentId} />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
```

### B. Hierarchy Visualization Component

```tsx
// File: components/agents/sub-agent-hierarchy.tsx

interface SubAgentHierarchyProps {
  orchestratorId: string;
}

export function SubAgentHierarchy({ orchestratorId }: SubAgentHierarchyProps) {
  const { hierarchy, isLoading } = useAgentHierarchy(orchestratorId);
  const [viewMode, setViewMode] = useState<'tree' | 'list'>('tree');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Sub-Agents Hierarchy</h3>
        <ToggleGroup value={viewMode} onValueChange={setViewMode}>
          <ToggleGroupItem value="tree">
            <NetworkIcon className="h-4 w-4 mr-2" />
            Tree
          </ToggleGroupItem>
          <ToggleGroupItem value="list">
            <ListIcon className="h-4 w-4 mr-2" />
            List
          </ToggleGroupItem>
        </ToggleGroup>
      </div>

      {viewMode === 'tree' ? (
        <div className="h-[400px] border rounded-lg bg-slate-50 dark:bg-slate-900">
          <ReactFlow
            nodes={hierarchyToNodes(hierarchy)}
            edges={hierarchyToEdges(hierarchy)}
            nodeTypes={{ agentNode: AgentHierarchyNode }}
            fitView
            panOnDrag
            zoomOnScroll
          >
            <Background variant="dots" />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
      ) : (
        <SubAgentListView hierarchy={hierarchy} />
      )}

      <Card>
        <CardHeader>
          <CardTitle>Sub-Agent Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <SubAgentStatsTable agents={flattenHierarchy(hierarchy)} />
        </CardContent>
      </Card>
    </div>
  );
}
```

### C. Supporting Utility Components

```tsx
// File: components/agents/shared/status-badge.tsx
export function StatusBadge({ status }: { status: ExecutionStatus }) {
  const config = {
    success: { label: 'Success', class: 'bg-emerald-100 text-emerald-700' },
    error: { label: 'Error', class: 'bg-red-100 text-red-700' },
    running: { label: 'Running', class: 'bg-blue-100 text-blue-700' },
    cancelled: { label: 'Cancelled', class: 'bg-slate-100 text-slate-700' },
    pending: { label: 'Pending', class: 'bg-amber-100 text-amber-700' }
  };

  return (
    <Badge variant="secondary" className={config[status].class}>
      {config[status].label}
    </Badge>
  );
}

// File: components/agents/shared/metric-card.tsx
export function MetricCard({ title, value, subtitle, trend, icon }: MetricCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
            )}
            {trend && (
              <div className={cn(
                "flex items-center gap-1 mt-2 text-sm",
                trend.direction === 'up' && trend.isPositive ? "text-emerald-600" : "",
                trend.direction === 'down' && !trend.isPositive ? "text-red-600" : ""
              )}>
                {trend.direction === 'up' ? (
                  <ArrowUpIcon className="h-4 w-4" />
                ) : (
                  <ArrowDownIcon className="h-4 w-4" />
                )}
                <span>{trend.value}% {trend.label}</span>
              </div>
            )}
          </div>
          {icon && (
            <div className="p-2 bg-muted rounded-lg">
              {icon}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Sprint 1 - Days 1-3)

| Task | Component | Priority |
|------|-----------|----------|
| Create agent dashboard route | `/agents/[agentId]/page.tsx` | High |
| Build MetricCard component | Shared component | High |
| Build StatusBadge component | Shared component | High |
| Set up agent metrics API | `/api/agents/[id]/metrics` | High |
| Create execution history table | Tab component | High |

### Phase 2: Core Visualizations (Sprint 1 - Days 4-6)

| Task | Component | Priority |
|------|-----------|----------|
| Build hierarchy visualization | Sub-agent hierarchy | High |
| Create execution timeline | Timeline view | High |
| Implement call tree view | Call tree component | Medium |
| Add agent-specific logs | Logs viewer | Medium |

### Phase 3: Advanced Features (Sprint 2)

| Task | Component | Priority |
|------|-----------|----------|
| Build relationship graph | Full graph view | High |
| Add data flow visualization | Data flow view | Medium |
| Implement cost breakdown | Cost attribution | Medium |
| Add routing paths for routers | Router visualization | Medium |
| Performance charts | Charts component | Low |

### Phase 4: Polish (Sprint 3)

| Task | Component | Priority |
|------|-----------|----------|
| Add filtering and search | All views | Medium |
| Export functionality | Traces, logs | Low |
| Real-time updates | WebSocket integration | Medium |
| Mobile responsiveness | All components | Medium |
| Accessibility audit | All components | High |

---

## 7. Technical Notes

### API Endpoints Required

```typescript
// Agent Metrics
GET /api/agents/:id/metrics
Response: {
  totalExecutions: number;
  successRate: number;
  avgDuration: number;
  tokensUsed: number;
  avgCost: number;
  activeWorkflows: number;
  trends: { ... };
}

// Agent Executions
GET /api/agents/:id/executions
Query: { page, limit, status, workflowId, dateFrom, dateTo }
Response: {
  executions: ExecutionSummary[];
  total: number;
  page: number;
}

// Agent Logs
GET /api/agents/:id/logs
Query: { level, executionId, from, to, search }
Response: {
  logs: LogEntry[];
  cursor: string;
}

// Agent Hierarchy (for orchestrators)
GET /api/agents/:id/hierarchy
Response: {
  root: HierarchyNode;
  stats: SubAgentStats[];
}

// Execution Trace
GET /api/executions/:id/trace
Response: {
  executionId: string;
  workflowId: string;
  workflowName: string;
  status: ExecutionStatus;
  startTime: string;
  endTime?: string;
  spans: ExecutionSpan[];
  totalCost: number;
  totalTokens: number;
}

// Agent Relationships (for graph)
GET /api/agents/relationships
Query: { types[], workflows[], connectedTo }
Response: {
  agents: AgentNode[];
  relationships: Relationship[];
}
```

### Data Models

```typescript
interface Agent {
  id: string;
  name: string;
  type: 'orchestrator' | 'router' | 'worker' | 'tool' | 'memory';
  description?: string;
  config: Record<string, any>;
  subAgentIds?: string[];  // for orchestrators
  routingRules?: RoutingRule[];  // for routers
  createdAt: Date;
  updatedAt: Date;
}

interface ExecutionSpan {
  id: string;
  executionId: string;
  agentId: string;
  agentName: string;
  agentType: AgentType;
  parentSpanId?: string;
  startTime: number;  // ms offset from execution start
  endTime: number;
  status: 'success' | 'error' | 'running';
  input?: any;
  output?: any;
  error?: string;
  tokens: {
    input: number;
    output: number;
  };
  cost: number;
}

interface Relationship {
  sourceId: string;
  targetId: string;
  type: 'orchestration' | 'routing' | 'tool';
  routePattern?: string;
  callFrequency: number;
  isActive: boolean;
}
```

### Performance Considerations

1. **Virtualization**: Use `@tanstack/react-virtual` for large execution lists
2. **Memoization**: Heavily memoize graph nodes/edges to prevent re-renders
3. **Pagination**: Default to 50 items per page, lazy load more
4. **Caching**: Cache agent metrics for 30s, refresh on focus
5. **WebSocket**: Use for real-time execution status, not polling
6. **Graph Layout**: Use `dagre` for automatic layout, cache positions

### Accessibility Requirements

- All interactive elements keyboard navigable
- ARIA labels on graph nodes
- Screen reader announcements for status changes
- Color not sole indicator of status (use icons)
- Minimum contrast ratios: 4.5:1 for text, 3:1 for UI
- Focus indicators on all interactive elements

---

*Document Version: 1.0*
*Last Updated: January 2, 2026*
*Author: UI Design Agent*

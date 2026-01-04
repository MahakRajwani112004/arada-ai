# Agent Details - Overview Tab UX Specification

**Version:** 1.0
**Date:** January 2026
**Status:** Design Proposal

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [User Personas & Goals](#2-user-personas--goals)
3. [Information Architecture](#3-information-architecture)
4. [Wireframes](#4-wireframes)
5. [Component Specifications](#5-component-specifications)
6. [Data Requirements](#6-data-requirements)
7. [Empty States](#7-empty-states)
8. [Responsive Behavior](#8-responsive-behavior)
9. [Implementation Recommendations](#9-implementation-recommendations)

---

## 1. Executive Summary

### 1.1 Problem Statement

The current Agent Details page only offers Chat and Edit modes, leaving users without visibility into:
- How their agent is performing
- What users are asking the agent
- Where failures occur
- Cost and resource consumption

### 1.2 Solution

Add an **Overview tab** that provides at-a-glance performance insights, usage patterns, and actionable diagnostics. The design follows the principle of **progressive disclosure**: surface critical metrics prominently while enabling drill-down for detailed analysis.

### 1.3 Design Principles

| Principle | Application |
|-----------|-------------|
| **Glanceable** | Key metrics visible in < 3 seconds |
| **Actionable** | Every insight suggests a next step |
| **Persona-Aware** | Different users find what they need quickly |
| **Minimal** | Show 5 metrics prominently, not 50 |
| **Contextual** | Compare to baselines, show trends |

---

## 2. User Personas & Goals

### 2.1 Developer ("Alex") - Debugging Agent Issues

**Primary Goals:**
- Quickly identify if the agent is healthy or broken
- Find specific errors and their root causes
- Understand latency bottlenecks
- See which tool calls are failing

**Key Questions:**
- "Why is this agent failing?"
- "Which errors are most common?"
- "Is latency acceptable?"
- "What was the exact error message?"

**Priority Metrics:**
1. Success Rate (with error breakdown)
2. Error log with stack traces
3. Latency distribution (P50, P95, P99)
4. Tool call success rates

### 2.2 Product Manager ("Sarah") - Checking Agent Usage

**Primary Goals:**
- Understand how users interact with the agent
- Identify popular use cases
- Track adoption over time
- Justify investment in the agent

**Key Questions:**
- "How many people are using this agent?"
- "What are they asking it to do?"
- "Is usage growing or declining?"
- "Are users satisfied?"

**Priority Metrics:**
1. Total Executions (with trend)
2. Top Asks / Common Queries
3. Usage over time chart
4. Active users count

### 2.3 Operations ("Mike") - Monitoring Performance

**Primary Goals:**
- Monitor system health at a glance
- Track costs and resource usage
- Identify performance degradation
- Ensure SLA compliance

**Key Questions:**
- "Is this agent costing too much?"
- "Are response times within SLA?"
- "Any unusual spikes or drops?"
- "Do I need to scale?"

**Priority Metrics:**
1. Cost (total and per-execution)
2. Latency trends
3. Throughput (executions/hour)
4. LLM token usage

---

## 3. Information Architecture

### 3.1 Tab Structure

```
Agent Details Page
+---------------------------------------------------------------+
| [Overview]    [Chat]    [Edit]    [Settings]                  |
+---------------------------------------------------------------+
```

### 3.2 Overview Tab Hierarchy

**Above the Fold** (visible without scrolling on 1080p):
1. Quick Stats Cards (4 cards)
2. Usage Trend Chart (sparkline or area chart)

**Below the Fold** (scrollable):
3. Top Asks Section
4. Recent Executions List
5. Error Breakdown (conditional - only if errors exist)

### 3.3 Visual Hierarchy

```
+---------------------------------------------------------------+
|                    ABOVE THE FOLD                              |
+---------------------------------------------------------------+
|                                                                |
|  [PRIMARY STATS - 4 Cards]                                     |
|  +-------------+ +-------------+ +-------------+ +-------------+
|  | Executions  | | Success     | | Avg Latency | | Total Cost  |
|  | 1,247       | | Rate        | | 1.2s        | | $12.45      |
|  | +12% ^      | | 94.2%       | | -8% v       | | +5% ^       |
|  +-------------+ +-------------+ +-------------+ +-------------+
|                                                                |
|  [USAGE TREND - Area Chart]                                    |
|  +----------------------------------------------------------+  |
|  |    ___/\___/\___     Executions over time                |  |
|  |   /            \___  Last 7 days | 30 days | 90 days     |  |
|  +----------------------------------------------------------+  |
|                                                                |
+---------------------------------------------------------------+
|                    BELOW THE FOLD                              |
+---------------------------------------------------------------+
|                                                                |
|  [TOP ASKS]                        [RECENT EXECUTIONS]         |
|  +---------------------------+     +---------------------------+
|  | 1. "Schedule a meeting"  |     | 2 min ago - Success       |
|  |    23% of queries        |     | "Draft email to..."       |
|  | 2. "Send email to..."    |     |                           |
|  |    18% of queries        |     | 5 min ago - Failed        |
|  | 3. "Check my calendar"   |     | "Find documents..."       |
|  |    15% of queries        |     |                           |
|  +---------------------------+     +---------------------------+
|                                                                |
|  [ERROR BREAKDOWN] (only shown if errors > 0)                  |
|  +----------------------------------------------------------+  |
|  | Tool Timeout     |========         | 45% (23 errors)     |  |
|  | Auth Failed      |====             | 25% (13 errors)     |  |
|  | Invalid Input    |===              | 18% (9 errors)      |  |
|  | LLM Error        |==               | 12% (6 errors)      |  |
|  +----------------------------------------------------------+  |
|                                                                |
+---------------------------------------------------------------+
```

---

## 4. Wireframes

### 4.1 Desktop View (1440px+)

```
+-----------------------------------------------------------------------+
| MagOneAI                                    [Search]  [?]  [Profile]  |
+-----------------------------------------------------------------------+
| < Back to Agents                                                       |
|                                                                        |
| +------------------------------------------------------------------+  |
| |                                                                  |  |
| |  Sales Assistant                                    [Edit] [Chat]|  |
| |  Handles outreach, follow-ups, and pipeline activities          |  |
| |                                                                  |  |
| +------------------------------------------------------------------+  |
|                                                                        |
| +------------------------------------------------------------------+  |
| | [Overview]     [Chat]      [Edit]      [Logs]      [Settings]    |  |
| +------------------------------------------------------------------+  |
|                                                                        |
| +------------------------------------------------------------------+  |
| |  PERFORMANCE OVERVIEW                     Time Range: [Last 7d v]|  |
| +------------------------------------------------------------------+  |
|                                                                        |
| +---------------+ +---------------+ +---------------+ +---------------+|
| | EXECUTIONS    | | SUCCESS RATE  | | AVG LATENCY   | | TOTAL COST   ||
| |               | |               | |               | |              ||
| |    1,247      | |    94.2%      | |    1.2s       | |   $12.45     ||
| |               | |               | |               | |              ||
| | [====] +12%   | | [=========-]  | | [====] -8%    | | [===] +5%    ||
| | vs last week  | | 73 failures   | | vs last week  | | vs last week ||
| +---------------+ +---------------+ +---------------+ +---------------+|
|                                                                        |
| +------------------------------------------------------------------+  |
| |  USAGE OVER TIME                                                  |  |
| |                                                                   |  |
| |  150 |                    .                                       |  |
| |      |        .   .    . . .    .                                |  |
| |  100 |   . .   . . .  .     .  . .   .                           |  |
| |      |  .   . .     ..       ..   . . .    .                     |  |
| |   50 | .                              . .. . .  .                |  |
| |      |                                         . .               |  |
| |    0 +---------------------------------------------------        |  |
| |        Mon   Tue   Wed   Thu   Fri   Sat   Sun                   |  |
| |                                                                   |  |
| |  --- Executions  ... Failures                                    |  |
| +------------------------------------------------------------------+  |
|                                                                        |
| +-------------------------------+  +-------------------------------+   |
| | TOP ASKS                      |  | RECENT EXECUTIONS             |   |
| | What users ask most often     |  | Latest activity               |   |
| +-------------------------------+  +-------------------------------+   |
| |                               |  |                               |   |
| | 1. "Schedule a meeting..."   |  | [OK] 2 min ago    1.1s        |   |
| |    [=======-------] 23%      |  | "Draft email to the team..."  |   |
| |    142 requests              |  | Tool: gmail:draft             |   |
| |                               |  +-------------------------------+   |
| | 2. "Send email to..."        |  | [X] 5 min ago     Timeout     |   |
| |    [=====----------] 18%     |  | "Find all documents from..."  |   |
| |    112 requests              |  | Error: google-drive timeout   |   |
| |                               |  +-------------------------------+   |
| | 3. "Check my calendar"       |  | [OK] 8 min ago    0.9s        |   |
| |    [=====-----------] 15%    |  | "What meetings do I have..."  |   |
| |    93 requests               |  | Tool: google-calendar:list    |   |
| |                               |  +-------------------------------+   |
| | 4. "Summarize this doc..."   |  | [OK] 12 min ago   2.3s        |   |
| |    [===-------------] 12%    |  | "Review the attached NDA..."  |   |
| |    74 requests               |  | Tool: document-analysis       |   |
| |                               |  +-------------------------------+   |
| | 5. "Draft a response to..."  |  |                               |   |
| |    [===-------------] 11%    |  | [View All Executions ->]      |   |
| |    68 requests               |  |                               |   |
| +-------------------------------+  +-------------------------------+   |
|                                                                        |
| +------------------------------------------------------------------+  |
| | ERROR BREAKDOWN                                                   |  |
| | 73 total errors in the last 7 days                               |  |
| +------------------------------------------------------------------+  |
| |                                                                   |  |
| | Tool Timeout                                                      |  |
| | [================================---------] 45% (33 errors)       |  |
| | Most affected: google-drive:search, slack:list_channels          |  |
| |                                                                   |  |
| | Authentication Failed                                             |  |
| | [===================-------------------] 25% (18 errors)          |  |
| | Token expired for: google-calendar                                |  |
| |                                                                   |  |
| | Invalid Input                                                     |  |
| | [===============-----------------------] 18% (13 errors)          |  |
| | Common: Missing email recipient, Invalid date format              |  |
| |                                                                   |  |
| | LLM Error                                                         |  |
| | [============--------------------------] 12% (9 errors)           |  |
| | Rate limit exceeded (3), Context too long (6)                     |  |
| |                                                                   |  |
| +------------------------------------------------------------------+  |
|                                                                        |
+-----------------------------------------------------------------------+
```

### 4.2 Stats Card Detailed Wireframe

```
+------------------------------------------+
|  EXECUTIONS                              |
|                                          |
|         1,247                            |   <- Primary metric (large)
|                                          |
|  +--+--+--+--+--+--+--+                  |   <- Sparkline (last 7 days)
|  |  |##|##|  |##|##|##|                  |
|  +--+--+--+--+--+--+--+                  |
|                                          |
|  [^] +12% vs last 7 days                |   <- Comparison (green/red)
|                                          |
+------------------------------------------+

States:
- Positive trend: Green arrow up, green text
- Negative trend: Red arrow down, red text
- Neutral: Gray dash, gray text
- Loading: Skeleton pulse animation
- Error: "Failed to load" with retry button
```

### 4.3 Success Rate Card (Special Treatment)

```
+------------------------------------------+
|  SUCCESS RATE                            |
|                                          |
|         94.2%                            |   <- Primary percentage
|                                          |
|  [========================------]        |   <- Progress bar
|   1,174 succeeded    73 failed           |   <- Counts below
|                                          |
|  [-] -2.1% vs last 7 days               |   <- Comparison (red = worse)
|                                          |
+------------------------------------------+

Color coding:
- > 95%: Green bar
- 90-95%: Yellow bar
- < 90%: Red bar
```

### 4.4 Top Asks Section Wireframe

```
+--------------------------------------------------+
|  TOP ASKS                            [View All >]|
|  What users ask most often                       |
+--------------------------------------------------+
|                                                  |
|  1  "Schedule a meeting with..."                 |
|     [===========================-------] 23%     |
|     142 requests  |  Avg 1.2s  |  98% success    |
|                                                  |
+--------------------------------------------------+
|                                                  |
|  2  "Send email to..."                           |
|     [======================------------] 18%     |
|     112 requests  |  Avg 1.8s  |  92% success    |
|                                                  |
+--------------------------------------------------+
|                                                  |
|  3  "Check my calendar for..."                   |
|     [==================----------------] 15%     |
|     93 requests   |  Avg 0.9s  |  99% success    |
|                                                  |
+--------------------------------------------------+
|                                                  |
|  4  "Summarize this document..."                 |
|     [===============-------------------] 12%     |
|     74 requests   |  Avg 3.2s  |  85% success    |
|                                                  |
+--------------------------------------------------+
|                                                  |
|  5  "Draft a response to..."                     |
|     [==============--------------------] 11%     |
|     68 requests   |  Avg 2.1s  |  91% success    |
|                                                  |
+--------------------------------------------------+
```

### 4.5 Recent Executions List Wireframe

```
+----------------------------------------------------------+
|  RECENT EXECUTIONS                          [View All >] |
|  Latest activity                                          |
+----------------------------------------------------------+
|                                                           |
|  [OK]  2 minutes ago                             1.1s    |
|  +------------------------------------------------+      |
|  | "Draft an email to the team about tomorrow's   |      |
|  | meeting and include the agenda..."             |      |
|  +------------------------------------------------+      |
|  Tools: gmail:draft                                       |
|  Tokens: 1,234 prompt / 456 completion                    |
|                                                           |
+----------------------------------------------------------+
|                                                           |
|  [X]   5 minutes ago                           Timeout   |
|  +------------------------------------------------+      |
|  | "Find all documents from Q4 planning that      |      |
|  | mention budget allocations..."                 |      |
|  +------------------------------------------------+      |
|  Error: google-drive:search timed out after 30s          |
|  [View Details] [Retry]                                  |
|                                                           |
+----------------------------------------------------------+
|                                                           |
|  [OK]  8 minutes ago                             0.9s    |
|  +------------------------------------------------+      |
|  | "What meetings do I have scheduled for this    |      |
|  | Thursday afternoon?"                           |      |
|  +------------------------------------------------+      |
|  Tools: google-calendar:list_events                       |
|  Tokens: 856 prompt / 234 completion                      |
|                                                           |
+----------------------------------------------------------+

Status indicators:
[OK]  = Green checkmark circle
[X]   = Red X circle
[!]   = Yellow warning triangle (partial failure)
[...] = Gray spinner (in progress)
```

### 4.6 Error Breakdown Section Wireframe

```
+---------------------------------------------------------------+
|  ERROR BREAKDOWN                                               |
|  73 total errors in the last 7 days    [View Error Logs >]    |
+---------------------------------------------------------------+
|                                                                |
|  Tool Timeout                                      33 errors   |
|  [================================================] 45%        |
|  +------------------------------------------------------------+
|  | Most affected tools:                                       |
|  | - google-drive:search (18 timeouts)                        |
|  | - slack:list_channels (12 timeouts)                        |
|  | - notion:search (3 timeouts)                               |
|  |                                               [Expand v]   |
|  +------------------------------------------------------------+
|                                                                |
|  Authentication Failed                             18 errors   |
|  [==============================------------------] 25%        |
|  +------------------------------------------------------------+
|  | Affected integrations:                                     |
|  | - google-calendar: Token expired                           |
|  |   [Reconnect Integration]                                  |
|  +------------------------------------------------------------+
|                                                                |
|  Invalid Input                                     13 errors   |
|  [========================------------------------] 18%        |
|  +------------------------------------------------------------+
|  | Common issues:                                             |
|  | - Missing email recipient (7)                              |
|  | - Invalid date format (4)                                  |
|  | - Empty message body (2)                                   |
|  +------------------------------------------------------------+
|                                                                |
|  LLM Error                                          9 errors   |
|  [===================-----------------------------] 12%        |
|  +------------------------------------------------------------+
|  | Breakdown:                                                 |
|  | - Context too long (6) - Consider chunking                 |
|  | - Rate limit exceeded (3) - Usage spike detected           |
|  +------------------------------------------------------------+
|                                                                |
+---------------------------------------------------------------+
```

---

## 5. Component Specifications

### 5.1 StatCard Component

```typescript
interface StatCardProps {
  title: string;
  value: string | number;
  format?: 'number' | 'percentage' | 'currency' | 'duration';
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
    label: string;  // e.g., "vs last 7 days"
  };
  sparkline?: number[];  // 7 data points for mini chart
  status?: 'success' | 'warning' | 'error' | 'neutral';
  loading?: boolean;
  error?: string;
  onClick?: () => void;
}
```

**Visual States:**
- Default: White background, subtle border
- Hover: Slight shadow, cursor pointer (if clickable)
- Loading: Skeleton pulse animation
- Error: Error message with retry button

### 5.2 UsageChart Component

```typescript
interface UsageChartProps {
  data: {
    date: string;
    executions: number;
    failures: number;
    successRate: number;
  }[];
  timeRange: '7d' | '30d' | '90d';
  onTimeRangeChange: (range: string) => void;
  loading?: boolean;
}
```

**Chart Type Recommendation:** Area chart with Recharts
- Primary line: Executions (solid blue fill)
- Secondary line: Failures (dashed red line)
- Tooltip: Show date, count, and success rate
- Interactive: Hover shows exact values

### 5.3 TopAsks Component

```typescript
interface TopAsksProps {
  items: {
    id: string;
    pattern: string;           // Summarized query pattern
    exampleQuery: string;      // Actual example
    count: number;
    percentage: number;
    avgLatency: number;
    successRate: number;
  }[];
  total: number;
  loading?: boolean;
  onViewAll?: () => void;
}
```

**Pattern Extraction Logic:**
To generate "Top Asks," we need to cluster similar queries. Recommended approach:
1. Use embeddings to group semantically similar inputs
2. Extract intent patterns (e.g., "schedule meeting", "send email")
3. Store aggregated patterns with counts

### 5.4 RecentExecutions Component

```typescript
interface RecentExecutionsProps {
  executions: {
    id: string;
    timestamp: Date;
    status: 'success' | 'error' | 'partial' | 'running';
    inputPreview: string;      // First 100 chars of input
    latencyMs: number | null;
    toolsUsed: string[];
    tokens?: {
      prompt: number;
      completion: number;
    };
    error?: {
      type: string;
      message: string;
    };
  }[];
  loading?: boolean;
  onViewAll?: () => void;
  onRetry?: (id: string) => void;
  onViewDetails?: (id: string) => void;
}
```

### 5.5 ErrorBreakdown Component

```typescript
interface ErrorBreakdownProps {
  errors: {
    type: string;
    count: number;
    percentage: number;
    details: string;           // Actionable context
    affectedTools?: string[];
    suggestedAction?: {
      label: string;
      action: () => void;
    };
  }[];
  totalErrors: number;
  timeRange: string;
  loading?: boolean;
  onViewLogs?: () => void;
}
```

**Error Type Categories:**
| Error Type | Description | Suggested Action |
|------------|-------------|------------------|
| tool_timeout | Tool call exceeded timeout | Check tool health, increase timeout |
| auth_failed | Integration auth expired | Reconnect integration |
| invalid_input | User input validation failed | Improve input handling |
| llm_error | LLM API error | Check rate limits, context length |
| tool_error | Tool returned error | Check tool configuration |
| network_error | Connection issues | Check network, retry |

---

## 6. Data Requirements

### 6.1 Required API Endpoints

```yaml
# Agent Overview Stats
GET /api/v1/agents/{agent_id}/stats:
  parameters:
    - timeRange: "7d" | "30d" | "90d"
  response:
    totalExecutions: number
    successfulExecutions: number
    failedExecutions: number
    successRate: number
    avgLatencyMs: number
    totalCostCents: number
    trend:
      executions: number      # Percentage change
      successRate: number
      latency: number
      cost: number

# Usage Over Time
GET /api/v1/agents/{agent_id}/usage-history:
  parameters:
    - timeRange: "7d" | "30d" | "90d"
    - granularity: "hour" | "day" | "week"
  response:
    data:
      - date: string
        executions: number
        failures: number
        avgLatencyMs: number
        costCents: number

# Top Asks (requires input pattern tracking)
GET /api/v1/agents/{agent_id}/top-asks:
  parameters:
    - timeRange: "7d" | "30d" | "90d"
    - limit: number (default: 5)
  response:
    total: number
    patterns:
      - pattern: string
        exampleQuery: string
        count: number
        percentage: number
        avgLatencyMs: number
        successRate: number

# Recent Executions
GET /api/v1/agents/{agent_id}/executions:
  parameters:
    - limit: number (default: 10)
    - offset: number
    - status: "success" | "error" | "all"
  response:
    data:
      - id: string
        timestamp: string
        status: string
        inputPreview: string
        latencyMs: number
        toolsUsed: string[]
        promptTokens: number
        completionTokens: number
        costCents: number
        error: { type: string, message: string } | null

# Error Breakdown
GET /api/v1/agents/{agent_id}/error-breakdown:
  parameters:
    - timeRange: "7d" | "30d" | "90d"
  response:
    totalErrors: number
    breakdown:
      - errorType: string
        count: number
        percentage: number
        affectedTools: string[]
        suggestedAction: string
```

### 6.2 Database Query Examples

```sql
-- Agent Stats for Time Range
SELECT
    COUNT(*) as total_executions,
    SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failed,
    AVG(latency_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency
FROM agent_executions
WHERE agent_id = :agent_id
AND timestamp >= NOW() - INTERVAL :time_range;

-- Usage Over Time (Daily Granularity)
SELECT
    DATE_TRUNC('day', timestamp) as date,
    COUNT(*) as executions,
    SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failures,
    AVG(latency_ms) as avg_latency
FROM agent_executions
WHERE agent_id = :agent_id
AND timestamp >= NOW() - INTERVAL :time_range
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY date;

-- Error Breakdown
SELECT
    error_type,
    COUNT(*) as error_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    ARRAY_AGG(DISTINCT tool_name) as affected_tools
FROM agent_executions
WHERE agent_id = :agent_id
AND success = false
AND timestamp >= NOW() - INTERVAL :time_range
GROUP BY error_type
ORDER BY error_count DESC;

-- Total Cost from LLM Usage
SELECT
    SUM(cost_cents) as total_cost_cents,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens
FROM llm_usage
WHERE agent_id = :agent_id
AND timestamp >= NOW() - INTERVAL :time_range;
```

### 6.3 Top Asks Implementation

To track "Top Asks," we need to cluster user inputs. Two approaches:

**Approach A: Intent Classification (Recommended)**
```python
# Add intent classification during execution
class AgentExecutionWithIntent(AgentExecutionModel):
    # Existing fields...
    input_intent: str  # Classified intent: "schedule_meeting", "send_email", etc.
    input_preview: str  # First 100 chars of sanitized input

# Classification can be done:
# 1. Rule-based: Regex patterns for common intents
# 2. LLM-based: Quick classification call
# 3. Embedding-based: Cluster similar inputs
```

**Approach B: Real-time Clustering**
```python
# Cluster inputs on query using embeddings
async def get_top_asks(agent_id: str, time_range: str, limit: int = 5):
    # 1. Get recent execution inputs
    executions = await get_executions(agent_id, time_range)
    inputs = [e.input_preview for e in executions]

    # 2. Generate embeddings
    embeddings = await generate_embeddings(inputs)

    # 3. Cluster similar inputs
    clusters = cluster_embeddings(embeddings, n_clusters=limit)

    # 4. Extract representative pattern for each cluster
    patterns = []
    for cluster in clusters:
        representative = get_cluster_representative(cluster)
        pattern = summarize_intent(representative)
        patterns.append({
            "pattern": pattern,
            "count": len(cluster),
            "examples": cluster[:3]
        })

    return patterns
```

---

## 7. Empty States

### 7.1 No Data Yet (New Agent)

```
+------------------------------------------------------------------+
|                                                                  |
|                         [Illustration]                           |
|                    (Agent looking at empty charts)               |
|                                                                  |
|                    No activity yet                               |
|                                                                  |
|     This agent hasn't been used yet. Start a conversation        |
|     to see performance metrics appear here.                      |
|                                                                  |
|                    [Start Chatting ->]                           |
|                                                                  |
+------------------------------------------------------------------+
```

### 7.2 No Data for Time Range

```
+------------------------------------------------------------------+
|                                                                  |
|     No activity in the last 7 days                              |
|                                                                  |
|     This agent wasn't used during this period.                  |
|     Try selecting a different time range.                        |
|                                                                  |
|     [Last 30 days]  [Last 90 days]  [All time]                  |
|                                                                  |
+------------------------------------------------------------------+
```

### 7.3 No Errors (Good State!)

```
+------------------------------------------------------------------+
|  ERROR BREAKDOWN                                                 |
+------------------------------------------------------------------+
|                                                                  |
|                  [Checkmark illustration]                        |
|                                                                  |
|                    No errors detected                            |
|                                                                  |
|     Great news! This agent has run without errors               |
|     in the selected time period.                                 |
|                                                                  |
+------------------------------------------------------------------+
```

### 7.4 Loading State

```
+---------------+ +---------------+ +---------------+ +---------------+
| EXECUTIONS    | | SUCCESS RATE  | | AVG LATENCY   | | TOTAL COST   |
|               | |               | |               | |              |
| [===========] | | [===========] | | [===========] | | [===========]|
| [=======]     | | [=========]   | | [=======]     | | [========]   |
|               | |               | |               | |              |
+---------------+ +---------------+ +---------------+ +---------------+

(Skeleton loading animation with pulse effect)
```

### 7.5 Error State

```
+------------------------------------------------------------------+
|                                                                  |
|     [Warning icon]                                               |
|                                                                  |
|     Unable to load metrics                                       |
|                                                                  |
|     We couldn't fetch the performance data. This might be       |
|     a temporary issue.                                           |
|                                                                  |
|     [Retry]                [Contact Support]                     |
|                                                                  |
+------------------------------------------------------------------+
```

---

## 8. Responsive Behavior

### 8.1 Breakpoints

| Breakpoint | Layout |
|------------|--------|
| Desktop (1440px+) | 4-column stats, 2-column sections |
| Laptop (1024px) | 4-column stats, 2-column sections |
| Tablet (768px) | 2-column stats, stacked sections |
| Mobile (< 768px) | 1-column everything, simplified |

### 8.2 Mobile Layout

```
+----------------------------------+
| < Back    Sales Assistant   ... |
+----------------------------------+
| [Overview] [Chat] [Edit] [...]  |
+----------------------------------+
|                                  |
| Time Range: [Last 7 days v]     |
|                                  |
+----------------------------------+
| EXECUTIONS      | SUCCESS RATE  |
| 1,247           | 94.2%         |
| +12% vs prev    | 73 failures   |
+----------------------------------+
| AVG LATENCY     | TOTAL COST    |
| 1.2s            | $12.45        |
| -8% vs prev     | +5% vs prev   |
+----------------------------------+
|                                  |
| USAGE TREND                     |
| [Simplified sparkline chart]    |
|                                  |
+----------------------------------+
|                                  |
| TOP ASKS                        |
| 1. Schedule meeting... (23%)    |
| 2. Send email to... (18%)       |
| 3. Check calendar... (15%)      |
| [View All]                       |
|                                  |
+----------------------------------+
|                                  |
| RECENT ACTIVITY                 |
+----------------------------------+
| [OK] 2m ago                     |
| Draft email to the team...      |
+----------------------------------+
| [X] 5m ago                      |
| Find documents from Q4...       |
| Error: Timeout                  |
+----------------------------------+
| [View All Executions]           |
+----------------------------------+
```

### 8.3 Mobile Optimizations

1. **Collapse stat cards**: 2x2 grid instead of 4-column
2. **Simplify charts**: Sparklines instead of full area charts
3. **Truncate text**: Shorter previews (50 chars vs 100)
4. **Hide secondary metrics**: Show core stats, hide details
5. **Bottom sheet for details**: Tap to expand execution details

---

## 9. Implementation Recommendations

### 9.1 Recommended Chart Library

**Recharts** is recommended for this implementation:
- React-native with JSX-style API
- Lightweight and performant
- Good responsive support
- Built-in animations

```tsx
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function UsageChart({ data }: { data: UsageDataPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data}>
        <XAxis dataKey="date" tickFormatter={formatDate} />
        <YAxis />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="executions"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.2}
        />
        <Area
          type="monotone"
          dataKey="failures"
          stroke="#ef4444"
          fill="transparent"
          strokeDasharray="5 5"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
```

### 9.2 Data Fetching Strategy

Use React Query (TanStack Query) for data fetching:

```tsx
// hooks/useAgentStats.ts
export function useAgentStats(agentId: string, timeRange: string) {
  return useQuery({
    queryKey: ['agent-stats', agentId, timeRange],
    queryFn: () => fetchAgentStats(agentId, timeRange),
    staleTime: 1000 * 60,        // Consider fresh for 1 minute
    refetchInterval: 1000 * 60,  // Auto-refresh every minute
  });
}

// In component
const { data, isLoading, error } = useAgentStats(agentId, '7d');
```

### 9.3 Polling for Live Updates

For operations users monitoring in real-time:

```tsx
const { data } = useAgentStats(agentId, timeRange, {
  refetchInterval: isLiveMode ? 10000 : false,  // 10s when live
});
```

### 9.4 Performance Considerations

1. **Paginate executions list**: Load 10, then lazy load more
2. **Cache aggressively**: Stats don't change rapidly
3. **Debounce time range changes**: Wait 300ms before fetching
4. **Use suspense**: Show loading states gracefully
5. **Virtualize long lists**: If showing 100+ executions

### 9.5 Accessibility Requirements

1. **Color contrast**: All text meets WCAG AA (4.5:1 ratio)
2. **Screen reader**: All charts have aria-labels and descriptions
3. **Keyboard navigation**: All interactive elements focusable
4. **Color-blind safe**: Don't rely on color alone for status
5. **Reduce motion**: Respect prefers-reduced-motion

### 9.6 Component File Structure

```
src/
  components/
    agent-overview/
      index.tsx                    # Main Overview component
      stat-card.tsx                # Individual stat card
      usage-chart.tsx              # Usage over time chart
      top-asks.tsx                 # Top asks section
      recent-executions.tsx        # Execution list
      error-breakdown.tsx          # Error analysis
      empty-states.tsx             # All empty state variants

  hooks/
    use-agent-stats.ts             # Stats fetching hook
    use-agent-executions.ts        # Executions list hook
    use-agent-errors.ts            # Error breakdown hook
    use-top-asks.ts                # Top asks hook

  lib/
    api/
      agent-analytics.ts           # API client functions
```

---

## 10. Metrics Priority Summary

### 10.1 By Prominence (What to Show Where)

| Location | Metrics | Persona |
|----------|---------|---------|
| **Stats Cards (Primary)** | Executions, Success Rate, Avg Latency, Total Cost | All |
| **Chart (Secondary)** | Usage trend over time | PM, Ops |
| **Top Asks (Discovery)** | Query patterns | PM |
| **Recent Executions** | Latest activity with status | Dev, Ops |
| **Error Breakdown** | Failure categorization | Dev |

### 10.2 Chart Type Recommendations

| Data | Chart Type | Rationale |
|------|------------|-----------|
| Usage over time | Area chart | Shows volume and trend |
| Success rate | Progress bar | Easy percentage visualization |
| Error breakdown | Horizontal bars | Compare categories |
| Latency distribution | Histogram (optional) | For power users |
| Top asks | Progress bars with text | Show proportion |

### 10.3 What NOT to Show

To keep the overview minimal, deliberately exclude:
- Raw token counts (show cost instead)
- Individual LLM call details (keep in Logs tab)
- Full error stack traces (link to details)
- Configuration details (keep in Edit tab)
- Historical data beyond 90 days (archive separately)

---

## Appendix A: Color Palette

```css
/* Status Colors */
--success: #22c55e;      /* Green - Success states */
--warning: #f59e0b;      /* Amber - Warning states */
--error: #ef4444;        /* Red - Error states */
--neutral: #6b7280;      /* Gray - Neutral states */

/* Trend Colors */
--trend-up-good: #22c55e;    /* Green - Improvement */
--trend-up-bad: #ef4444;     /* Red - Increase in cost/errors */
--trend-down-good: #22c55e;  /* Green - Decrease in latency */
--trend-down-bad: #ef4444;   /* Red - Decrease in usage */

/* Chart Colors */
--chart-primary: #3b82f6;    /* Blue - Primary metric */
--chart-secondary: #8b5cf6;  /* Purple - Secondary metric */
--chart-failure: #ef4444;    /* Red - Failures line */
```

---

## Appendix B: Keyboard Shortcuts (Power Users)

| Shortcut | Action |
|----------|--------|
| `r` | Refresh data |
| `1-4` | Switch time range (7d, 30d, 90d, All) |
| `e` | Jump to error breakdown |
| `l` | Open full logs |
| `?` | Show keyboard shortcuts |

---

**Document Revision History:**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial specification |

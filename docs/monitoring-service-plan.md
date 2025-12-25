# Monitoring Service Implementation Plan

## Overview

Create a monitoring service with two components:
1. **Analytics** - KPIs for agents, workflows, LLM usage, costs, system metrics
2. **Logging** - Detailed operation logs with permanent retention

**Stack:** Prometheus + Grafana + Loki

---

## Key Design Principles

### 1. FOREVER STORAGE (Permanent Retention)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DUAL PERMANENT STORAGE STRATEGY                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LOKI (Logs) - retention_period: 0 = FOREVER                        │   │
│  │  • Raw log text (searchable)                                        │   │
│  │  • Use for: debugging, text search, tracing                         │   │
│  │  • Query: "Show errors containing 'timeout'"                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  POSTGRESQL (Analytics) - No auto-delete = FOREVER                  │   │
│  │  • Structured data (tokens, costs, latency)                         │   │
│  │  • Use for: reports, aggregations, dashboards                       │   │
│  │  • Query: "Total cost last month by model"                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BOTH are permanent. BOTH are backed up with your regular backups.         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. ZERO MANUAL LOGGING (Automatic via Choke Points)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              NO logger.info() IN YOUR BUSINESS CODE!                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  We instrument at "CHOKE POINTS" - places ALL traffic flows through         │
│  Add logging ONCE at each point = captures EVERYTHING automatically         │
│                                                                             │
│                                                                             │
│                         ┌─────────────────┐                                 │
│                         │   HTTP Request  │                                 │
│                         └────────┬────────┘                                 │
│                                  │                                          │
│                                  ▼                                          │
│  CHOKE POINT 1 ───▶  ┌─────────────────────┐                               │
│  middleware.py       │  RequestLogging     │  Auto-logs ALL requests       │
│                      │  Middleware         │  method, path, status, time   │
│                      └────────┬────────────┘                               │
│                               │                                             │
│                               ▼                                             │
│                      ┌─────────────────────┐                                │
│                      │   Your API Routes   │  NO CHANGES NEEDED!           │
│                      │   /agents/execute   │                                │
│                      └────────┬────────────┘                                │
│                               │                                             │
│                               ▼                                             │
│  CHOKE POINT 2 ───▶  ┌─────────────────────┐                               │
│  base.py (agents)    │   BaseAgent         │  Auto-logs ALL agents         │
│                      │   .execute()        │  agent_id, type, latency      │
│                      └────────┬────────────┘                               │
│                               │                                             │
│                               ▼                                             │
│  CHOKE POINT 3 ───▶  ┌─────────────────────┐                               │
│  base.py (llm)       │   LLMProvider       │  Auto-logs ALL LLM calls      │
│                      │   .complete()       │  tokens, cost, model, time    │
│                      └─────────────────────┘                               │
│                                                                             │
│                                                                             │
│  RESULT: Modify only 4-5 files. Your 100+ business files = UNCHANGED!      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. FILES TO MODIFY (Only These!)

| File | What We Add | What Gets Logged Automatically |
|------|-------------|-------------------------------|
| `src/config/logging.py` | Loki handler | All logs shipped to Loki |
| `src/llm/providers/base.py` | Logging wrapper | Every LLM call (tokens, cost, latency) |
| `src/agents/base.py` | Logging wrapper | Every agent execution |
| `src/api/middleware.py` | Metrics + Loki | Every HTTP request/response |
| `src/workflows/executor.py` | Logging wrapper | Every workflow run |

**Your business code files: ZERO changes needed!**

---

## Architecture Flowchart

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           YOUR APPLICATION                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │   Agent     │    │   LLM       │    │  Workflow   │    │    API      │       │
│  │  Execution  │    │   Call      │    │  Execution  │    │   Request   │       │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘       │
│         │                  │                  │                  │              │
│         └──────────────────┴──────────────────┴──────────────────┘              │
│                                      │                                           │
│                        ┌─────────────┴─────────────┐                            │
│                        ▼                           ▼                            │
│              ┌─────────────────┐         ┌─────────────────┐                    │
│              │  METRICS        │         │  LOGS           │                    │
│              │  (Numbers)      │         │  (Text Events)  │                    │
│              └────────┬────────┘         └────────┬────────┘                    │
└───────────────────────┼────────────────────────────┼────────────────────────────┘
                        │                            │
          ┌─────────────┴─────────────┐    ┌────────┴────────┐
          ▼                           ▼    ▼                 │
┌─────────────────┐          ┌─────────────────┐             │
│   PROMETHEUS    │          │   POSTGRESQL    │             │
│  (Time-Series)  │          │   (Permanent)   │             │
│                 │          │                 │             │
│ • Real-time     │          │ • llm_usage     │             │
│   metrics       │          │ • agent_exec    │             │
│ • 30 day        │          │ • workflow_     │             │
│   retention     │          │   analytics     │             │
│ • Fast queries  │          │ • FOREVER       │             │
└────────┬────────┘          └────────┬────────┘             │
         │                            │                      │
         │    ┌───────────────────────┤                      │
         │    │                       │                      │
         ▼    ▼                       │                      ▼
┌─────────────────┐                   │           ┌─────────────────┐
│    GRAFANA      │◄──────────────────┘           │      LOKI       │
│  (Dashboards)   │                               │  (Log Storage)  │
│                 │◄──────────────────────────────┤                 │
│ • Visualize     │                               │ • Searchable    │
│ • Alert         │                               │ • Permanent     │
│ • Explore       │                               │ • Structured    │
└────────┬────────┘                               └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR CUSTOM UI (Option)                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  Analytics  │    │   Logs      │    │   Costs     │          │
│  │   Widget    │    │   Viewer    │    │   Report    │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                  │
│                            │                                     │
│              Query via API: PostgreSQL + Prometheus + Loki       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Storage Map

```
┌────────────────────────────────────────────────────────────────────┐
│                        WHERE DATA GOES                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────┐     ┌──────────────────┐                    │
│  │   KPIs/METRICS   │     │      LOGS        │                    │
│  └────────┬─────────┘     └────────┬─────────┘                    │
│           │                        │                               │
│     ┌─────┴─────┐            ┌─────┴─────┐                        │
│     ▼           ▼            ▼           ▼                        │
│ ┌───────┐  ┌─────────┐  ┌───────┐  ┌─────────┐                   │
│ │Real-  │  │Permanent│  │Real-  │  │Permanent│                   │
│ │time   │  │History  │  │time   │  │Archive  │                   │
│ └───┬───┘  └────┬────┘  └───┬───┘  └────┬────┘                   │
│     │           │           │           │                         │
│     ▼           ▼           ▼           ▼                         │
│ ┌─────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐                  │
│ │Prometheus│ │PostgreSQL│ │Stdout  │ │  Loki   │                  │
│ │ scrape  │ │ INSERT   │ │structlog│ │  push   │                  │
│ │ /metrics│ │          │ │        │ │         │                   │
│ └─────────┘ └──────────┘ └────────┘ └─────────┘                   │
│                                                                    │
│  WHY MULTIPLE STORES?                                              │
│  • Prometheus = fast aggregation, alerting (30 day rolling)       │
│  • PostgreSQL = permanent history for reports, compliance          │
│  • Loki = searchable logs, correlate with metrics                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## KPI Example: Agent Success Rate

```
┌─────────────────────────────────────────────────────────────────────┐
│                    KPI: AGENT SUCCESS RATE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  STEP 1: Code Instrumentation                                       │
│  ────────────────────────────                                       │
│                                                                     │
│  # In src/agents/types/llm_agent.py                                 │
│                                                                     │
│  from src.monitoring.metrics import AGENT_EXECUTION_TOTAL           │
│                                                                     │
│  async def execute(self, context):                                  │
│      try:                                                           │
│          response = await self._call_llm(context)                   │
│          AGENT_EXECUTION_TOTAL.labels(                              │
│              agent_id=self.config.id,                               │
│              agent_type="llm",                                      │
│              status="success"    # ◄── SUCCESS                      │
│          ).inc()                                                    │
│          return response                                            │
│      except Exception:                                              │
│          AGENT_EXECUTION_TOTAL.labels(                              │
│              agent_id=self.config.id,                               │
│              agent_type="llm",                                      │
│              status="failure"    # ◄── FAILURE                      │
│          ).inc()                                                    │
│          raise                                                      │
│                                                                     │
│  STEP 2: What Prometheus Scrapes                                    │
│  ───────────────────────────────                                    │
│                                                                     │
│  GET http://localhost:8000/metrics                                  │
│                                                                     │
│  magure_agent_executions_total{agent_id="kpi-agent",                │
│                                agent_type="llm",                    │
│                                status="success"} 1523               │
│  magure_agent_executions_total{agent_id="kpi-agent",                │
│                                agent_type="llm",                    │
│                                status="failure"} 47                 │
│                                                                     │
│  STEP 3: Grafana Dashboard Query (PromQL)                           │
│  ─────────────────────────────────────────                          │
│                                                                     │
│  Success Rate = successes / total * 100                             │
│                                                                     │
│  sum(rate(magure_agent_executions_total{status="success"}[5m]))     │
│  /                                                                  │
│  sum(rate(magure_agent_executions_total[5m]))                       │
│  * 100                                                              │
│                                                                     │
│  Result: 97.0%  ────────────────────────▶  [██████████░] 97%        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Log Example: LLM Call

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LOG: LLM CALL DETAILS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  STEP 1: Code Logging                                               │
│  ────────────────────                                               │
│                                                                     │
│  # In src/llm/providers/openai.py                                   │
│                                                                     │
│  logger.info(                                                       │
│      "llm_call_completed",                                          │
│      provider="openai",                                             │
│      model="gpt-4o",                                                │
│      prompt_tokens=1250,                                            │
│      completion_tokens=380,                                         │
│      latency_ms=2340.5,                                             │
│      cost_cents=156,                                                │
│      request_id="req-abc123",                                       │
│      agent_id="kpi-calculator"                                      │
│  )                                                                  │
│                                                                     │
│  STEP 2: JSON Log Sent to Loki                                      │
│  ─────────────────────────────                                      │
│                                                                     │
│  {                                                                  │
│    "timestamp": "2025-01-15T10:23:45.123Z",                         │
│    "level": "INFO",                                                 │
│    "event": "llm_call_completed",                                   │
│    "provider": "openai",                                            │
│    "model": "gpt-4o",                                               │
│    "prompt_tokens": 1250,                                           │
│    "completion_tokens": 380,                                        │
│    "latency_ms": 2340.5,                                            │
│    "cost_cents": 156,                                               │
│    "request_id": "req-abc123",                                      │
│    "agent_id": "kpi-calculator"                                     │
│  }                                                                  │
│                                                                     │
│  STEP 3: Query in Grafana (LogQL)                                   │
│  ────────────────────────────────                                   │
│                                                                     │
│  # Find all LLM calls for an agent                                  │
│  {app="magure-ai"} |= "llm_call_completed"                          │
│                    | json                                           │
│                    | agent_id="kpi-calculator"                      │
│                                                                     │
│  # Find slow calls (>5 seconds)                                     │
│  {app="magure-ai"} | json | latency_ms > 5000                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Dual UI Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         YOUR TWO UIs                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                      YOUR NEXT.JS APP (web/)                             │    │
│  │                                                                          │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │    │
│  │  │ Analytics Page  │  │  Logs Viewer    │  │  Cost Report    │          │    │
│  │  │                 │  │                 │  │                 │          │    │
│  │  │ [Success: 97%]  │  │ 10:23 LLM call  │  │ Today: $12.50   │          │    │
│  │  │ [Tokens: 50K]   │  │ 10:24 Agent OK  │  │ GPT-4o: $8.00   │          │    │
│  │  │ [Cost: $12.50]  │  │ 10:25 Error!    │  │ Claude: $4.50   │          │    │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘          │    │
│  │           │                    │                    │                    │    │
│  │           └────────────────────┴────────────────────┘                    │    │
│  │                                │                                         │    │
│  │                    ┌───────────▼───────────┐                            │    │
│  │                    │  /api/analytics/*     │                            │    │
│  │                    │  Backend API Router   │                            │    │
│  │                    └───────────────────────┘                            │    │
│  │  Use: Quick glance, embedded widgets                                     │    │
│  └──────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                      GRAFANA (localhost:3001)                            │    │
│  │                                                                          │    │
│  │  • Agent Performance Dashboard    • Workflow Analytics Dashboard         │    │
│  │  • LLM Cost Analysis Dashboard    • System Health Dashboard              │    │
│  │  • Log Explorer (search all logs)                                        │    │
│  │  • Alerting & Notifications                                              │    │
│  │                                                                          │    │
│  │  Use: Deep analysis, debugging, alerts                                   │    │
│  └──────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  SAME DATA SOURCES ──────────────────────────────────────────────────────────    │
│                                                                                  │
│       ┌─────────────┐      ┌─────────────┐      ┌─────────────┐               │
│       │ PostgreSQL  │      │ Prometheus  │      │    Loki     │               │
│       │ (permanent) │      │ (real-time) │      │   (logs)    │               │
│       └─────────────┘      └─────────────┘      └─────────────┘               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Summary

| Component | Purpose | Port | Retention |
|-----------|---------|------|-----------|
| **Prometheus** | Metrics collection & queries | 9090 | 30 days |
| **Grafana** | Dashboards & alerting | 3001 | N/A |
| **Loki** | Log aggregation | 3100 | Permanent |
| **PostgreSQL** | Analytics history | 5432 | Permanent |

---

## File Structure

```
src/monitoring/
├── __init__.py
├── config.py                      # Monitoring configuration
├── metrics/
│   ├── __init__.py
│   ├── prometheus_metrics.py      # Metric definitions
│   ├── collectors.py              # System metrics collector
│   └── middleware.py              # FastAPI metrics middleware
├── analytics/
│   ├── __init__.py
│   ├── models.py                  # Database models
│   ├── repository.py              # Data access layer
│   ├── service.py                 # Analytics service
│   └── cost_calculator.py         # OpenAI + Anthropic pricing
└── logging/
    ├── __init__.py
    ├── handlers.py                # Loki log handler
    └── context.py                 # Log context enrichment

docker/
├── docker-compose.monitoring.yml  # Prometheus, Grafana, Loki
└── monitoring/
    ├── prometheus/prometheus.yml
    ├── grafana/
    │   ├── provisioning/
    │   └── dashboards/*.json
    └── loki/loki-config.yml
```

---

## Database Schema (New Tables)

### 1. `llm_usage` - Token & Cost Tracking
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| timestamp | DateTime | When call occurred |
| request_id | String | HTTP request correlation |
| agent_id | String | Which agent made the call |
| workflow_id | String | Which workflow execution |
| provider | String | "openai" or "anthropic" |
| model | String | Model name (gpt-4o, claude-3-5-sonnet) |
| prompt_tokens | Integer | Input tokens |
| completion_tokens | Integer | Output tokens |
| cost_cents | Integer | Cost in USD cents |
| latency_ms | Integer | Response time |
| success | Boolean | Success/failure |

### 2. `agent_executions` - Agent Performance
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| timestamp | DateTime | When executed |
| agent_id | String | Agent identifier |
| agent_type | String | llm, rag, tool, etc. |
| success | Boolean | Success/failure |
| latency_ms | Integer | Execution time |
| llm_calls_count | Integer | Number of LLM calls |
| tool_calls_count | Integer | Number of tool calls |
| tokens_used | Integer | Total tokens |

### 3. `workflow_analytics` - Workflow Metrics
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| workflow_id | String | Workflow identifier |
| status | String | completed, failed, timeout |
| duration_ms | Integer | Total execution time |
| steps_executed | Integer | Steps completed |
| steps_failed | Integer | Steps that failed |

---

## Prometheus Metrics

### HTTP Metrics
```
magure_http_requests_total{method, endpoint, status_code}
magure_http_request_duration_seconds{method, endpoint}
magure_http_requests_in_progress{method, endpoint}
```

### Agent Metrics
```
magure_agent_executions_total{agent_id, agent_type, status}
magure_agent_execution_duration_seconds{agent_id, agent_type}
magure_agent_tool_calls_total{agent_id, tool_name, status}
```

### LLM Metrics
```
magure_llm_requests_total{provider, model, status}
magure_llm_request_duration_seconds{provider, model}
magure_llm_tokens_total{provider, model, token_type}
magure_llm_cost_cents_total{provider, model}
```

### Workflow Metrics
```
magure_workflow_executions_total{workflow_id, status}
magure_workflow_duration_seconds{workflow_id}
magure_workflows_active
```

---

## LLM Cost Calculator

Pricing in cents per 1K tokens:

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenAI | gpt-4o | 0.25 | 1.0 |
| OpenAI | gpt-4o-mini | 0.015 | 0.06 |
| OpenAI | gpt-4-turbo | 1.0 | 3.0 |
| OpenAI | o1-preview | 1.5 | 6.0 |
| Anthropic | claude-3-5-sonnet | 0.3 | 1.5 |
| Anthropic | claude-3-opus | 1.5 | 7.5 |
| Anthropic | claude-3-haiku | 0.025 | 0.125 |

---

## Grafana Dashboards

### 1. Agent Performance
- Executions over time (line chart)
- Success rate by agent type (gauge)
- Top 10 agents by execution count (bar)
- Latency heatmap

### 2. LLM Usage & Costs
- Token usage by model (stacked bar)
- Cost breakdown (pie chart)
- Cost over time (line chart)
- Latency percentiles (histogram)

### 3. Workflow Analytics
- Runs over time
- Status distribution
- Duration by workflow
- Steps histogram

### 4. System Health
- CPU/memory usage
- Database connections
- API request rate
- Error rate & p99 latency

---

## Integration Points (Choke Point Strategy)

### Files We Modify (ONLY THESE!)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHOKE POINT INSTRUMENTATION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TOTAL FILES TO MODIFY: 7 files                                             │
│  YOUR BUSINESS CODE: 0 files changed                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| # | File | Change | Auto-Captures |
|---|------|--------|---------------|
| 1 | `src/config/logging.py` | Add Loki handler | All logs → Loki |
| 2 | `src/llm/providers/base.py` | Logging wrapper in base class | Every LLM call (all providers) |
| 3 | `src/agents/base.py` | Logging wrapper in execute() | Every agent execution |
| 4 | `src/api/middleware.py` | Add Prometheus metrics | Every HTTP request |
| 5 | `src/api/app.py` | Add `/metrics` endpoint | Prometheus scraping |
| 6 | `src/workflows/executor.py` | Logging wrapper | Every workflow run |
| 7 | `src/config/settings.py` | Monitoring config vars | Configuration |

### What Gets Captured Automatically

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTOMATIC CAPTURE - NO MANUAL LOGGING                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HTTP Layer (middleware.py)                                                 │
│  ├── Every request: method, path, headers                                   │
│  ├── Every response: status_code, duration_ms                               │
│  ├── Request ID for tracing                                                 │
│  └── Client IP address                                                      │
│                                                                             │
│  LLM Layer (base.py)                                                        │
│  ├── Every OpenAI call                                                      │
│  ├── Every Anthropic call                                                   │
│  ├── Model used (gpt-4o, claude-3-5-sonnet, etc.)                          │
│  ├── Tokens: prompt + completion                                            │
│  ├── Cost: calculated automatically from pricing table                      │
│  ├── Latency: response time in ms                                           │
│  └── Success/failure + error type                                           │
│                                                                             │
│  Agent Layer (base.py)                                                      │
│  ├── Every agent execution                                                  │
│  ├── Agent ID and type (llm, rag, tool, router, etc.)                      │
│  ├── Execution time                                                         │
│  ├── Tool calls made                                                        │
│  └── Success/failure                                                        │
│                                                                             │
│  Workflow Layer (executor.py)                                               │
│  ├── Every workflow run                                                     │
│  ├── Steps executed                                                         │
│  ├── Duration                                                               │
│  └── Final status                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation
1. Create `src/monitoring/` module
2. Prometheus metric definitions
3. Metrics middleware
4. `/metrics` endpoint
5. Docker Compose for Prometheus

### Phase 2: Analytics Database
1. Database models
2. Alembic migrations
3. Cost calculator
4. Analytics repository
5. Analytics service

### Phase 3: Instrumentation
1. Instrument LLM providers
2. Agent execution metrics
3. Temporal activities
4. Workflow metrics
5. Background aggregation

### Phase 4: Logging
1. Loki container
2. Loki log handler
3. structlog integration
4. Log context enrichment

### Phase 5: Dashboards
1. Grafana container
2. Dashboard JSON files
3. Data source provisioning
4. Alert rules

---

## Dependencies

```toml
prometheus-client>=0.19.0
python-logging-loki>=0.3.1
psutil>=5.9.0
```

---

## Config Settings

```python
# Monitoring
prometheus_enabled: bool = True
loki_enabled: bool = True
loki_url: str = "http://localhost:3100"
analytics_enabled: bool = True
analytics_aggregation_interval: int = 3600  # 1 hour
cost_tracking_enabled: bool = True
```

---

## Custom UI API Endpoints

```
GET /api/analytics/token-usage?hours=24
GET /api/analytics/costs?hours=24
GET /api/analytics/agent-success-rate?agent_id=X
GET /api/analytics/recent-logs?limit=50&level=error
```

---

## Final Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MONITORING SERVICE HIGHLIGHTS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✅ PERMANENT STORAGE                                                       │
│     • Loki: retention_period = 0 (forever)                                  │
│     • PostgreSQL: analytics tables (forever)                                │
│     • Both backed up with your regular backup strategy                      │
│                                                                             │
│  ✅ ZERO MANUAL LOGGING                                                     │
│     • Instrument 7 "choke point" files only                                 │
│     • Your 100+ business code files: NO CHANGES                             │
│     • All LLM calls, agents, workflows captured automatically               │
│                                                                             │
│  ✅ WHAT'S CAPTURED AUTOMATICALLY                                           │
│     • Every HTTP request/response                                           │
│     • Every LLM call (tokens, cost, latency, model)                        │
│     • Every agent execution (type, duration, success)                       │
│     • Every workflow run (steps, duration, status)                          │
│                                                                             │
│  ✅ TWO UIs                                                                 │
│     • Grafana (localhost:3001): Full dashboards, alerts, exploration        │
│     • Your App: Embedded widgets via /api/analytics/*                       │
│                                                                             │
│  ✅ COST TRACKING                                                           │
│     • OpenAI: gpt-4o, gpt-4o-mini, gpt-4-turbo, o1-preview                 │
│     • Anthropic: claude-3-5-sonnet, claude-3-opus, claude-3-haiku          │
│     • Cost calculated per request automatically                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Quick Reference

| Question | Answer |
|----------|--------|
| How long are logs kept? | **Forever** (Loki + PostgreSQL) |
| Do I add logging to every file? | **No!** Only 7 choke point files |
| What gets logged automatically? | HTTP, LLM calls, agents, workflows |
| Where do I see dashboards? | **Grafana** at localhost:3001 |
| Where do I see in my app? | **/api/analytics/*** endpoints |
| How is cost calculated? | **Automatically** from token counts |

### Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics storage (30 day rolling) |
| Grafana | 3001 | Dashboards & alerts |
| Loki | 3100 | Log storage (forever) |
| PostgreSQL | 5432 | Analytics (forever) - existing |

### New Dependencies

```toml
prometheus-client>=0.19.0    # Metrics
python-logging-loki>=0.3.1   # Loki log shipping
psutil>=5.9.0                # System metrics
```

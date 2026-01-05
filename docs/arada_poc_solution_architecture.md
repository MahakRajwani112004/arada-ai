# Arada POC - Solution Architecture

**Version:** 1.0
**Date:** 5 January 2026
**Target Showcase:** 16 January 2026

---

## 1. Executive Summary

This document outlines the solution architecture for the Arada POC, leveraging a **Multi-Agent + Skills/Semantic Layer** approach. The system is designed to deliver:

- **Conversational Analytics** - Chat-based interface with no pre-loaded dashboards
- **Pre-identified Insights** - Automated analysis surfaced proactively
- **Deep Exploration** - Drill-down capabilities driven by conversation
- **Automated Visualizations** - Charts generated on-demand based on context
- **Contextual Memory** - Full conversation history maintained within each session

---

## 2. Architecture Overview

```
                                    +---------------------------+
                                    |      Chat Interface       |
                                    |   (Next.js Frontend)      |
                                    +-------------+-------------+
                                                  |
                                                  | SSE Streaming
                                                  v
+-------------------------------------------------------------------------------------------+
|                                    API Gateway (FastAPI)                                   |
|                              /chat  /conversations  /insights                             |
+-------------------------------------------------------------------------------------------+
                                                  |
                    +-----------------------------+-----------------------------+
                    |                             |                             |
                    v                             v                             v
        +-------------------+         +-------------------+         +-------------------+
        |   Analytics       |         |    Conversation   |         |    Insight        |
        |   Orchestrator    |         |    Manager        |         |    Engine         |
        |   (Multi-Agent)   |         |    (Memory)       |         |    (Pre-computed) |
        +-------------------+         +-------------------+         +-------------------+
                    |                             |                             |
                    +-----------------------------+-----------------------------+
                                                  |
+-------------------------------------------------------------------------------------------+
|                              Agent Layer (Temporal Workflows)                             |
+-------------------------------------------------------------------------------------------+
        |                   |                   |                   |
        v                   v                   v                   v
+---------------+   +---------------+   +---------------+   +---------------+
|  Descriptive  |   |   Deep Dive   |   | Decomposition |   |   What-If     |
|    Agent      |   |    Agent      |   |    Agent      |   |    Agent      |
| (FullAgent)   |   | (FullAgent)   |   | (FullAgent)   |   | (ToolAgent)   |
+---------------+   +---------------+   +---------------+   +---------------+
        |                   |                   |                   |
        +-------------------+-------------------+-------------------+
                                    |
+-------------------------------------------------------------------------------------------+
|                               Tools & Skills Layer                                        |
+-------------------------------------------------------------------------------------------+
        |                   |                   |                   |
        v                   v                   v                   v
+---------------+   +---------------+   +---------------+   +---------------+
|     KPI       |   |    Chart      |   |   What-If     |   |    Query      |
|  Calculator   |   |   Generator   |   |   Simulator   |   |    Engine     |
+---------------+   +---------------+   +---------------+   +---------------+
                                    |
+-------------------------------------------------------------------------------------------+
|                               Semantic Layer                                              |
|                    KPI Definitions | Business Rules | Terminology                         |
+-------------------------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------------------------+
|                               Data Layer                                                  |
|                         PostgreSQL | Qdrant | Redis Cache                                 |
+-------------------------------------------------------------------------------------------+
```

---

## 3. Multi-Agent Architecture

### 3.1 Agent Hierarchy

```
                    +----------------------------------+
                    |      Analytics Orchestrator      |
                    |       (OrchestratorAgent)        |
                    |                                  |
                    |  - Routes queries to specialists |
                    |  - Synthesizes multi-agent output|
                    |  - Manages analysis workflow     |
                    +----------------------------------+
                                    |
            +-----------------------+-----------------------+
            |           |           |           |           |
            v           v           v           v           v
    +------------+ +------------+ +------------+ +------------+ +------------+
    |Descriptive | | Deep Dive  | |Decomposition| | What-If   | |  Insight   |
    |   Agent    | |   Agent    | |   Agent    | |   Agent    | |  Agent     |
    +------------+ +------------+ +------------+ +------------+ +------------+
    | KPI metrics| | Drill-down | | Breakdown  | | Scenarios  | | Anomalies  |
    | Trends     | | Root cause | | Attribution| | Simulation | | Patterns   |
    | Comparisons| | Filtering  | | Waterfall  | | Projection | | Alerts     |
    +------------+ +------------+ +------------+ +------------+ +------------+
```

### 3.2 Agent Specifications

#### 3.2.1 Analytics Orchestrator (Master Agent)

| Property | Value |
|----------|-------|
| **Type** | `OrchestratorAgent` |
| **Mode** | `llm_driven` with auto-discovery |
| **Role** | Route queries, coordinate multi-agent analysis, synthesize results |

**Configuration:**
```python
OrchestratorConfig(
    mode="llm_driven",
    auto_discover=True,
    max_parallel_agents=3,
    max_depth=2,
    aggregation_strategy="sequential",
    circuit_breaker_threshold=3
)
```

**System Prompt:**
```
You are the Analytics Orchestrator for Arada real estate analytics.

Your role is to:
1. Understand the user's analytical intent
2. Route to the appropriate specialist agent(s)
3. Synthesize insights from multiple agents when needed
4. Maintain conversational context for follow-up questions

Available Specialist Agents:
- descriptive_agent: KPI metrics, trends, period comparisons
- deepdive_agent: Drill-down analysis, root cause investigation
- decomposition_agent: Breakdown analysis, attribution, waterfall
- whatif_agent: Scenario simulation, impact projection
- insight_agent: Pre-computed insights, anomaly detection

Always respond conversationally and include relevant visualizations.
```

---

#### 3.2.2 Descriptive Analytics Agent

| Property | Value |
|----------|-------|
| **Type** | `FullAgent` |
| **Tools** | `kpi_calculator`, `chart_generator`, `real_estate_query` |
| **Skills** | `descriptive_analytics_skill`, `kpi_interpretation_skill` |
| **KB** | KPI definitions, benchmarks, industry standards |

**Capabilities:**
- Calculate and display 10 KPIs
- Show trends (monthly, quarterly, YoY)
- Compare vs benchmarks/portfolio
- Generate time-series visualizations

**Supported KPIs (10):**
| # | KPI | Formula | Visualization |
|---|-----|---------|---------------|
| 1 | Net Sales | SUM(net_sale_value) | Line/Bar |
| 2 | Total Bookings | COUNT(bookings) | Bar |
| 3 | Portfolio Value | SUM(portfolio) | Area |
| 4 | Cancellation Rate | cancelled/total * 100 | Line + Threshold |
| 5 | Avg Realization | collected/portfolio * 100 | Gauge |
| 6 | Avg Discount | AVG(discount_pct) | Bar |
| 7 | Collection Efficiency | collected/target * 100 | Gauge |
| 8 | Avg Deal Size | AVG(deal_value) | Bar |
| 9 | Conversion Rate | converted/leads * 100 | Funnel |
| 10 | Price per Sqft | AVG(price/sqft) | Bar |

---

#### 3.2.3 Deep Dive Agent

| Property | Value |
|----------|-------|
| **Type** | `FullAgent` |
| **Tools** | `real_estate_query`, `chart_generator`, `kpi_calculator` |
| **Skills** | `drill_down_skill`, `root_cause_skill` |
| **KB** | Dimension hierarchies, common drill paths |

**Capabilities:**
- Drill-down on any KPI by dimensions
- Filter by region, project, cluster, unit type, etc.
- Identify outliers and anomalies
- Compare segments within a KPI

**Drill-Down Dimensions:**
```
Region
  └── Project/Development
        └── Cluster
              └── Unit Type
                    └── Individual Unit

Lead Source
  └── Channel
        └── Campaign

Time
  └── Year
        └── Quarter
              └── Month
                    └── Week
```

**Deep Dive Focus Areas (from MOM):**
- Cancellation analysis by region, project
- [Additional KPIs to be defined]

---

#### 3.2.4 Decomposition Agent

| Property | Value |
|----------|-------|
| **Type** | `FullAgent` |
| **Tools** | `decomposition_tool`, `chart_generator`, `real_estate_query` |
| **Skills** | `variance_analysis_skill`, `attribution_skill` |
| **KB** | Decomposition methodologies |

**Capabilities:**
- Waterfall decomposition (contribution analysis)
- Variance decomposition (period-over-period)
- Mix vs rate decomposition
- Attribution analysis

**Decomposition Types (Max 3 as per MOM):**
| # | Type | Use Case | Visualization |
|---|------|----------|---------------|
| 1 | Contribution Breakdown | What's driving Net Sales? | Waterfall |
| 2 | Period Variance | Why did cancellations change? | Bridge Chart |
| 3 | Mix Analysis | Price vs Volume effect | Stacked Bar |

---

#### 3.2.5 What-If Agent

| Property | Value |
|----------|-------|
| **Type** | `ToolAgent` |
| **Tools** | `what_if_simulator`, `chart_generator` |
| **Skills** | `scenario_modeling_skill` |

**Capabilities:**
- Scenario simulation
- Impact projection
- Sensitivity analysis
- Multi-variable what-if

**What-If Scenarios (from MOM):**
| # | Scenario | Parameters | Output |
|---|----------|------------|--------|
| 1 | Net Sales Impact | Price change %, Volume change % | Projected Net Sales |
| 2 | [Additional TBD] | | |

**Simulation Engine:**
```python
WhatIfScenarios = {
    "net_sales_projection": {
        "inputs": ["price_change_pct", "volume_change_pct", "discount_cap"],
        "model": "linear_impact",
        "confidence_interval": 0.95
    },
    "cancellation_impact": {
        "inputs": ["policy_change", "follow_up_frequency"],
        "model": "logistic_regression",
        "confidence_interval": 0.90
    }
}
```

---

#### 3.2.6 Insight Agent

| Property | Value |
|----------|-------|
| **Type** | `FullAgent` |
| **Tools** | `insight_detector`, `chart_generator` |
| **Skills** | `anomaly_detection_skill`, `pattern_recognition_skill` |

**Capabilities:**
- Pre-computed insights surfacing
- Anomaly detection
- Trend identification
- Proactive alerts

**Pre-Identified Insights Engine:**
```python
InsightTypes = [
    "significant_change",     # >10% change in any KPI
    "threshold_breach",       # KPI crosses warning/critical threshold
    "trend_reversal",         # Trend direction change
    "outlier_segment",        # Segment significantly different from average
    "correlation_detected",   # Strong correlation between metrics
    "forecast_deviation"      # Actual vs forecast variance
]
```

---

## 4. Skills & Semantic Layer

### 4.1 Skill Definitions

#### 4.1.1 Descriptive Analytics Skill

```python
Skill(
    name="descriptive_analytics",
    description="Expert in calculating and interpreting KPI metrics",
    category=SkillCategory.DATA_ANALYSIS,
    terminology=[
        Term("Net Sales", "Total value of sales after cancellations"),
        Term("Realization", "Percentage of portfolio value collected"),
        Term("Portfolio Value", "Total value of active bookings"),
        # ... more terms
    ],
    reasoning_patterns=[
        ReasoningPattern(
            name="kpi_interpretation",
            steps=[
                "1. Identify the KPI being asked about",
                "2. Calculate current value",
                "3. Compare to benchmark/threshold",
                "4. Determine status (normal/warning/critical)",
                "5. Provide contextual interpretation"
            ]
        )
    ],
    examples=[
        SkillExample(
            input="What is the trend of net sales in 2024?",
            output="Net Sales showed a 12% growth in 2024..."
        )
    ]
)
```

#### 4.1.2 Drill-Down Skill

```python
Skill(
    name="drill_down_analysis",
    description="Expert in hierarchical data exploration and root cause analysis",
    category=SkillCategory.DATA_ANALYSIS,
    reasoning_patterns=[
        ReasoningPattern(
            name="drill_down_navigation",
            steps=[
                "1. Identify current context from conversation history",
                "2. Determine the dimension to drill into",
                "3. Apply appropriate filters",
                "4. Calculate metrics at new granularity",
                "5. Identify notable patterns or outliers"
            ]
        )
    ]
)
```

#### 4.1.3 Scenario Modeling Skill

```python
Skill(
    name="scenario_modeling",
    description="Expert in what-if analysis and impact simulation",
    category=SkillCategory.DATA_ANALYSIS,
    reasoning_patterns=[
        ReasoningPattern(
            name="what_if_analysis",
            steps=[
                "1. Establish baseline metrics",
                "2. Identify variables to modify",
                "3. Apply impact model",
                "4. Calculate projected outcomes",
                "5. Present best/worst/expected scenarios"
            ]
        )
    ]
)
```

### 4.2 Semantic Layer (KPI Definitions)

```python
ARADA_SEMANTIC_LAYER = {
    "kpis": {
        "net_sales": {
            "name": "Net Sales",
            "formula": "SUM(sale_value) - SUM(cancellation_value)",
            "unit": "AED",
            "aggregation": "SUM",
            "dimensions": ["region", "project", "cluster", "unit_type", "time"],
            "thresholds": {
                "critical_low": 0.7,  # 70% of target
                "warning_low": 0.85,
                "warning_high": 1.15,
                "critical_high": 1.3
            }
        },
        "cancellation_rate": {
            "name": "Cancellation Rate",
            "formula": "COUNT(cancelled) / COUNT(total) * 100",
            "unit": "%",
            "aggregation": "RATIO",
            "dimensions": ["region", "project", "cluster", "reason", "time"],
            "thresholds": {
                "warning": 45,
                "critical": 55
            },
            "inverse": True  # Lower is better
        },
        # ... 8 more KPIs
    },
    "dimensions": {
        "region": {
            "hierarchy": ["region", "project", "cluster", "unit_type"],
            "drill_path": "region -> project -> cluster -> unit"
        },
        "time": {
            "hierarchy": ["year", "quarter", "month", "week"],
            "drill_path": "year -> quarter -> month -> week"
        }
    },
    "business_rules": {
        "cancellation_valid_period": "Within 30 days of booking",
        "realization_calculation": "Only confirmed payments",
        "discount_cap": "Maximum 15% unless approved"
    }
}
```

---

## 5. Conversation Flow & Memory

### 5.1 Conversation Architecture

```
User Session
    │
    ├── Conversation 1
    │   ├── Message 1: "Show me net sales trend for 2024"
    │   │   └── Context: {kpi: "net_sales", time: "2024", view: "trend"}
    │   ├── Message 2: "Break it down by region"
    │   │   └── Context: {kpi: "net_sales", time: "2024", dimension: "region"}
    │   ├── Message 3: "Drill into Dubai"
    │   │   └── Context: {kpi: "net_sales", time: "2024", filter: {region: "Dubai"}}
    │   └── Message 4: "What if we increase prices by 5%?"
    │       └── Context: {scenario: "price_change", base_context: {...}}
    │
    └── Conversation 2 (New Topic)
        └── ...
```

### 5.2 Context Accumulation Pattern

```python
class ConversationContext:
    """Maintains analytical context across conversation turns"""

    session_id: str
    current_kpi: Optional[str]
    current_dimensions: List[str]
    active_filters: Dict[str, Any]
    time_range: Dict[str, str]
    comparison_base: Optional[Dict]
    drill_path: List[str]  # ["region:Dubai", "project:DAMAC Bay"]
    last_visualization: Optional[Dict]

    def apply_drill_down(self, dimension: str, value: str):
        """Add filter and track drill path"""
        self.active_filters[dimension] = value
        self.drill_path.append(f"{dimension}:{value}")

    def reset_to_level(self, level: int):
        """Reset drill path to specific level"""
        self.drill_path = self.drill_path[:level]
        # Rebuild filters from drill path
```

### 5.3 Memory Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Message                                │
│         "Show me cancellations for Dubai projects"              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│                   Context Manager                               │
│  1. Load conversation history                                   │
│  2. Extract accumulated context                                 │
│  3. Merge with new request                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│                   Analytics Orchestrator                        │
│  Receives: {                                                    │
│    user_input: "Show me cancellations for Dubai projects",      │
│    conversation_history: [...previous messages...],             │
│    context: {                                                   │
│      previous_kpi: "net_sales",                                 │
│      previous_filters: {region: "UAE"},                         │
│      drill_path: ["region:UAE"]                                 │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│                   Agent Response                                │
│  - Updates context: {kpi: "cancellation_rate", filter: Dubai}   │
│  - Stores in conversation history                               │
│  - Returns chart + insights                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Automated Visualization System

### 6.1 Chart Selection Logic

```python
CHART_SELECTION_RULES = {
    "trend": {
        "single_metric": "line",
        "multiple_metrics": "multi_line",
        "with_target": "line_with_threshold"
    },
    "comparison": {
        "few_categories": "bar",           # < 7 categories
        "many_categories": "horizontal_bar",  # >= 7 categories
        "part_of_whole": "pie"
    },
    "distribution": {
        "continuous": "histogram",
        "categorical": "bar"
    },
    "decomposition": {
        "contribution": "waterfall",
        "variance": "bridge",
        "mix": "stacked_bar"
    },
    "correlation": {
        "two_variables": "scatter",
        "multiple": "heatmap"
    }
}
```

### 6.2 Auto-Insight Generation

```python
class InsightGenerator:
    """Generates insights automatically with each visualization"""

    def generate_insights(self, data: DataFrame, chart_type: str) -> List[str]:
        insights = []

        # Statistical insights
        insights.append(f"Maximum: {data.max()} in {data.idxmax()}")
        insights.append(f"Minimum: {data.min()} in {data.idxmin()}")

        # Variance analysis
        cv = data.std() / data.mean()
        if cv > 0.5:
            insights.append("High variance detected across segments")

        # Trend detection (for time series)
        if is_time_series(data):
            trend = detect_trend(data)
            insights.append(f"Overall trend: {trend}")

        # Threshold breaches
        for kpi, value in data.items():
            status = check_threshold(kpi, value)
            if status != "normal":
                insights.append(f"{kpi} is in {status} status")

        return insights
```

### 6.3 Visualization Response Format

```python
VisualizationResponse = {
    "chart_config": {
        "type": "bar",
        "data": {
            "labels": ["Q1", "Q2", "Q3", "Q4"],
            "datasets": [{"label": "Net Sales", "data": [100, 120, 115, 140]}]
        },
        "options": {
            "responsive": True,
            "plugins": {"title": {"text": "Net Sales by Quarter"}}
        }
    },
    "ascii_chart": """
    Net Sales by Quarter
    ████████████████████  Q4: 140M
    ███████████████       Q2: 120M
    ██████████████        Q3: 115M
    ████████████          Q1: 100M
    """,
    "insights": [
        "Q4 shows highest net sales at 140M AED",
        "15% growth from Q1 to Q4",
        "Q3 dip of 4% recovered in Q4"
    ],
    "data_summary": {
        "total": 475,
        "average": 118.75,
        "max": 140,
        "min": 100
    }
}
```

---

## 7. Pre-Identified Insights System

### 7.1 Insight Pipeline

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Data Source    │────>│  Insight Engine  │────>│   Insight Store  │
│   (Real-time)    │     │  (Scheduled)     │     │   (Redis/PG)     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                           │
                                                           v
┌──────────────────────────────────────────────────────────────────────┐
│                        Chat Interface                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Pre-Identified Insights                                       │ │
│  │  ────────────────────────                                      │ │
│  │  ! Cancellation rate in Dubai increased 12% this month         │ │
│  │  ! Net Sales exceeded target by 8% in Q4                       │ │
│  │  i Collection efficiency trending down for 3 consecutive weeks │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Ask me anything...                                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### 7.2 Insight Detection Rules

```python
INSIGHT_DETECTION_RULES = [
    {
        "name": "significant_change",
        "condition": "abs(current - previous) / previous > 0.10",
        "priority": "high",
        "template": "{kpi} changed by {change_pct}% compared to {period}"
    },
    {
        "name": "threshold_breach",
        "condition": "value crosses threshold boundary",
        "priority": "critical",
        "template": "{kpi} has crossed {threshold_type} threshold ({threshold_value})"
    },
    {
        "name": "trend_reversal",
        "condition": "trend direction changed for 2+ periods",
        "priority": "medium",
        "template": "{kpi} trend has reversed from {old_trend} to {new_trend}"
    },
    {
        "name": "segment_outlier",
        "condition": "segment value > 2 std from mean",
        "priority": "medium",
        "template": "{segment} shows unusual {kpi} ({value} vs avg {average})"
    },
    {
        "name": "forecast_miss",
        "condition": "abs(actual - forecast) / forecast > 0.15",
        "priority": "high",
        "template": "{kpi} is {variance_pct}% {direction} forecast"
    }
]
```

---

## 8. Data Flow Architecture

### 8.1 Query Execution Flow

```
User Question
      │
      v
┌─────────────────┐
│ Query Parser    │  Parse natural language to structured query
└─────────────────┘
      │
      v
┌─────────────────┐
│ Semantic Layer  │  Map to KPI definitions, dimensions, filters
└─────────────────┘
      │
      v
┌─────────────────┐
│ Query Builder   │  Build SQL/aggregation query
└─────────────────┘
      │
      v
┌─────────────────┐
│ Cache Check     │  Check Redis for recent identical queries
└─────────────────┘
      │
      v (cache miss)
┌─────────────────┐
│ Data Service    │  Execute against PostgreSQL/CSV
└─────────────────┘
      │
      v
┌─────────────────┐
│ Result Processor│  Apply formatting, calculations
└─────────────────┘
      │
      v
┌─────────────────┐
│ Cache Store     │  Store in Redis (TTL: 5 min)
└─────────────────┘
      │
      v
Response
```

### 8.2 Data Schema Requirements

```sql
-- Core fact table
CREATE TABLE sales_facts (
    id SERIAL PRIMARY KEY,
    booking_date DATE,
    region VARCHAR(100),
    project VARCHAR(200),
    cluster VARCHAR(100),
    unit_type VARCHAR(50),
    unit_id VARCHAR(50),

    -- Measures
    sale_value DECIMAL(15,2),
    net_sale_value DECIMAL(15,2),
    discount_pct DECIMAL(5,2),
    discount_value DECIMAL(15,2),
    collected_amount DECIMAL(15,2),

    -- Status
    booking_status VARCHAR(50),  -- booked, cancelled, confirmed
    cancellation_date DATE,
    cancellation_reason VARCHAR(200),

    -- Lead info
    lead_source VARCHAR(100),
    channel VARCHAR(100),
    nationality VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Dimension tables
CREATE TABLE dim_region (...);
CREATE TABLE dim_project (...);
CREATE TABLE dim_time (...);
```

---

## 9. Technical Implementation

### 9.1 New Components to Build

| Component | Type | Priority | Description |
|-----------|------|----------|-------------|
| `AnalyticsOrchestrator` | Agent | P0 | Master orchestrator for analytics queries |
| `DecompositionTool` | Tool | P0 | Waterfall/variance decomposition |
| `InsightDetector` | Tool | P1 | Pre-computed insight generation |
| `ContextManager` | Service | P0 | Conversation context accumulation |
| `SemanticLayerService` | Service | P0 | KPI/dimension definitions |
| `CacheService` | Service | P1 | Redis caching for queries |

### 9.2 Existing Components to Extend

| Component | Extension Needed |
|-----------|-----------------|
| `KPICalculatorTool` | Add Arada-specific KPIs, real DB queries |
| `WhatIfSimulatorTool` | Add Net Sales scenario, real impact models |
| `ChartGeneratorTool` | Add waterfall, bridge chart types |
| `RealEstateQueryTool` | Connect to Arada data source |
| `ConversationRepository` | Add context extraction methods |

### 9.3 Agent Configuration Files

```yaml
# config/agents/analytics_orchestrator.yaml
name: analytics_orchestrator
type: orchestrator
description: Master analytics orchestrator for Arada POC

llm:
  provider: openai
  model: gpt-4-turbo
  temperature: 0.3

orchestrator_config:
  mode: llm_driven
  auto_discover: true
  max_parallel_agents: 3
  max_depth: 2
  aggregation_strategy: sequential

  child_agents:
    - descriptive_agent
    - deepdive_agent
    - decomposition_agent
    - whatif_agent
    - insight_agent

system_prompt: |
  You are the Analytics Orchestrator for Arada real estate analytics.
  Route queries to appropriate specialist agents and synthesize results.
  Always maintain conversation context for follow-up questions.
```

```yaml
# config/agents/descriptive_agent.yaml
name: descriptive_agent
type: full
description: KPI metrics and trend analysis

llm:
  provider: openai
  model: gpt-4-turbo
  temperature: 0.2

tools:
  - kpi_calculator
  - chart_generator
  - real_estate_query

skills:
  - descriptive_analytics
  - kpi_interpretation

knowledge_base:
  collection: arada_kpi_definitions
  search_mode: hybrid
  top_k: 5
```

---

## 10. Why This Architecture is the Best Design

### 10.1 Multi-Agent Benefits

| Benefit | Explanation |
|---------|-------------|
| **Specialization** | Each agent is optimized for specific analysis types, leading to better results |
| **Scalability** | New analysis capabilities added by creating new specialist agents |
| **Maintainability** | Changes to one analysis type don't affect others |
| **Parallel Processing** | Multiple agents can work simultaneously for complex queries |
| **Fault Isolation** | Failure in one agent doesn't crash the entire system |

### 10.2 Skills/Semantic Layer Benefits

| Benefit | Explanation |
|---------|-------------|
| **Consistency** | Single source of truth for KPI definitions |
| **Business Alignment** | Domain terminology embedded in system |
| **Explainability** | Reasoning patterns make analysis transparent |
| **Reusability** | Skills shared across agents |
| **Adaptability** | Business rules can be updated without code changes |

### 10.3 Conversational Memory Benefits

| Benefit | Explanation |
|---------|-------------|
| **Natural Interaction** | Users can ask follow-ups without repeating context |
| **Progressive Analysis** | Drill-down naturally through conversation |
| **Context Preservation** | Analysis state maintained across messages |
| **Reduced Cognitive Load** | System tracks where user is in analysis |

### 10.4 Architecture Comparison

```
Traditional BI Dashboard          vs.        Multi-Agent Conversational
─────────────────────────                    ────────────────────────────
Fixed visualizations                         Dynamic, on-demand charts
Pre-defined drill paths                      Natural language exploration
Manual filtering                             Conversational filtering
No context                                   Full conversation memory
Separate tools                               Unified chat interface
Static insights                              AI-generated insights
```

---

## 11. POC Success Criteria Alignment

| Requirement (from MOM) | Architecture Solution | Status |
|----------------------|----------------------|--------|
| Descriptive analytics (10 KPIs) | Descriptive Agent + KPI Calculator | Covered |
| Deep dive (Cancellation, region, project) | Deep Dive Agent + Drill-down skill | Covered |
| Decomposition (Max 3) | Decomposition Agent + Decomposition Tool | Covered |
| What-if (Net sales + 1 more) | What-If Agent + Simulator Tool | Covered |
| No pre-loaded visuals | Chat-first interface design | Covered |
| Conversational memory | Context Manager + Conversation Repository | Covered |
| Automated visualizations | Chart Generator + Auto-selection | Covered |
| Pre-identified insights | Insight Engine + Detection Rules | Covered |

---

## 12. Implementation Timeline

### Phase 1: Foundation (Days 1-3)
- [ ] Set up Arada data source connection
- [ ] Configure 10 KPIs in semantic layer
- [ ] Create Descriptive Agent configuration
- [ ] Implement basic conversation context

### Phase 2: Core Analysis (Days 4-7)
- [ ] Implement Deep Dive Agent with drill-down
- [ ] Build Decomposition Tool (waterfall)
- [ ] Create What-If scenarios for Net Sales
- [ ] Integrate Chart Generator enhancements

### Phase 3: Orchestration (Days 8-10)
- [ ] Configure Analytics Orchestrator
- [ ] Implement agent routing logic
- [ ] Add conversation memory accumulation
- [ ] Build pre-identified insights engine

### Phase 4: Polish & Demo (Days 11-14)
- [ ] End-to-end testing
- [ ] Demo script preparation
- [ ] Performance optimization
- [ ] Documentation

---

## 13. Appendix

### A. Sample Conversation Flow

```
User: Show me the trend of net sales in 2024

System: [Routes to Descriptive Agent]
        [Generates line chart]

        Net Sales showed consistent growth in 2024:
        - Q1: 120M AED
        - Q2: 145M AED (+21%)
        - Q3: 138M AED (-5%)
        - Q4: 165M AED (+20%)

        [LINE CHART]

        Key Insights:
        - Total 2024 Net Sales: 568M AED
        - Q3 dip attributed to seasonal factors
        - Strong Q4 recovery exceeded targets by 12%

User: Break this down by region

System: [Routes to Deep Dive Agent]
        [Uses conversation context: kpi=net_sales, year=2024]
        [Generates bar chart]

        Net Sales 2024 by Region:
        - Dubai: 280M AED (49%)
        - Abu Dhabi: 168M AED (30%)
        - Sharjah: 85M AED (15%)
        - RAK: 35M AED (6%)

        [BAR CHART]

        Insights:
        - Dubai dominates with nearly half of sales
        - Abu Dhabi shows 35% YoY growth

User: Why is Sharjah underperforming?

System: [Routes to Deep Dive Agent]
        [Drills into Sharjah data]

        Sharjah Analysis:
        - Cancellation rate: 52% (Critical - above 45% threshold)
        - Avg realization: 68% (Below portfolio avg of 78%)
        - Top cancellation reasons:
          1. Financing issues (45%)
          2. Price concerns (30%)
          3. Timeline delays (25%)

        [WATERFALL: Cancellation breakdown]

        Recommendation: Focus on financing assistance programs

User: What if we cap discounts at 10% in Sharjah?

System: [Routes to What-If Agent]
        [Uses context: region=Sharjah]

        Scenario: 10% Discount Cap in Sharjah

        Current State:
        - Avg discount: 14.5%
        - Net Sales: 85M AED

        Projected Impact:
        - Best case: +8% Net Sales (91.8M)
        - Expected: +3% Net Sales (87.5M)
        - Worst case: -5% Net Sales (80.7M) due to volume loss

        Confidence: 78%

        [SCENARIO COMPARISON CHART]
```

### B. API Endpoints

```
POST /api/v1/chat
  - Main chat endpoint
  - Handles all analytical queries

GET /api/v1/insights
  - Returns pre-computed insights
  - Filterable by category, priority

GET /api/v1/conversations/{id}
  - Get conversation with full history

POST /api/v1/conversations/{id}/context
  - Get accumulated analytical context
```

### C. Environment Variables

```bash
# Arada POC Configuration
ARADA_DATA_SOURCE=postgresql://...
ARADA_CACHE_TTL=300
ARADA_INSIGHT_REFRESH_INTERVAL=3600

# Agent Configuration
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4-turbo
ORCHESTRATOR_MAX_DEPTH=2

# Feature Flags
ENABLE_PRECOMPUTED_INSIGHTS=true
ENABLE_CONVERSATION_CONTEXT=true
ENABLE_AUTO_VISUALIZATION=true
```

---

**Document Version:** 1.0
**Last Updated:** 5 January 2026
**Author:** MagOne AI Team

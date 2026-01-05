# Arada POC - Multi-Agent Architecture

## POC Requirements Summary

Based on the POC plan document (2 Jan):

| Requirement | Details |
|-------------|---------|
| **POC Scope Document** | 5 Jan |
| **POC Showcase** | 16 Jan |
| **Descriptive Analytics** | 10 KPIs |
| **Deep Dive** | Cancellation by region, project, etc. |
| **Decomposition** | Max 3 |
| **What-If** | Net Sales + 1 more |
| **Chat System** | Pre-identified insights + explore further |
| **Visualizations** | Auto-generated, no pre-loaded dashboard |
| **Memory** | Conversational within each chat session |

---

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              ARADA ANALYTICS PLATFORM                                │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           CHAT INTERFACE                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  User: "What is the trend of net sales in 2026?"                         │  │  │
│  │  │  ─────────────────────────────────────────────                           │  │  │
│  │  │  Assistant: Net sales in 2026 show an upward trend...                    │  │  │
│  │  │  [Auto-generated Chart: Monthly Net Sales Trend]                         │  │  │
│  │  └──────────────────────────────────────────────────────────────────────────┘  │  │
│  │                    ↑ Conversational Memory (Session-based) ↑                   │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                         │                                            │
│                                         ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │                        MASTER ROUTER AGENT                                     │  │
│  │                                                                                │  │
│  │   Intent Classification → Routes to Specialized Agents                        │  │
│  │                                                                                │  │
│  │   ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐     │  │
│  │   │ Descriptive │  Deep Dive  │Decomposition│   What-If   │  Insights   │     │  │
│  │   │   (KPIs)    │  Analysis   │  Analysis   │  Scenarios  │  Retrieval  │     │  │
│  │   └──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘     │  │
│  └──────────┼─────────────┼─────────────┼─────────────┼─────────────┼────────────┘  │
│             │             │             │             │             │                │
│             ▼             ▼             ▼             ▼             ▼                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │  DESCRIPTIVE │ │  DEEP DIVE   │ │DECOMPOSITION │ │   WHAT-IF    │ │  INSIGHTS  │ │
│  │    AGENT     │ │    AGENT     │ │    AGENT     │ │    AGENT     │ │   AGENT    │ │
│  │  (ToolAgent) │ │(Orchestrator)│ │(Orchestrator)│ │ (ToolAgent)  │ │ (RAGAgent) │ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬──────┘ │
│         │                │                │                │               │        │
│         ▼                ▼                ▼                ▼               ▼        │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           TOOLS & DATA LAYER                                 │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐  │   │
│  │  │  CSV-SQL   │  │ Calculator │  │  DateTime  │  │    Knowledge Base      │  │   │
│  │  │ MCP Server │  │    Tool    │  │    Tool    │  │  (Pre-loaded Insights) │  │   │
│  │  └─────┬──────┘  └────────────┘  └────────────┘  └────────────────────────┘  │   │
│  │        │                                                                      │   │
│  │        ▼                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────────────┐    │   │
│  │  │                    ARADA DATA SOURCES                                │    │   │
│  │  │  Sales Data │ Cancellations │ Regions │ Projects │ Financial KPIs   │    │   │
│  │  └──────────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                          SKILLS LAYER (Semantic)                             │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │   │
│  │  │ KPI Formulas │ │  Business    │ │ Visualization│ │   Analysis Patterns  │ │   │
│  │  │ & Definitions│ │ Terminology  │ │    Rules     │ │   & Reasoning Steps  │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Specifications

### 1. Master Router Agent

| Property | Configuration |
|----------|---------------|
| **Type** | `RouterAgent` |
| **Purpose** | Classify user intent and route to appropriate specialized agent |
| **Input** | User query + conversation history |
| **Output** | Routed to one of 5 specialized agents |

#### Routing Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MASTER ROUTER DECISION TREE                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   User Query                                                                    │
│       │                                                                         │
│       ▼                                                                         │
│   ┌───────────────────────────────────────────────────────────────────┐        │
│   │  Intent: "Show me KPI", "What is the value of", "Trend of"        │        │
│   │  Keywords: net sales, revenue, units, growth rate, etc.           │        │
│   └─────────────────────────┬─────────────────────────────────────────┘        │
│                             │ YES → DESCRIPTIVE AGENT                          │
│                             │                                                   │
│   ┌───────────────────────────────────────────────────────────────────┐        │
│   │  Intent: "Why", "Analyze", "Break down", "Drill into"             │        │
│   │  Keywords: cancellation, by region, by project, reasons           │        │
│   └─────────────────────────┬─────────────────────────────────────────┘        │
│                             │ YES → DEEP DIVE AGENT                            │
│                             │                                                   │
│   ┌───────────────────────────────────────────────────────────────────┐        │
│   │  Intent: "Decompose", "Components of", "Break into factors"       │        │
│   │  Keywords: contribution, attribution, variance                    │        │
│   └─────────────────────────┬─────────────────────────────────────────┘        │
│                             │ YES → DECOMPOSITION AGENT                        │
│                             │                                                   │
│   ┌───────────────────────────────────────────────────────────────────┐        │
│   │  Intent: "What if", "If we increase", "Scenario", "Impact of"     │        │
│   │  Keywords: change, increase, decrease, simulate                   │        │
│   └─────────────────────────┬─────────────────────────────────────────┘        │
│                             │ YES → WHAT-IF AGENT                              │
│                             │                                                   │
│   ┌───────────────────────────────────────────────────────────────────┐        │
│   │  Intent: "Key insights", "Summary", "What should I know"          │        │
│   │  Fallback: General questions about business performance           │        │
│   └─────────────────────────┬─────────────────────────────────────────┘        │
│                             │ DEFAULT → INSIGHTS AGENT                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Skills Injected
- Query classification patterns
- KPI keyword mapping
- Intent recognition rules

---

### 2. Descriptive Analytics Agent

| Property | Configuration |
|----------|---------------|
| **Type** | `ToolAgent` |
| **Purpose** | Answer KPI queries with current/historical data |
| **Tools** | CSV-SQL MCP, Calculator, DateTime |
| **KPIs Covered** | 10 defined KPIs (Net Sales, Revenue, Units Sold, etc.) |

#### Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      DESCRIPTIVE AGENT WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   INPUT: "What is the trend of net sales in 2026?"                             │
│       │                                                                         │
│       ▼                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 1: Parse Query                                                │      │
│   │  ├── KPI Identified: "net_sales"                                    │      │
│   │  ├── Time Period: 2026                                              │      │
│   │  ├── Analysis Type: Trend (time series)                             │      │
│   │  └── Granularity: Monthly (default for trend)                       │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 2: Generate SQL Query (via Skills)                            │      │
│   │  ┌─────────────────────────────────────────────────────────────┐    │      │
│   │  │  SELECT                                                      │    │      │
│   │  │    DATE_TRUNC('month', transaction_date) as month,          │    │      │
│   │  │    SUM(gross_sales - returns - discounts) as net_sales      │    │      │
│   │  │  FROM sales_transactions                                     │    │      │
│   │  │  WHERE YEAR(transaction_date) = 2026                        │    │      │
│   │  │  GROUP BY month ORDER BY month                              │    │      │
│   │  └─────────────────────────────────────────────────────────────┘    │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 3: Execute via CSV-SQL MCP Server                             │      │
│   │  └── Returns: [{month: "Jan", net_sales: 1.2M}, ...]               │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 4: Calculate Trend Metrics                                    │      │
│   │  ├── MoM Growth: +5.2% average                                      │      │
│   │  ├── YTD Total: $14.5M                                              │      │
│   │  └── Trend Direction: Upward                                        │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 5: Format Response with Visualization Data                    │      │
│   │  ├── Natural Language Summary                                       │      │
│   │  └── Chart Data: {type: "line", data: [...], title: "..."}         │      │
│   └─────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
│   OUTPUT: "Net sales in 2026 show an upward trend with 5.2% average            │
│            monthly growth. Total YTD is $14.5M." + [Line Chart]                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Sample Queries Handled

| User Query | Agent Action |
|------------|--------------|
| "What is net sales for 2026?" | SQL aggregation → single value |
| "Show me monthly revenue" | SQL with GROUP BY month → bar chart |
| "Compare Q3 vs Q4 units sold" | SQL for both periods → comparison chart |
| "Top 5 regions by sales" | SQL with ORDER BY LIMIT → ranked list |

---

### 3. Deep Dive Analysis Agent

| Property | Configuration |
|----------|---------------|
| **Type** | `OrchestratorAgent` |
| **Purpose** | Multi-dimensional drill-down analysis |
| **Sub-Agents** | Dimension Analyzer, Anomaly Detector, Correlation Finder |
| **Use Cases** | Cancellation deep dive by region/project |

#### Orchestration Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DEEP DIVE AGENT ORCHESTRATION                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   INPUT: "Why are cancellations high in Q4? Drill down by region and project"  │
│       │                                                                         │
│       ▼                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │               ORCHESTRATOR: Plan Analysis Steps                     │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│         ┌───────────────────────┼───────────────────────┐                      │
│         │                       │                       │                      │
│         ▼                       ▼                       ▼                      │
│   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                    │
│   │  SUB-AGENT 1  │   │  SUB-AGENT 2  │   │  SUB-AGENT 3  │                    │
│   │   Regional    │   │    Project    │   │   Temporal    │                    │
│   │   Analysis    │   │   Analysis    │   │   Analysis    │                    │
│   │               │   │               │   │               │                    │
│   │ "Cancellation │   │ "Cancellation │   │ "Cancellation │                    │
│   │  by region"   │   │  by project"  │   │   by week"    │                    │
│   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘                    │
│           │                   │                   │                            │
│           ▼                   ▼                   ▼                            │
│   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                    │
│   │ Region North: │   │ Project A: 8% │   │ Week 45: Peak │                    │
│   │   12% cancel  │   │ Project B: 15%│   │   at 18%      │                    │
│   │ Region South: │   │ Project C: 5% │   │ Week 48: 12%  │                    │
│   │   6% cancel   │   │               │   │               │                    │
│   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘                    │
│           │                   │                   │                            │
│           └───────────────────┼───────────────────┘                            │
│                               │                                                 │
│                               ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │                    AGGREGATION & CORRELATION                        │      │
│   │  ┌─────────────────────────────────────────────────────────────┐    │      │
│   │  │  Finding: Region North + Project B = 23% cancellation       │    │      │
│   │  │  Correlation: Week 45 spike coincides with Project B launch │    │      │
│   │  │  Root Cause: Project B in North region had delivery issues  │    │      │
│   │  └─────────────────────────────────────────────────────────────┘    │      │
│   └─────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
│   OUTPUT:                                                                       │
│   "Cancellation analysis reveals Project B in the North region is the          │
│    primary driver with 23% cancellation rate. This correlates with             │
│    Week 45 when Project B launched with reported delivery delays."             │
│                                                                                 │
│   + [Heatmap: Region x Project] + [Timeline Chart: Weekly Cancellations]       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Sub-Agent Definitions

| Sub-Agent | Type | Purpose | Output |
|-----------|------|---------|--------|
| **Dimension Analyzer** | ToolAgent | Break down KPI by each dimension | Ranked list by dimension value |
| **Anomaly Detector** | ToolAgent | Find outliers and spikes | Anomalies with timestamps |
| **Correlation Finder** | LLMAgent | Cross-dimension patterns | Correlated dimension pairs |

---

### 4. Decomposition Analysis Agent

| Property | Configuration |
|----------|---------------|
| **Type** | `OrchestratorAgent` |
| **Purpose** | Break down metrics into contributing factors |
| **Max Decompositions** | 3 (as per POC scope) |
| **Techniques** | Variance decomposition, contribution analysis |

#### Decomposition Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     DECOMPOSITION AGENT WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   INPUT: "Decompose the net sales change from Q3 to Q4"                        │
│       │                                                                         │
│       ▼                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 1: Identify Decomposition Type                                │      │
│   │  ├── Variance Decomposition (Period over Period)                    │      │
│   │  └── Components: Price, Volume, Mix, New Products                   │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 2: Calculate Each Component (Parallel Execution)              │      │
│   │                                                                     │      │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │      │
│   │   │   PRICE     │  │   VOLUME    │  │    MIX      │  │    NEW    │ │      │
│   │   │   EFFECT    │  │   EFFECT    │  │   EFFECT    │  │ PRODUCTS  │ │      │
│   │   │             │  │             │  │             │  │           │ │      │
│   │   │  +$1.2M     │  │  +$0.8M     │  │  -$0.3M     │  │  +$0.5M   │ │      │
│   │   │  (Price ↑)  │  │ (Units ↑)   │  │(Low margin  │  │(Product X)│ │      │
│   │   │             │  │             │  │  mix shift) │  │           │ │      │
│   │   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 3: Aggregate & Validate                                       │      │
│   │  ├── Total Variance: +$2.2M                                         │      │
│   │  ├── Sum of Components: $1.2M + $0.8M - $0.3M + $0.5M = $2.2M ✓    │      │
│   │  └── Reconciliation: PASSED                                         │      │
│   └─────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
│   OUTPUT:                                                                       │
│   "Net sales increased by $2.2M from Q3 to Q4:                                 │
│    • Price Effect: +$1.2M (average price increase of 3%)                       │
│    • Volume Effect: +$0.8M (12% more units sold)                               │
│    • Mix Effect: -$0.3M (shift toward lower-margin products)                   │
│    • New Products: +$0.5M (Product X launch contribution)"                     │
│                                                                                 │
│   + [Waterfall Chart: Q3 → Components → Q4]                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Decomposition Types Supported

| Type | Use Case | Components |
|------|----------|------------|
| **Variance** | Period-over-period change | Price, Volume, Mix, New |
| **Contribution** | What drives a total | By region, product, channel |
| **Attribution** | Marketing impact | Channel attribution |

---

### 5. What-If Scenario Agent

| Property | Configuration |
|----------|---------------|
| **Type** | `ToolAgent` |
| **Purpose** | Simulate business scenarios and predict outcomes |
| **Tools** | Calculator, CSV-SQL MCP (for baseline data) |
| **Capabilities** | Single variable changes, multi-variable simulation |

#### What-If Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        WHAT-IF SCENARIO WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   INPUT: "What if we increase net sales by 10% next quarter?"                  │
│       │                                                                         │
│       ▼                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 1: Parse Scenario Parameters                                  │      │
│   │  ├── Variable: net_sales                                            │      │
│   │  ├── Change: +10%                                                   │      │
│   │  ├── Period: Next Quarter (Q1 2027)                                 │      │
│   │  └── Baseline: Current Q4 2026 value                                │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 2: Fetch Baseline Data                                        │      │
│   │  └── Q4 2026 Net Sales: $5.2M                                       │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 3: Apply Business Rules (from Skills)                         │      │
│   │  ┌─────────────────────────────────────────────────────────────┐    │      │
│   │  │  IF net_sales ↑ 10% THEN:                                   │    │      │
│   │  │    • Gross Margin Impact: +8% (economies of scale)          │    │      │
│   │  │    • Operating Costs: +3% (variable costs)                  │    │      │
│   │  │    • Inventory Requirements: +12%                           │    │      │
│   │  │    • Cash Flow Impact: +$0.4M                               │    │      │
│   │  └─────────────────────────────────────────────────────────────┘    │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 4: Calculate Projected Values                                 │      │
│   │                                                                     │      │
│   │   ┌─────────────────────────────────────────────────────────────┐   │      │
│   │   │  METRIC              │  BASELINE  │  PROJECTED  │  CHANGE   │   │      │
│   │   ├─────────────────────────────────────────────────────────────┤   │      │
│   │   │  Net Sales           │  $5.2M     │  $5.72M     │  +10%     │   │      │
│   │   │  Gross Profit        │  $1.8M     │  $2.07M     │  +15%     │   │      │
│   │   │  Operating Costs     │  $0.9M     │  $0.93M     │  +3%      │   │      │
│   │   │  Net Profit          │  $0.9M     │  $1.14M     │  +27%     │   │      │
│   │   └─────────────────────────────────────────────────────────────┘   │      │
│   └─────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
│   OUTPUT:                                                                       │
│   "If net sales increase by 10% to $5.72M next quarter:                        │
│    • Gross Profit would rise 15% to $2.07M (scale efficiencies)                │
│    • Operating Costs increase modestly by 3%                                    │
│    • Net Profit impact: +27% ($0.24M additional profit)                        │
│    • Required inventory investment: +$0.3M"                                     │
│                                                                                 │
│   + [Comparison Bar Chart: Baseline vs Projected]                              │
│   + [Sensitivity Table: 5%, 10%, 15%, 20% scenarios]                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Scenario Types

| Scenario | Example Query | Output |
|----------|---------------|--------|
| **Single Variable** | "What if sales +10%?" | Impact on related metrics |
| **Multi-Variable** | "What if price +5% and volume -3%?" | Combined effect analysis |
| **Sensitivity** | "Show sensitivity of profit to sales" | Range of outcomes table |

---

### 6. Insights Retrieval Agent

| Property | Configuration |
|----------|---------------|
| **Type** | `RAGAgent` |
| **Purpose** | Retrieve pre-loaded business insights |
| **Knowledge Base** | Pre-identified insights documents |
| **Use Cases** | Executive summaries, key findings, recommendations |

#### RAG Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       INSIGHTS AGENT (RAG) WORKFLOW                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   INPUT: "What are the key insights for this quarter?"                         │
│       │                                                                         │
│       ▼                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 1: Embed Query                                                │      │
│   │  └── Vector: [0.12, -0.34, 0.56, ...]                              │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 2: Retrieve from Knowledge Base                               │      │
│   │  ┌─────────────────────────────────────────────────────────────┐    │      │
│   │  │  PRE-LOADED INSIGHTS DOCUMENTS:                             │    │      │
│   │  │  ├── quarterly_summary.md (similarity: 0.92)                │    │      │
│   │  │  ├── kpi_highlights.md (similarity: 0.87)                   │    │      │
│   │  │  └── risk_alerts.md (similarity: 0.81)                      │    │      │
│   │  └─────────────────────────────────────────────────────────────┘    │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  STEP 3: Generate Response with Retrieved Context                   │      │
│   │  └── LLM synthesizes insights from retrieved documents             │      │
│   └─────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
│   OUTPUT:                                                                       │
│   "Key insights for Q4 2026:                                                   │
│                                                                                 │
│    GROWTH                                                                       │
│    • Net sales up 12% YoY, exceeding target by 2%                             │
│    • North region driving 60% of growth                                        │
│                                                                                 │
│    RISKS                                                                        │
│    • Cancellation rate in Project B requires attention (15%)                   │
│    • Inventory turnover slowing in South region                                │
│                                                                                 │
│    RECOMMENDATIONS                                                              │
│    • Investigate Project B delivery issues                                     │
│    • Consider promotional activity in South region"                            │
│                                                                                 │
│   Sources: quarterly_summary.md, kpi_highlights.md, risk_alerts.md             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Skills Configuration

### Skill: arada_kpi_definitions

```yaml
name: arada_kpi_definitions
description: KPI formulas and definitions for Arada business metrics

terminology:
  net_sales:
    term: "Net Sales"
    definition: "Gross sales minus returns and discounts"
    formula: "gross_sales - returns - discounts"
    table: "sales_transactions"

  cancellation_rate:
    term: "Cancellation Rate"
    definition: "Percentage of orders cancelled before delivery"
    formula: "(cancelled_orders / total_orders) * 100"
    table: "orders"

  aov:
    term: "Average Order Value"
    definition: "Total revenue divided by number of orders"
    formula: "total_revenue / order_count"
    table: "orders"

  conversion_rate:
    term: "Conversion Rate"
    definition: "Percentage of visitors who completed a purchase"
    formula: "(purchasers / visitors) * 100"
    table: "analytics"

reasoning_patterns:
  trend_analysis: |
    1. Fetch time series data for the specified period
    2. Calculate period-over-period growth rates
    3. Identify patterns (upward, downward, seasonal)
    4. Summarize overall trend direction and magnitude

  comparison_analysis: |
    1. Fetch data for both comparison periods/segments
    2. Calculate absolute and percentage differences
    3. Rank by magnitude of difference
    4. Highlight significant variances

examples:
  - input: "What is net sales for 2026?"
    output: "SELECT SUM(gross_sales - returns - discounts) as net_sales FROM sales_transactions WHERE YEAR(transaction_date) = 2026"

  - input: "Show monthly cancellation rate"
    output: "SELECT DATE_TRUNC('month', order_date) as month, (COUNT(CASE WHEN status='cancelled' THEN 1 END) * 100.0 / COUNT(*)) as cancellation_rate FROM orders GROUP BY month"
```

### Skill: arada_data_schema

```yaml
name: arada_data_schema
description: Database schema and table relationships for Arada data

terminology:
  regions:
    term: "Regions"
    definition: "Geographic divisions: North, South, East, West"

  projects:
    term: "Projects"
    definition: "Product development initiatives (A, B, C, etc.)"

  dimensions:
    term: "Analysis Dimensions"
    definition: "Available drill-down dimensions: region, project, time_period, customer_segment"

files:
  - name: schema.sql
    description: Database table definitions

  - name: relationships.md
    description: Table relationships and join patterns
```

### Skill: arada_visualization_rules

```yaml
name: arada_visualization_rules
description: Rules for selecting appropriate chart types

reasoning_patterns:
  chart_selection: |
    IF trend over time → line_chart
    IF comparison across categories → bar_chart
    IF part-to-whole relationship → pie_chart
    IF two variables correlation → scatter_plot
    IF decomposition/waterfall → waterfall_chart
    IF geographic distribution → map_visualization
    IF matrix/cross-tabulation → heatmap

  formatting_rules: |
    - Currency: Format with $ and appropriate suffix (K, M, B)
    - Percentages: Show 1 decimal place with % symbol
    - Dates: Use MMM YYYY for monthly, YYYY for yearly
    - Large numbers: Use thousand separators
```

### Skill: arada_business_rules

```yaml
name: arada_business_rules
description: Business logic for calculations and scenarios

terminology:
  fiscal_year:
    term: "Fiscal Year"
    definition: "April to March"

  target_margin:
    term: "Target Margin"
    definition: "32% gross margin target"

  acceptable_cancellation:
    term: "Acceptable Cancellation Rate"
    definition: "Below 5% is considered acceptable"

reasoning_patterns:
  what_if_calculations: |
    For net_sales changes:
      - Gross margin scales at 0.8x rate (economies of scale)
      - Variable costs scale at 0.3x rate
      - Fixed costs remain constant
      - Inventory requirements scale at 1.2x rate

  threshold_alerts: |
    - Cancellation rate > 10%: HIGH alert
    - Cancellation rate > 5%: MEDIUM alert
    - Margin below 30%: WARNING
    - YoY growth < 0%: CONCERN
```

---

## End-to-End Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         END-TO-END REQUEST FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   USER                                                                          │
│     │                                                                           │
│     │  "Show me net sales monthly in 2026"                                     │
│     ▼                                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  CHAT INTERFACE (Next.js Frontend)                                  │      │
│   │  └── POST /api/v1/workflow/execute                                  │      │
│   │      {                                                              │      │
│   │        "agent_id": "master-router",                                 │      │
│   │        "user_input": "Show me net sales monthly in 2026",          │      │
│   │        "conversation_history": [...previous messages...]            │      │
│   │      }                                                              │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  FASTAPI BACKEND                                                    │      │
│   │  └── Submit to Temporal Workflow                                    │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  TEMPORAL WORKFLOW                                                  │      │
│   │  ├── Safety Check Activity (Input Sanitization)                     │      │
│   │  ├── Router Agent Activity                                          │      │
│   │  │   └── Intent: "descriptive" → Route to Descriptive Agent        │      │
│   │  ├── Descriptive Agent Activity                                     │      │
│   │  │   ├── Skill Injection: kpi_definitions, data_schema             │      │
│   │  │   ├── Tool Call: CSV-SQL MCP (generate & execute query)         │      │
│   │  │   ├── Tool Call: Calculator (compute metrics)                   │      │
│   │  │   └── Generate Response with Chart Data                         │      │
│   │  └── Analytics Recording (async)                                    │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  RESPONSE TO FRONTEND                                               │      │
│   │  {                                                                  │      │
│   │    "content": "Here are the monthly net sales for 2026...",        │      │
│   │    "confidence": 0.95,                                              │      │
│   │    "metadata": {                                                    │      │
│   │      "visualization": {                                            │      │
│   │        "type": "bar_chart",                                        │      │
│   │        "title": "Monthly Net Sales 2026",                          │      │
│   │        "data": [                                                   │      │
│   │          {"month": "Jan", "value": 1200000},                       │      │
│   │          {"month": "Feb", "value": 1350000},                       │      │
│   │          ...                                                       │      │
│   │        ]                                                           │      │
│   │      }                                                             │      │
│   │    },                                                              │      │
│   │    "sources": ["sales_transactions table"]                         │      │
│   │  }                                                                  │      │
│   └─────────────────────────────┬───────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  FRONTEND RENDERS                                                   │      │
│   │  ├── Natural Language Response                                      │      │
│   │  └── Auto-generated Bar Chart                                       │      │
│   └─────────────────────────────────────────────────────────────────────┘      │
│                                 │                                               │
│                                 ▼                                               │
│   USER SEES:                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │  "Here are the monthly net sales for 2026. Total YTD is $14.5M     │      │
│   │   with consistent month-over-month growth averaging 5.2%."          │      │
│   │                                                                     │      │
│   │   [Bar Chart: Monthly Net Sales]                                   │      │
│   │   | $1.5M |                                                  ████  │      │
│   │   | $1.2M |                                            ████  ████  │      │
│   │   | $0.9M |                               ████   ████  ████  ████  │      │
│   │   | $0.6M |         ████   ████   ████   ████   ████  ████  ████  │      │
│   │   | $0.3M |  ████   ████   ████   ████   ████   ████  ████  ████  │      │
│   │   └───────┴──Jan────Feb────Mar────Apr────May────Jun───Jul───Aug── │      │
│   └─────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## POC Requirements Mapping

| POC Requirement | Implementation |
|-----------------|----------------|
| **Multi-agent architecture** | RouterAgent → 5 Specialized Agents (Descriptive, DeepDive, Decomposition, What-if, Insights) |
| **Skills/Semantic layer** | 4 Skills: KPI Definitions, Data Schema, Visualization Rules, Business Rules |
| **Descriptive Analytics (10 KPIs)** | ToolAgent with CSV-SQL MCP + KPI Skills |
| **Deep Dive (Cancellation)** | OrchestratorAgent with parallel dimension analysis |
| **Decomposition (Max 3)** | OrchestratorAgent with variance analysis |
| **What-if (Net Sales +1)** | ToolAgent with business rules from Skills |
| **Chat system** | Stateless API with conversation_history |
| **No pre-loaded dashboard** | Conversational interface, insights on demand |
| **Conversational memory** | AgentContext.conversation_history per session |
| **Automated visualizations** | Response metadata with chart type & data |

---

## Sample User Queries

| Query | Agent | Response Type |
|-------|-------|---------------|
| "What is the trend of net sales in 2026?" | Descriptive | Line chart + trend summary |
| "Show me net sales monthly in 2026" | Descriptive | Bar chart + monthly data |
| "Why are cancellations high in Q4?" | Deep Dive | Heatmap + root cause analysis |
| "Break down revenue change Q3 to Q4" | Decomposition | Waterfall chart + factors |
| "What if we increase sales by 10%?" | What-If | Comparison chart + projections |
| "What are the key insights this quarter?" | Insights | Executive summary from KB |

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend API** | FastAPI (Python) |
| **Workflow Engine** | Temporal |
| **LLM Providers** | OpenAI (GPT-4), Anthropic (Claude) |
| **Vector Store** | Weaviate |
| **Database** | PostgreSQL |
| **Frontend** | Next.js |
| **MCP Servers** | CSV-SQL, Google Calendar, Gmail, Filesystem |
| **Monitoring** | Prometheus + Custom Analytics |

---

## Next Steps for Implementation

1. **Configure Master Router Agent** with intent classification routing table
2. **Create 5 Specialized Agents** with appropriate tools and skills
3. **Define Skills** with Arada-specific KPI formulas and business rules
4. **Connect CSV-SQL MCP** to Arada data sources
5. **Load Knowledge Base** with pre-identified insights documents
6. **Build Frontend Chat Interface** with visualization rendering
7. **Test End-to-End Flows** with sample queries from POC scope

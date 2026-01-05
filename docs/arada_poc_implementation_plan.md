# Arada POC - Implementation Plan

**Date:** 5 January 2026
**Showcase:** 16 January 2026

---

## Executive Summary

| Component | Count |
|-----------|-------|
| **Workflows** | 1 (Single orchestrated workflow) |
| **Agents** | 5 (1 Orchestrator + 4 Specialists) |
| **Skills** | 6 |
| **Built-in Tools** | 5 |

---

## System Flowchart

```
                                 ┌─────────────────────────────────┐
                                 │           USER QUERY            │
                                 │  "What is net sales trend?"     │
                                 └─────────────────────────────────┘
                                                 │
                                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                            │
│                              ARADA ANALYTICS WORKFLOW                                      │
│                                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                                      │ │
│  │                        ANALYTICS ORCHESTRATOR (Master Agent)                         │ │
│  │                           Type: OrchestratorAgent                                    │ │
│  │                                                                                      │ │
│  │   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                 │ │
│  │   │ Intent Classifier│───>│  Agent Router   │───>│ Result Synthesizer│               │ │
│  │   └─────────────────┘    └─────────────────┘    └─────────────────┘                 │ │
│  │                                   │                                                  │ │
│  └───────────────────────────────────┼──────────────────────────────────────────────────┘ │
│                                      │                                                    │
│         ┌────────────────────────────┼────────────────────────────┐                      │
│         │                            │                            │                      │
│         ▼                            ▼                            ▼                      │
│  ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐          │
│  │   DESCRIPTIVE   │          │    DEEP DIVE    │          │  DECOMPOSITION  │          │
│  │     AGENT       │          │     AGENT       │          │     AGENT       │          │
│  │  (FullAgent)    │          │  (FullAgent)    │          │  (ToolAgent)    │          │
│  │                 │          │                 │          │                 │          │
│  │ Skills:         │          │ Skills:         │          │ Skills:         │          │
│  │ • KPI Skill     │          │ • Drill-down    │          │ • Variance      │          │
│  │ • Trend Skill   │          │ • Root Cause    │          │ • Attribution   │          │
│  │                 │          │                 │          │                 │          │
│  │ Tools:          │          │ Tools:          │          │ Tools:          │          │
│  │ • KPI Calculator│          │ • Query Engine  │          │ • Decomposition │          │
│  │ • Chart Gen     │          │ • Chart Gen     │          │ • Chart Gen     │          │
│  │ • Query Engine  │          │ • KPI Calculator│          │ • Query Engine  │          │
│  └─────────────────┘          └─────────────────┘          └─────────────────┘          │
│         │                            │                            │                      │
│         │                            │                            │                      │
│         │                            ▼                            │                      │
│         │                     ┌─────────────────┐                 │                      │
│         │                     │    WHAT-IF      │                 │                      │
│         │                     │     AGENT       │                 │                      │
│         │                     │  (ToolAgent)    │                 │                      │
│         │                     │                 │                 │                      │
│         │                     │ Skills:         │                 │                      │
│         │                     │ • Scenario Skill│                 │                      │
│         │                     │                 │                 │                      │
│         │                     │ Tools:          │                 │                      │
│         │                     │ • What-If Sim   │                 │                      │
│         │                     │ • Chart Gen     │                 │                      │
│         │                     │ • KPI Calculator│                 │                      │
│         │                     └─────────────────┘                 │                      │
│         │                            │                            │                      │
│         └────────────────────────────┼────────────────────────────┘                      │
│                                      │                                                    │
│                                      ▼                                                    │
│                          ┌─────────────────────┐                                         │
│                          │   TOOL LAYER        │                                         │
│                          │                     │                                         │
│                          │  ┌───────────────┐  │                                         │
│                          │  │KPI Calculator │  │                                         │
│                          │  └───────────────┘  │                                         │
│                          │  ┌───────────────┐  │                                         │
│                          │  │Chart Generator│  │                                         │
│                          │  └───────────────┘  │                                         │
│                          │  ┌───────────────┐  │                                         │
│                          │  │ Query Engine  │  │                                         │
│                          │  └───────────────┘  │                                         │
│                          │  ┌───────────────┐  │                                         │
│                          │  │What-If Simul. │  │                                         │
│                          │  └───────────────┘  │                                         │
│                          │  ┌───────────────┐  │                                         │
│                          │  │Decomp. Tool   │  │                                         │
│                          │  └───────────────┘  │                                         │
│                          └─────────────────────┘                                         │
│                                      │                                                    │
│                                      ▼                                                    │
│                          ┌─────────────────────┐                                         │
│                          │    DATA LAYER       │                                         │
│                          │  (Arada Sales DB)   │                                         │
│                          └─────────────────────┘                                         │
│                                                                                            │
└────────────────────────────────────────────────────────────────────────────────────────────┘
                                                 │
                                                 ▼
                                 ┌─────────────────────────────────┐
                                 │           RESPONSE              │
                                 │  Chart + Insights + Next Steps  │
                                 └─────────────────────────────────┘
```

---

## Query Routing Flow

```
                              USER QUERY
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  INTENT CLASSIFICATION  │
                    └─────────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
    ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
    │ KPI/Trend     │     │ Drill/Filter  │     │ Why/Breakdown │
    │ Keywords:     │     │ Keywords:     │     │ Keywords:     │
    │ • "trend"     │     │ • "by region" │     │ • "why"       │
    │ • "show me"   │     │ • "drill"     │     │ • "break down"│
    │ • "what is"   │     │ • "filter"    │     │ • "decompose" │
    │ • "compare"   │     │ • "segment"   │     │ • "attribute" │
    └───────────────┘     └───────────────┘     └───────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
    ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
    │  DESCRIPTIVE  │     │   DEEP DIVE   │     │ DECOMPOSITION │
    │    AGENT      │     │    AGENT      │     │    AGENT      │
    └───────────────┘     └───────────────┘     └───────────────┘


                    ┌───────────────┐
                    │ Scenario      │
                    │ Keywords:     │
                    │ • "what if"   │
                    │ • "simulate"  │
                    │ • "impact"    │
                    │ • "scenario"  │
                    └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   WHAT-IF     │
                    │    AGENT      │
                    └───────────────┘
```

---

## Detailed Component Breakdown

### WORKFLOWS (1 Total)

| # | Workflow Name | Description |
|---|---------------|-------------|
| 1 | **Arada Analytics Workflow** | Single orchestrated workflow that handles all 4 analysis types. The orchestrator classifies intent and routes to the appropriate specialist agent. Maintains conversation context across turns. |

---

### AGENTS (5 Total)

| # | Agent Name | Type | Analysis Scope | Description |
|---|------------|------|----------------|-------------|
| 1 | **Analytics Orchestrator** | `OrchestratorAgent` | All | Master coordinator that classifies user intent, routes queries to specialist agents, maintains conversation context, and synthesizes multi-agent responses when complex queries span multiple analysis types. |
| 2 | **Descriptive Agent** | `FullAgent` | Descriptive Analytics | Handles KPI calculations, trend analysis, and period comparisons. Returns metrics with visualizations and interprets what the numbers mean in business context. Covers all 10 KPIs. |
| 3 | **Deep Dive Agent** | `FullAgent` | Deep Dive Analysis | Performs hierarchical drill-down analysis (Region→Project→Cluster→Unit). Identifies outliers, compares segments, and suggests next drill-down options. Preserves context from previous queries. |
| 4 | **Decomposition Agent** | `ToolAgent` | Decomposition Analysis | Creates waterfall and bridge charts to explain what drove KPI changes. Performs contribution analysis, variance decomposition, and mix-vs-rate analysis. Ensures components sum to total. |
| 5 | **What-If Agent** | `ToolAgent` | What-If Analysis | Runs scenario simulations with configurable parameters. Returns best/expected/worst case projections with confidence intervals. States assumptions transparently. |

---

### SKILLS (6 Total)

| # | Skill Name | Used By Agent | Description |
|---|------------|---------------|-------------|
| 1 | **KPI Interpretation Skill** | Descriptive Agent | Domain expertise for calculating and interpreting Arada's 10 KPIs. Contains formulas, thresholds, benchmarks, and business context for each metric. Knows when to flag warnings. |
| 2 | **Trend Analysis Skill** | Descriptive Agent | Expertise in time-series analysis - MoM, QoQ, YoY comparisons. Detects trend reversals, seasonality patterns, and growth rates. Selects appropriate chart types for temporal data. |
| 3 | **Drill-Down Skill** | Deep Dive Agent | Knowledge of Arada's dimension hierarchies and drill paths. Knows how to navigate Region→Project→Cluster→Unit. Maintains context and suggests logical next drill-downs. |
| 4 | **Root Cause Skill** | Deep Dive Agent | Techniques for identifying why metrics are over/under performing. Compares segment performance, detects outliers, and investigates contributing factors. |
| 5 | **Variance Attribution Skill** | Decomposition Agent | Methodology for decomposing changes into component contributions. Knows waterfall math, bridge chart construction, and mix-vs-rate decomposition formulas. |
| 6 | **Scenario Modeling Skill** | What-If Agent | Expertise in building scenarios with parameter inputs. Knows price elasticity models, volume-value tradeoffs, and how to present uncertainty with confidence levels. |

---

### BUILT-IN TOOLS (5 Total)

| # | Tool Name | Used By | Description |
|---|-----------|---------|-------------|
| 1 | **KPI Calculator** | Descriptive, Deep Dive, What-If | Calculates all 10 Arada KPIs with auto-selection based on question type. Returns values with benchmark comparison, threshold status (normal/warning/critical), and delta calculations. |
| 2 | **Chart Generator** | All Agents | Generates visualizations (bar, line, pie, horizontal bar, area, scatter, waterfall). Returns both ASCII representation for text display and Chart.js config for UI rendering. Auto-generates insights. |
| 3 | **Query Engine** | Descriptive, Deep Dive, Decomposition | Executes data queries against Arada sales data. Supports aggregation (SUM/AVG/COUNT), filtering (WHERE), grouping (GROUP BY), and trending (time-series). Returns structured data. |
| 4 | **What-If Simulator** | What-If Agent | Runs scenario simulations with parameter inputs (price change %, volume change %, discount cap). Returns projected impact with best/expected/worst cases and confidence intervals. |
| 5 | **Decomposition Tool** | Decomposition Agent | Performs waterfall decomposition, variance analysis, and contribution attribution. Takes two periods/segments and breaks down the difference into component parts that sum to total. |

---

## Analysis Scope → Agent → Tools Mapping

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ANALYSIS SCOPE MAPPING                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────┐                                                        │
│  │ 1. DESCRIPTIVE      │ ──────> Descriptive Agent ──────> • KPI Calculator    │
│  │    (10 KPIs)        │                                   • Chart Generator   │
│  │                     │                                   • Query Engine      │
│  │ Examples:           │                                                        │
│  │ • Net sales trend   │         Skills:                                        │
│  │ • Monthly bookings  │         • KPI Interpretation                           │
│  │ • Cancellation rate │         • Trend Analysis                               │
│  └─────────────────────┘                                                        │
│                                                                                 │
│  ┌─────────────────────┐                                                        │
│  │ 2. DEEP DIVE        │ ──────> Deep Dive Agent ───────> • Query Engine       │
│  │    (Drill-down)     │                                  • Chart Generator    │
│  │                     │                                  • KPI Calculator     │
│  │ Examples:           │                                                        │
│  │ • By region         │         Skills:                                        │
│  │ • By project        │         • Drill-Down                                   │
│  │ • Filter to Dubai   │         • Root Cause                                   │
│  └─────────────────────┘                                                        │
│                                                                                 │
│  ┌─────────────────────┐                                                        │
│  │ 3. DECOMPOSITION    │ ──────> Decomposition Agent ───> • Decomposition Tool │
│  │    (Max 3 types)    │                                  • Chart Generator    │
│  │                     │                                  • Query Engine       │
│  │ Examples:           │                                                        │
│  │ • Why did sales ↓?  │         Skills:                                        │
│  │ • Break down change │         • Variance Attribution                         │
│  │ • Waterfall         │                                                        │
│  └─────────────────────┘                                                        │
│                                                                                 │
│  ┌─────────────────────┐                                                        │
│  │ 4. WHAT-IF          │ ──────> What-If Agent ─────────> • What-If Simulator  │
│  │    (Net Sales + 1)  │                                  • Chart Generator    │
│  │                     │                                  • KPI Calculator     │
│  │ Examples:           │                                                        │
│  │ • Price +5% impact  │         Skills:                                        │
│  │ • Discount cap sim  │         • Scenario Modeling                            │
│  │ • Volume scenarios  │                                                        │
│  └─────────────────────┘                                                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Conversation Context Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        CONVERSATION MEMORY FLOW                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Turn 1: "Show me net sales trend in 2024"                                   │
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Context: { kpi: "net_sales", period: "2024", view: "trend" }        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│          │                                                                   │
│          ▼                                                                   │
│  Turn 2: "Break it down by region"                                           │
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Context: { kpi: "net_sales", period: "2024", dimension: "region" }  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│          │                                                                   │
│          ▼                                                                   │
│  Turn 3: "Drill into Dubai"                                                  │
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Context: { kpi: "net_sales", period: "2024",                        │    │
│  │           filter: { region: "Dubai" },                              │    │
│  │           drill_path: ["region:Dubai"] }                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│          │                                                                   │
│          ▼                                                                   │
│  Turn 4: "What if we increase prices by 5%?"                                 │
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Context: { base_kpi: "net_sales", base_filter: { region: "Dubai" }, │    │
│  │           scenario: "price_change", params: { change: 5% } }        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary Table

| Category | Item | Count | Details |
|----------|------|-------|---------|
| **Workflows** | Arada Analytics | 1 | Single orchestrated workflow |
| **Agents** | Total | 5 | 1 Orchestrator + 4 Specialists |
| | Orchestrator | 1 | Routes & synthesizes |
| | Specialist | 4 | Descriptive, Deep Dive, Decomposition, What-If |
| **Skills** | Total | 6 | Domain expertise injected into agents |
| **Tools** | Total | 5 | KPI Calc, Chart Gen, Query, What-If Sim, Decomp |
| **Analysis Scopes** | Total | 4 | As per POC MOM |
| | Descriptive | 10 KPIs | Trends, comparisons |
| | Deep Dive | Cancellation + others | Region, project drill-down |
| | Decomposition | Max 3 | Waterfall, variance, mix |
| | What-If | Net Sales + 1 | Scenario simulation |

---

## Files Created

| File | Purpose |
|------|---------|
| `src/config/arada_poc_agents.py` | Agent configurations (all 5 agents) |
| `scripts/register_arada_agents.py` | Script to register agents to DB |
| `docs/arada_poc_solution_architecture.md` | Full technical architecture |
| `docs/arada_poc_ui_integration.md` | UI integration guide |
| `docs/arada_poc_implementation_plan.md` | This plan document |

---

## Next Steps

1. **Run registration:** `python scripts/register_arada_agents.py`
2. **Create/update tools:** Implement `decomposition_tool` if not exists
3. **Connect data:** Wire Query Engine to Arada sales database
4. **Build UI page:** Create `/arada` page using orchestrator agent
5. **Test conversation flow:** Verify context preservation across turns

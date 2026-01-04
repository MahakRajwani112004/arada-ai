# AI Agent Builder - Product Specification

## MagOneAI v2 Hero Feature

**Version:** 1.0
**Date:** January 2026
**Status:** Specification Complete
**Priority:** P0 - Hero Feature

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Vision & Goals](#2-vision--goals)
3. [User Flows](#3-user-flows)
4. [Feature Specifications](#4-feature-specifications)
5. [UI Specifications](#5-ui-specifications)
6. [AI Behavior Specifications](#6-ai-behavior-specifications)
7. [Data Models](#7-data-models)
8. [API Specifications](#8-api-specifications)
9. [Technical Architecture](#9-technical-architecture)
10. [Edge Cases & Error Handling](#10-edge-cases--error-handling)
11. [Implementation Roadmap](#11-implementation-roadmap)
12. [Success Metrics](#12-success-metrics)

---

## 1. Executive Summary

### What is AI Agent Builder?

AI Agent Builder is a natural language interface that allows users to describe what they want to build and have AI automatically architect and create a complete multi-agent system - including all necessary agents, their configurations, tools, flow rules, and triggers.

### Key Differentiator

Unlike traditional workflow builders that only create flow structures (requiring pre-existing agents), AI Agent Builder creates the **entire architecture**:

```
Traditional Workflow Builder:
  User describes → AI creates workflow → User must create agents separately

AI Agent Builder:
  User describes → AI creates EVERYTHING → Ready to use immediately
```

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Natural Language Input** | Describe requirements in plain English |
| **Intelligent Analysis** | AI understands intent, identifies capabilities needed |
| **Architecture Design** | AI proposes optimal agent structure |
| **Automatic Creation** | Creates all agents, configs, and flows |
| **Smart Reuse** | Finds and reuses existing agents when appropriate |
| **Conversational Iteration** | Modify existing systems via natural language |
| **Visual Preview** | See architecture before and after creation |

---

## 2. Vision & Goals

### Vision Statement

> "Any user should be able to describe a complex AI system in plain English and have it built automatically in under 2 minutes."

### Goals

| Goal | Target | Measurement |
|------|--------|-------------|
| Time to first working agent system | < 2 minutes | From description to testable |
| User success rate | > 80% | First attempt creates working system |
| Modification success rate | > 90% | Conversational changes work correctly |
| Agent reuse rate | > 40% | Existing agents reused when appropriate |
| User satisfaction | > 4.5/5 | Post-creation survey |

### Non-Goals (v1)

- Visual-first editing (Canvas is secondary view, not primary input)
- Multi-language support (English only for v1)
- Team collaboration features
- Version control / rollback
- Template marketplace

---

## 3. User Flows

### 3.1 Primary Flow: Create New Agent System

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRIMARY USER FLOW                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ DESCRIBE│────▶│ ANALYZE │────▶│ PROPOSE │────▶│CUSTOMIZE│────▶│ CREATE  │
│         │     │         │     │         │     │(optional)│     │         │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
  User types     AI shows        AI shows        User can       AI creates
  natural        analysis        proposed        modify any     all agents
  language       progress        architecture    part           and configs
  description                                                         │
                                                                      ▼
                                                               ┌─────────┐
                                                               │  READY  │
                                                               │         │
                                                               └─────────┘
                                                                     │
                                                                     ▼
                                                               Test, Use,
                                                               or Iterate
```

### 3.2 Secondary Flow: Modify Existing System

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MODIFICATION FLOW                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐
│   SELECT    │────▶│  DESCRIBE   │────▶│   PREVIEW   │────▶│  APPLY  │
│ ORCHESTRATOR│     │   CHANGE    │     │   CHANGES   │     │         │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
  Open existing       "Add sentiment      AI shows what      AI modifies
  orchestrator        analysis before     will change:       existing
  dashboard           routing"            + new agents       architecture
                                          ~ modified agents
                                          - removed items
```

### 3.3 Entry Points

| Entry Point | Location | Trigger |
|-------------|----------|---------|
| Dashboard CTA | Home page | "Build with AI" button |
| New Agent | /agents/new | "Generate with AI" option |
| Empty State | First time user | Primary action |
| Orchestrator Detail | /agents/[id] | "Modify with AI" button |
| Canvas View | Orchestrator canvas | "AI Suggest" floating button |
| Command Palette | Global (Cmd+K) | "Build agent system..." |

---

## 4. Feature Specifications

### 4.1 Natural Language Input

#### Input Box Specification

```
┌─────────────────────────────────────────────────────────────────────┐
│  Describe what you want to build:                                    │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │  [Multiline textarea - min 3 rows, max 10 rows]                 ││
│  │                                                                  ││
│  │  Placeholder: "I need an AI that handles customer support -     ││
│  │  it should route queries to specialists, process refunds,       ││
│  │  and escalate to humans when needed..."                         ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  Examples: [Customer Support] [Sales Assistant] [Data Pipeline]     │
│                                                                      │
│  [Generate Architecture]                                             │
└─────────────────────────────────────────────────────────────────────┘
```

#### Example Prompts (Clickable Templates)

| Template | Expands To |
|----------|------------|
| Customer Support | "Build a customer support system that handles billing questions, technical issues, and order tracking. It should escalate complex issues to human agents and send email confirmations." |
| Sales Assistant | "Create a sales assistant that qualifies leads, schedules demos, updates CRM, and sends follow-up emails. It should hand off hot leads to sales reps." |
| Data Pipeline | "Build a data processing system that extracts data from uploaded files, validates it, transforms it, and loads it into our database with error reporting." |
| Content Moderator | "Create a content moderation system that analyzes user submissions for policy violations, auto-approves safe content, and flags risky content for human review." |

#### Input Validation

| Rule | Behavior |
|------|----------|
| Min length | 20 characters (show hint if shorter) |
| Max length | 2000 characters |
| Empty submit | Show inline error |
| Gibberish detection | AI responds asking for clarification |

### 4.2 AI Analysis Phase

#### Analysis Steps (Shown to User)

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔍 Analyzing your requirements...                                   │
│                                                                      │
│  ✓ Understanding intent                                    [1.2s]   │
│    → Primary goal: Customer support automation                      │
│    → Secondary goals: Billing, Technical, Orders                    │
│                                                                      │
│  ✓ Identifying capabilities needed                         [0.8s]   │
│    → Query routing (intent classification)                          │
│    → Billing inquiry handling                                       │
│    → Technical support with documentation                           │
│    → Order tracking and status                                      │
│    → Human escalation workflow                                      │
│    → Email notifications                                            │
│                                                                      │
│  ✓ Scanning existing agents                                [0.5s]   │
│    → Found 3 potential matches                                      │
│    → "Email Sender" - 95% match                                    │
│    → "Doc Search" - 78% match                                      │
│    → "CRM Agent" - 45% match (not using)                           │
│                                                                      │
│  ✓ Checking available integrations                         [0.3s]   │
│    → Stripe (billing) ✓ Connected                                  │
│    → Shopify (orders) ✓ Connected                                  │
│    → Gmail (email) ✓ Connected                                     │
│    → Zendesk (tickets) ○ Available but not connected               │
│                                                                      │
│  ⏳ Designing optimal architecture...                       [1.5s]   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Analysis Output (Internal)

```typescript
interface AnalysisResult {
  // Intent understanding
  primaryGoal: string;
  secondaryGoals: string[];

  // Capabilities identified
  capabilities: {
    name: string;
    description: string;
    requiredTools: string[];
    suggestedAgentType: AgentType;
  }[];

  // Existing agent matches
  existingAgentMatches: {
    agentId: string;
    agentName: string;
    matchScore: number;
    matchReason: string;
    recommended: boolean;
  }[];

  // Integration requirements
  integrations: {
    name: string;
    required: boolean;
    connected: boolean;
    tools: string[];
  }[];

  // Confidence and warnings
  overallConfidence: number;
  warnings: string[];
  clarificationNeeded: string | null;
}
```

### 4.3 Architecture Proposal

#### Proposal Display

```
┌─────────────────────────────────────────────────────────────────────┐
│  Here's my suggested architecture:                                   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    [VISUAL DIAGRAM]                              ││
│  │                                                                  ││
│  │  Shows orchestrator with all sub-agents in a tree/graph view    ││
│  │  - Color coded by agent type                                    ││
│  │  - 🆕 badge for new agents                                      ││
│  │  - ♻️ badge for reused existing agents                          ││
│  │  - Connection lines showing flow                                 ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  SUMMARY                                                         ││
│  │                                                                  ││
│  │  Orchestrator: Customer Support System                          ││
│  │  Mode: Hybrid (follows flow, LLM can adapt)                     ││
│  │                                                                  ││
│  │  Agents to Create:                                              ││
│  │  ┌─────────────────────────────────────────────────────────────┐││
│  │  │ NAME              │ TYPE        │ PURPOSE                   │││
│  │  │───────────────────│─────────────│───────────────────────────│││
│  │  │ Intent Router     │ Router      │ Classify and route queries│││
│  │  │ Billing Agent     │ Worker      │ Handle billing questions  │││
│  │  │ Technical Agent   │ Worker      │ Answer tech questions     │││
│  │  │ Orders Agent      │ Worker      │ Track orders and shipping │││
│  │  │ Human Escalation  │ Human       │ Escalate complex issues   │││
│  │  └─────────────────────────────────────────────────────────────┘││
│  │                                                                  ││
│  │  Existing Agents to Reuse:                                      ││
│  │  • Email Sender (for notifications)                             ││
│  │                                                                  ││
│  │  Tools to Configure:                                            ││
│  │  • stripe:get-invoices, stripe:process-refund                   ││
│  │  • shopify:get-order, shopify:track-shipping                    ││
│  │  • gmail:send                                                   ││
│  │                                                                  ││
│  │  Triggers:                                                       ││
│  │  • Webhook: POST /api/support                                   ││
│  │  • Chat interface                                               ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  [View Details]  [Customize]  [Create All →]                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Proposal Data Structure

```typescript
interface ArchitectureProposal {
  // Orchestrator definition
  orchestrator: {
    name: string;
    description: string;
    mode: 'sequential' | 'parallel' | 'hybrid' | 'llm_driven';
    triggers: TriggerConfig[];
  };

  // Agents to create
  newAgents: {
    tempId: string;  // Temporary ID for UI reference
    name: string;
    type: AgentType;
    description: string;
    goal: string;
    tools: string[];
    skills: string[];
    knowledgeBases: string[];
    config: Record<string, any>;
  }[];

  // Existing agents to reuse
  reuseAgents: {
    agentId: string;
    agentName: string;
    role: string;  // Role in this orchestrator
  }[];

  // Flow definition
  flow: {
    from: string;  // tempId or agentId
    to: string;    // tempId or agentId
    condition?: string;
    label?: string;
  }[];

  // Routing rules (for router agents)
  routingRules: {
    routerTempId: string;
    rules: {
      pattern: string;
      targetTempId: string;
      description: string;
    }[];
  }[];

  // Metadata
  estimatedCreationTime: number;  // seconds
  warnings: string[];
  suggestions: string[];
}
```

### 4.4 Customization Phase

#### Customization UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  Customize Your Architecture                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ORCHESTRATOR SETTINGS                                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Name: [Customer Support System               ]                   ││
│  │                                                                  ││
│  │ Mode: [Hybrid ▼]                                                ││
│  │       ○ Sequential - Agents run in defined order                ││
│  │       ○ Parallel - Agents run simultaneously                    ││
│  │       ● Hybrid - Follow flow, LLM can adapt                     ││
│  │       ○ LLM Driven - LLM decides everything                     ││
│  │                                                                  ││
│  │ Triggers:                                                        ││
│  │   ✓ [Webhook] Path: [/api/support        ]                      ││
│  │   ✓ [Chat Interface]                                            ││
│  │   ☐ [Schedule] Cron: [                   ]                      ││
│  │   [+ Add Trigger]                                               ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  SUB-AGENTS                                          [+ Add Agent]  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │ ▶ Intent Router              [Router] 🆕                        ││
│  │                                                                  ││
│  │ ▼ Billing Agent              [Worker] 🆕      [Remove] [↑] [↓] ││
│  │   ┌─────────────────────────────────────────────────────────┐   ││
│  │   │ Name: [Billing Agent                    ]               │   ││
│  │   │ Goal: [Help customers with billing questions and        │   ││
│  │   │        process refunds when appropriate                 ]   │   ││
│  │   │                                                          │   ││
│  │   │ Tools:                                                   │   ││
│  │   │   ✓ stripe:get-invoices                                 │   ││
│  │   │   ✓ stripe:process-refund                               │   ││
│  │   │   ✓ stripe:get-customer                                 │   ││
│  │   │   [+ Add Tool]                                          │   ││
│  │   │                                                          │   ││
│  │   │ Knowledge Base:                                          │   ││
│  │   │   [Select knowledge base ▼]                             │   ││
│  │   │                                                          │   ││
│  │   │ Advanced:                                                │   ││
│  │   │   Temperature: [0.7    ]                                │   ││
│  │   │   Max Tokens:  [2048   ]                                │   ││
│  │   └─────────────────────────────────────────────────────────┘   ││
│  │                                                                  ││
│  │ ▶ Technical Agent            [Worker] 🆕                        ││
│  │ ▶ Orders Agent               [Worker] 🆕                        ││
│  │ ▶ Human Escalation           [Human]  🆕                        ││
│  │ ▶ Email Sender               [Tool]   ♻️ Existing               ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  FLOW RULES                                          [+ Add Rule]   │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │ 1. [Intent Router ▼] → [Billing Agent ▼]                        ││
│  │    When: [intent = "billing_*"              ]           [×]     ││
│  │                                                                  ││
│  │ 2. [Intent Router ▼] → [Technical Agent ▼]                      ││
│  │    When: [intent = "technical_*"            ]           [×]     ││
│  │                                                                  ││
│  │ 3. [Intent Router ▼] → [Orders Agent ▼]                         ││
│  │    When: [intent = "order_*"                ]           [×]     ││
│  │                                                                  ││
│  │ 4. [Any Agent ▼] → [Human Escalation ▼]                         ││
│  │    When: [confidence < 0.6                  ]           [×]     ││
│  │                                                                  ││
│  │ 5. [* (After resolution) ▼] → [Email Sender ▼]                  ││
│  │    When: [always                            ]           [×]     ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  [← Back]  [Preview in Canvas]  [Create All →]                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Customization Actions

| Action | Behavior |
|--------|----------|
| Edit orchestrator name | Updates proposal |
| Change mode | Updates proposal, may show warnings |
| Add/remove trigger | Updates proposal |
| Expand agent | Shows editable agent config |
| Edit agent field | Updates proposal |
| Add tool to agent | Updates proposal |
| Remove agent | Updates proposal, may break flow rules |
| Reorder agents | Updates proposal |
| Add flow rule | Updates proposal |
| Edit flow rule | Updates proposal |
| Remove flow rule | Updates proposal |

### 4.5 Creation Phase

#### Creation Progress UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  Creating Your Agent Architecture                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │  ✓ Intent Router                                        [1.2s]  ││
│  │    └─ Created with 3 routing rules                              ││
│  │                                                                  ││
│  │  ✓ Billing Agent                                        [1.8s]  ││
│  │    └─ Connected 3 Stripe tools                                  ││
│  │    └─ Configured billing instructions                           ││
│  │                                                                  ││
│  │  ✓ Technical Agent                                      [1.5s]  ││
│  │    └─ Connected Doc Search knowledge base                       ││
│  │    └─ Configured technical instructions                         ││
│  │                                                                  ││
│  │  ✓ Orders Agent                                         [1.4s]  ││
│  │    └─ Connected 2 Shopify tools                                 ││
│  │    └─ Configured order tracking instructions                    ││
│  │                                                                  ││
│  │  ✓ Human Escalation                                     [0.8s]  ││
│  │    └─ Set up approval workflow                                  ││
│  │    └─ Configured notification settings                          ││
│  │                                                                  ││
│  │  ⏳ Customer Support Orchestrator                       [2.1s]  ││
│  │    └─ Linking 5 sub-agents                                      ││
│  │    └─ Configuring 5 flow rules                                  ││
│  │    └─ Setting up webhook trigger                                ││
│  │    └─ Enabling chat interface                                   ││
│  │                                                                  ││
│  │  [████████████████████████░░░░░░] 78%                           ││
│  │                                                                  ││
│  │  Estimated time remaining: ~5 seconds                           ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  [Cancel]                                                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Creation Steps (Internal)

```typescript
async function createArchitecture(proposal: ArchitectureProposal): Promise<CreationResult> {
  const results: AgentCreationResult[] = [];
  const agentIdMap: Map<string, string> = new Map();  // tempId -> realId

  // Step 1: Create all new agents (in dependency order)
  for (const agent of sortByDependency(proposal.newAgents)) {
    emit('progress', { step: 'creating_agent', agent: agent.name });

    const created = await createAgent({
      name: agent.name,
      type: agent.type,
      description: agent.description,
      goal: agent.goal,
      tools: agent.tools,
      skills: agent.skills,
      knowledge_bases: agent.knowledgeBases,
      config: agent.config,
    });

    agentIdMap.set(agent.tempId, created.id);
    results.push({ tempId: agent.tempId, agentId: created.id, status: 'created' });

    emit('progress', { step: 'agent_created', agent: agent.name, agentId: created.id });
  }

  // Step 2: Create orchestrator with all sub-agents
  emit('progress', { step: 'creating_orchestrator', name: proposal.orchestrator.name });

  const subAgents = [
    ...proposal.newAgents.map(a => ({
      agent_id: agentIdMap.get(a.tempId)!,
      alias: a.name,
    })),
    ...proposal.reuseAgents.map(a => ({
      agent_id: a.agentId,
      alias: a.role,
    })),
  ];

  const flow = proposal.flow.map(f => ({
    from: agentIdMap.get(f.from) || f.from,
    to: agentIdMap.get(f.to) || f.to,
    condition: f.condition,
  }));

  const orchestrator = await createAgent({
    name: proposal.orchestrator.name,
    type: 'orchestrator',
    description: proposal.orchestrator.description,
    config: {
      mode: proposal.orchestrator.mode,
      sub_agents: subAgents,
      flow: flow,
      triggers: proposal.orchestrator.triggers,
    },
  });

  emit('progress', { step: 'orchestrator_created', orchestratorId: orchestrator.id });

  // Step 3: Configure routing rules for router agents
  for (const routing of proposal.routingRules) {
    const routerId = agentIdMap.get(routing.routerTempId)!;
    await updateAgentConfig(routerId, {
      routing_table: routing.rules.reduce((acc, rule) => {
        acc[rule.pattern] = agentIdMap.get(rule.targetTempId) || rule.targetTempId;
        return acc;
      }, {} as Record<string, string>),
    });
  }

  emit('progress', { step: 'complete', orchestratorId: orchestrator.id });

  return {
    orchestratorId: orchestrator.id,
    createdAgents: results,
    totalTime: Date.now() - startTime,
  };
}
```

### 4.6 Completion & Next Steps

#### Completion UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  🎉 Your Customer Support System is Ready!                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │                           ✓                                     ││
│  │                                                                  ││
│  │              Successfully created in 8.2 seconds                ││
│  │                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────┐   ││
│  │  │ CREATED                                                  │   ││
│  │  │                                                          │   ││
│  │  │ • 1 Orchestrator: Customer Support System               │   ││
│  │  │ • 5 Sub-Agents                                          │   ││
│  │  │ • 5 Flow Rules                                          │   ││
│  │  │ • 2 Triggers                                            │   ││
│  │  └─────────────────────────────────────────────────────────┘   ││
│  │                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────┐   ││
│  │  │ ENDPOINTS                                                │   ││
│  │  │                                                          │   ││
│  │  │ API Invoke:                                              │   ││
│  │  │ POST https://api.magone.ai/v1/agents/agt_xyz/invoke     │   ││
│  │  │                                                 [Copy]   │   ││
│  │  │                                                          │   ││
│  │  │ Webhook:                                                 │   ││
│  │  │ POST https://api.magone.ai/webhooks/wh_abc123           │   ││
│  │  │                                                 [Copy]   │   ││
│  │  └─────────────────────────────────────────────────────────┘   ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  What would you like to do next?                                    │
│                                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │              │ │              │ │              │ │            │ │
│  │  💬 Test in  │ │  📊 View     │ │  🎨 Edit in  │ │  📤 Share  │ │
│  │     Chat     │ │   Dashboard  │ │    Canvas    │ │            │ │
│  │              │ │              │ │              │ │            │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.7 Conversational Modification

#### Modification Interface

```
┌─────────────────────────────────────────────────────────────────────┐
│  Customer Support System                         [Modify with AI]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    AI MODIFICATION CHAT                          ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │                                                                  ││
│  │  USER:                                                          ││
│  │  Add sentiment analysis before routing so angry customers       ││
│  │  go directly to human agents                                    ││
│  │                                                                  ││
│  │  ─────────────────────────────────────────────────────────────  ││
│  │                                                                  ││
│  │  AI:                                                            ││
│  │  I'll add a Sentiment Analyzer that runs before the router.     ││
│  │  Here's what will change:                                       ││
│  │                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────┐   ││
│  │  │ CHANGES PREVIEW                                          │   ││
│  │  │                                                          │   ││
│  │  │ + NEW: Sentiment Analyzer [Worker]                       │   ││
│  │  │   └─ Analyzes customer sentiment before routing          │   ││
│  │  │                                                          │   ││
│  │  │ ~ MODIFIED: Flow Rules                                   │   ││
│  │  │   └─ Added: Start → Sentiment Analyzer                   │   ││
│  │  │   └─ Added: Sentiment (angry) → Human Escalation         │   ││
│  │  │   └─ Modified: Sentiment (neutral/positive) → Router     │   ││
│  │  │                                                          │   ││
│  │  │ ○ UNCHANGED: All existing agents                         │   ││
│  │  └─────────────────────────────────────────────────────────┘   ││
│  │                                                                  ││
│  │  [Preview in Canvas]  [Apply Changes]  [Modify Further]         ││
│  │                                                                  ││
│  │  ─────────────────────────────────────────────────────────────  ││
│  │                                                                  ││
│  │  USER:                                                          ││
│  │  Also require manager approval for refunds over $100            ││
│  │                                                                  ││
│  │  ─────────────────────────────────────────────────────────────  ││
│  │                                                                  ││
│  │  AI:                                                            ││
│  │  I'll add a conditional approval step to the billing flow:      ││
│  │                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────┐   ││
│  │  │ CHANGES PREVIEW                                          │   ││
│  │  │                                                          │   ││
│  │  │ ~ MODIFIED: Flow Rules                                   │   ││
│  │  │   └─ Added: Billing Agent → Human Escalation             │   ││
│  │  │     (when: refund_amount > 100)                          │   ││
│  │  │                                                          │   ││
│  │  │ ~ MODIFIED: Human Escalation                             │   ││
│  │  │   └─ Added "manager@company.com" to approvers            │   ││
│  │  │   └─ Set approval title: "Refund Approval Required"      │   ││
│  │  └─────────────────────────────────────────────────────────┘   ││
│  │                                                                  ││
│  │  [Preview in Canvas]  [Apply Changes]  [Modify Further]         ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Describe what you want to change...                    [Send]   ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Modification Types Supported

| Modification Type | Example | AI Behavior |
|-------------------|---------|-------------|
| Add agent | "Add sentiment analysis" | Creates new agent, updates flow |
| Remove agent | "Remove the orders agent" | Removes agent, cleans up flow rules |
| Modify agent | "Make billing agent also handle subscriptions" | Updates agent config/tools |
| Add flow rule | "Escalate when confidence is low" | Adds new flow rule |
| Remove flow rule | "Don't send emails automatically" | Removes flow rule |
| Change routing | "Route VIP customers to human directly" | Modifies router config |
| Add trigger | "Also trigger on schedule daily" | Adds trigger to orchestrator |
| Change mode | "Make it fully LLM-driven" | Changes orchestrator mode |
| Add tool | "Add Slack notifications" | Adds tool to relevant agent |
| Add knowledge | "Use our FAQ docs for technical questions" | Links knowledge base |

---

## 5. UI Specifications

### 5.1 Component Library

All components use shadcn/ui + Tailwind CSS.

#### AI Builder Modal/Page

```tsx
// Route: /agents/build or Modal overlay
interface AIBuilderProps {
  mode: 'create' | 'modify';
  existingOrchestrator?: string;  // agentId if modifying
  onComplete: (orchestratorId: string) => void;
  onCancel: () => void;
}
```

#### Analysis Progress Component

```tsx
interface AnalysisStepProps {
  step: {
    id: string;
    label: string;
    status: 'pending' | 'running' | 'complete' | 'error';
    duration?: number;
    details?: string[];
  };
}

// Renders:
// ✓ Step label                    [1.2s]
//   └─ Detail line 1
//   └─ Detail line 2
```

#### Architecture Diagram Component

```tsx
interface ArchitectureDiagramProps {
  proposal: ArchitectureProposal;
  interactive: boolean;  // Can click nodes
  onNodeClick?: (nodeId: string) => void;
  highlightNew: boolean;  // Show 🆕 badges
  highlightReused: boolean;  // Show ♻️ badges
}

// Uses React Flow for rendering
// Custom node types for each agent type
// Auto-layout using dagre
```

#### Agent Card (in customization list)

```tsx
interface AgentCardProps {
  agent: ProposedAgent;
  expanded: boolean;
  isNew: boolean;
  isReused: boolean;
  onToggle: () => void;
  onEdit: (field: string, value: any) => void;
  onRemove: () => void;
  onReorder: (direction: 'up' | 'down') => void;
}
```

### 5.2 Layout Specifications

#### Desktop (≥1024px)

```
┌─────────────────────────────────────────────────────────────────────┐
│  AI Agent Builder                                            [×]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Full width content area - 1200px max, centered]                  │
│                                                                     │
│  In Proposal/Customize phase:                                       │
│  ┌──────────────────────────────┐ ┌───────────────────────────────┐│
│  │                              │ │                               ││
│  │  Visual Diagram              │ │  Summary / Config Panel       ││
│  │  (60% width)                 │ │  (40% width)                  ││
│  │                              │ │                               ││
│  └──────────────────────────────┘ └───────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Tablet (768px - 1023px)

```
┌─────────────────────────────────────────────────────────────────────┐
│  AI Agent Builder                                            [×]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Stacked layout - diagram above, config below]                    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Visual Diagram (100% width, 300px height)                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Summary / Config Panel (100% width)                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Mobile (< 768px)

```
┌─────────────────────────────────┐
│  AI Agent Builder         [×]   │
├─────────────────────────────────┤
│                                 │
│  [Tabs: Diagram | Config]       │
│                                 │
│  [Selected tab content]         │
│                                 │
│  [Sticky bottom action bar]     │
│                                 │
└─────────────────────────────────┘
```

### 5.3 Animation Specifications

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Analysis steps appear | Fade in + slide up | 300ms | ease-out |
| Checkmark on complete | Scale pop | 200ms | spring |
| Diagram nodes | Fade in sequentially | 100ms each | ease-out |
| Progress bar | Width transition | continuous | linear |
| Agent card expand | Height transition | 200ms | ease-in-out |
| Creation step complete | Slide left + fade | 300ms | ease-out |

---

## 6. AI Behavior Specifications

### 6.1 System Prompt for Analysis

```markdown
You are an AI Agent Architect for MagOneAI. Your job is to analyze user requirements and design optimal multi-agent architectures.

## Your Capabilities
- Understand natural language descriptions of AI systems
- Identify required capabilities and map them to agent types
- Design orchestration flows with appropriate routing
- Select relevant tools and integrations
- Reuse existing agents when appropriate

## Agent Types Available
- **Orchestrator**: Coordinates multiple sub-agents, has execution modes (sequential, parallel, hybrid, llm_driven)
- **Router**: Classifies intent and routes to appropriate agent
- **Worker**: Performs tasks using LLM + tools, the most common type
- **Tool**: Wraps external tools/APIs without LLM reasoning
- **Human**: Pauses for human approval or input

## Analysis Output Format
Provide your analysis as JSON matching the AnalysisResult schema.

## Guidelines
1. Keep architectures simple - don't over-engineer
2. Prefer fewer agents with more capabilities over many simple agents
3. Always include error handling paths (escalation to human)
4. Consider existing agents before creating new ones
5. Match tools to actual available integrations
```

### 6.2 System Prompt for Architecture Design

```markdown
You are designing a multi-agent architecture based on the analysis.

## Design Principles
1. **Simplicity**: Minimum agents needed to accomplish the goal
2. **Reusability**: Design agents that can be reused elsewhere
3. **Resilience**: Include fallback paths and human escalation
4. **Clarity**: Clear naming and obvious flow

## Architecture Output Format
Provide your architecture as JSON matching the ArchitectureProposal schema.

## Flow Rule Guidelines
- Start with a router if multiple distinct intents exist
- Use conditions for business rules (amount thresholds, etc.)
- Always have a path to human escalation
- End with notification/confirmation where appropriate

## Naming Conventions
- Orchestrator: "[Domain] System" or "[Domain] Orchestrator"
- Router: "[Domain] Router" or "Intent Router"
- Worker: "[Function] Agent" (e.g., "Billing Agent")
- Tool: "[Tool Name] Connector" or "[Action] Tool"
- Human: "Human [Action]" (e.g., "Human Approval")
```

### 6.3 System Prompt for Modification

```markdown
You are modifying an existing agent architecture based on user requests.

## Current Architecture
{current_architecture_json}

## Modification Guidelines
1. Minimize changes - only modify what's necessary
2. Preserve existing agent IDs when modifying (don't recreate)
3. Clearly categorize changes as: NEW, MODIFIED, REMOVED, UNCHANGED
4. Validate that changes don't break existing flows
5. Suggest additional changes if the request implies them

## Output Format
Provide changes as JSON with:
- additions: new agents/rules to add
- modifications: changes to existing agents/rules
- removals: agents/rules to remove
- warnings: potential issues with the changes
```

### 6.4 Clarification Handling

When AI needs clarification:

```typescript
interface ClarificationRequest {
  question: string;
  options?: string[];  // Suggested answers
  required: boolean;   // Can proceed without answer?
  context: string;     // Why AI is asking
}

// Example:
{
  question: "Should billing agents be able to process refunds automatically, or should all refunds require approval?",
  options: [
    "Automatic for small amounts, approval for large",
    "Always require approval",
    "Always automatic"
  ],
  required: false,
  context: "This affects whether I add a Human Approval agent to the billing flow"
}
```

UI for clarification:

```
┌─────────────────────────────────────────────────────────────────────┐
│  🤔 I have a question:                                               │
│                                                                      │
│  Should billing agents be able to process refunds automatically,    │
│  or should all refunds require approval?                            │
│                                                                      │
│  ○ Automatic for small amounts, approval for large (recommended)    │
│  ○ Always require approval                                          │
│  ○ Always automatic                                                 │
│  ○ Let me specify...                                                │
│                                                                      │
│  [Skip - Use Default]  [Continue →]                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Data Models

### 7.1 Database Schema Additions

```sql
-- AI Builder Sessions (for resumability)
CREATE TABLE ai_builder_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  status VARCHAR(20) NOT NULL DEFAULT 'in_progress',  -- in_progress, completed, abandoned
  mode VARCHAR(20) NOT NULL,  -- create, modify
  target_orchestrator_id UUID REFERENCES agents(id),  -- null for create, set for modify

  -- Input
  user_prompt TEXT NOT NULL,

  -- Analysis
  analysis_result JSONB,
  analysis_completed_at TIMESTAMP,

  -- Proposal
  proposal JSONB,
  proposal_completed_at TIMESTAMP,

  -- Customizations
  customizations JSONB,  -- User modifications to proposal

  -- Creation
  created_agents JSONB,  -- Array of created agent IDs
  orchestrator_id UUID REFERENCES agents(id),
  creation_completed_at TIMESTAMP,

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- AI Builder Feedback (for improvement)
CREATE TABLE ai_builder_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES ai_builder_sessions(id),
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  feedback_text TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 7.2 TypeScript Types

```typescript
// Builder session state
interface AIBuilderState {
  step: 'input' | 'analyzing' | 'proposal' | 'customizing' | 'creating' | 'complete' | 'error';
  mode: 'create' | 'modify';
  targetOrchestrator?: string;

  // Input
  userPrompt: string;

  // Analysis
  analysisProgress: AnalysisStep[];
  analysisResult?: AnalysisResult;

  // Proposal
  proposal?: ArchitectureProposal;

  // Customizations
  customizedProposal?: ArchitectureProposal;

  // Creation
  creationProgress: CreationStep[];
  creationResult?: CreationResult;

  // Error
  error?: {
    step: string;
    message: string;
    recoverable: boolean;
  };
}

interface AnalysisStep {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  startedAt?: Date;
  completedAt?: Date;
  details?: string[];
}

interface CreationStep {
  id: string;
  type: 'agent' | 'orchestrator' | 'config';
  name: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  agentId?: string;
  details?: string[];
}

interface CreationResult {
  orchestratorId: string;
  createdAgents: {
    tempId: string;
    agentId: string;
    name: string;
  }[];
  reusedAgents: string[];
  totalTime: number;
  endpoints: {
    invoke: string;
    webhook?: string;
  };
}
```

---

## 8. API Specifications

### 8.1 Start Builder Session

```yaml
POST /api/v1/ai-builder/sessions
Authorization: Bearer <token>

Request:
{
  "mode": "create",  # or "modify"
  "target_orchestrator_id": null,  # Required if mode = "modify"
  "prompt": "Build a customer support system..."
}

Response:
{
  "session_id": "ses_abc123",
  "status": "analyzing",
  "created_at": "2026-01-02T10:00:00Z"
}
```

### 8.2 Get Analysis Progress (SSE)

```yaml
GET /api/v1/ai-builder/sessions/{session_id}/analysis/stream
Authorization: Bearer <token>

Response: Server-Sent Events

event: step_started
data: {"step_id": "understand_intent", "label": "Understanding intent"}

event: step_completed
data: {"step_id": "understand_intent", "duration": 1.2, "details": ["Primary goal: Customer support"]}

event: analysis_complete
data: {"analysis_result": {...}}
```

### 8.3 Get Architecture Proposal

```yaml
GET /api/v1/ai-builder/sessions/{session_id}/proposal
Authorization: Bearer <token>

Response:
{
  "proposal": {
    "orchestrator": {...},
    "new_agents": [...],
    "reuse_agents": [...],
    "flow": [...],
    "routing_rules": [...],
    "estimated_creation_time": 10
  }
}
```

### 8.4 Update Proposal (Customization)

```yaml
PATCH /api/v1/ai-builder/sessions/{session_id}/proposal
Authorization: Bearer <token>

Request:
{
  "customizations": {
    "orchestrator": {
      "name": "My Custom Name"
    },
    "new_agents": {
      "temp_billing": {
        "tools": ["stripe:get-invoices", "stripe:process-refund", "stripe:get-customer"]
      }
    },
    "add_flow_rule": {
      "from": "temp_billing",
      "to": "temp_human",
      "condition": "refund_amount > 100"
    }
  }
}

Response:
{
  "proposal": {...},  # Updated proposal
  "validation": {
    "valid": true,
    "warnings": []
  }
}
```

### 8.5 Execute Creation

```yaml
POST /api/v1/ai-builder/sessions/{session_id}/create
Authorization: Bearer <token>

Request:
{
  "confirm": true
}

Response:
{
  "status": "creating",
  "stream_url": "/api/v1/ai-builder/sessions/{session_id}/create/stream"
}
```

### 8.6 Get Creation Progress (SSE)

```yaml
GET /api/v1/ai-builder/sessions/{session_id}/create/stream
Authorization: Bearer <token>

Response: Server-Sent Events

event: agent_creating
data: {"temp_id": "temp_router", "name": "Intent Router"}

event: agent_created
data: {"temp_id": "temp_router", "agent_id": "agt_xyz", "name": "Intent Router"}

event: orchestrator_creating
data: {"name": "Customer Support System"}

event: complete
data: {"orchestrator_id": "agt_abc", "endpoints": {...}}
```

### 8.7 Conversational Modification

```yaml
POST /api/v1/ai-builder/sessions/{session_id}/modify
Authorization: Bearer <token>

Request:
{
  "message": "Add sentiment analysis before routing"
}

Response:
{
  "changes": {
    "additions": [...],
    "modifications": [...],
    "removals": []
  },
  "preview": {...},  # Updated proposal
  "confirmation_required": true
}
```

### 8.8 Apply Modification

```yaml
POST /api/v1/ai-builder/sessions/{session_id}/modify/apply
Authorization: Bearer <token>

Request:
{
  "confirm": true
}

Response:
{
  "status": "applying",
  "stream_url": "/api/v1/ai-builder/sessions/{session_id}/modify/stream"
}
```

---

## 9. Technical Architecture

### 9.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                   │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ AI Builder   │  │ React Flow   │  │ SSE Client   │              │
│  │ UI Component │  │ (Diagrams)   │  │ (Progress)   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └─────────────────┴─────────────────┘                       │
│                           │                                         │
└───────────────────────────┼─────────────────────────────────────────┘
                            │ HTTP/SSE
                            ▼
┌───────────────────────────────────────────────────────────────────── │
│                           BACKEND                                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     AI Builder Service                        │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
│  │  │  Analyzer   │  │  Architect  │  │  Creator    │          │  │
│  │  │  Module     │  │  Module     │  │  Module     │          │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │  │
│  │         │                │                │                  │  │
│  └─────────┼────────────────┼────────────────┼──────────────────┘  │
│            │                │                │                      │
│            ▼                ▼                ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   LLM API   │  │ Agent CRUD  │  │  Session    │                │
│  │  (Anthropic)│  │   Service   │  │   Store     │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Module Responsibilities

#### Analyzer Module

```python
class AnalyzerModule:
    """Analyzes user requirements and produces AnalysisResult."""

    async def analyze(self, prompt: str, context: BuilderContext) -> AnalysisResult:
        # Step 1: Understand intent
        intent = await self._understand_intent(prompt)
        yield AnalysisStep("understand_intent", "complete", details=[intent.summary])

        # Step 2: Identify capabilities
        capabilities = await self._identify_capabilities(prompt, intent)
        yield AnalysisStep("identify_capabilities", "complete", details=capabilities.names)

        # Step 3: Find existing agents
        matches = await self._find_existing_agents(context.workspace_id, capabilities)
        yield AnalysisStep("scan_existing", "complete", details=[f"Found {len(matches)} matches"])

        # Step 4: Check integrations
        integrations = await self._check_integrations(context.workspace_id, capabilities)
        yield AnalysisStep("check_integrations", "complete", details=integrations.summary)

        return AnalysisResult(
            primary_goal=intent.primary_goal,
            secondary_goals=intent.secondary_goals,
            capabilities=capabilities,
            existing_agent_matches=matches,
            integrations=integrations,
            overall_confidence=self._calculate_confidence(...)
        )
```

#### Architect Module

```python
class ArchitectModule:
    """Designs optimal agent architecture based on analysis."""

    async def design(self, analysis: AnalysisResult, context: BuilderContext) -> ArchitectureProposal:
        # Build prompt with analysis context
        prompt = self._build_architecture_prompt(analysis, context)

        # Get architecture from LLM
        response = await self.llm.complete(
            system=ARCHITECT_SYSTEM_PROMPT,
            user=prompt,
            response_format=ArchitectureProposalSchema
        )

        # Validate and enhance proposal
        proposal = self._parse_proposal(response)
        proposal = await self._enhance_proposal(proposal, analysis)
        proposal = self._validate_proposal(proposal)

        return proposal
```

#### Creator Module

```python
class CreatorModule:
    """Creates agents and orchestrators based on proposal."""

    async def create(self, proposal: ArchitectureProposal, context: BuilderContext) -> CreationResult:
        agent_id_map = {}
        created_agents = []

        # Sort agents by dependency (routers before workers, etc.)
        sorted_agents = self._sort_by_dependency(proposal.new_agents)

        # Create each agent
        for agent_spec in sorted_agents:
            yield CreationStep(agent_spec.temp_id, "creating", agent_spec.name)

            agent = await self.agent_service.create(
                workspace_id=context.workspace_id,
                **agent_spec.to_create_params()
            )

            agent_id_map[agent_spec.temp_id] = agent.id
            created_agents.append(agent)

            yield CreationStep(agent_spec.temp_id, "complete", agent_spec.name, agent_id=agent.id)

        # Create orchestrator
        yield CreationStep("orchestrator", "creating", proposal.orchestrator.name)

        orchestrator = await self.agent_service.create(
            workspace_id=context.workspace_id,
            type="orchestrator",
            name=proposal.orchestrator.name,
            config={
                "mode": proposal.orchestrator.mode,
                "sub_agents": self._map_sub_agents(proposal, agent_id_map),
                "flow": self._map_flow(proposal.flow, agent_id_map),
                "triggers": proposal.orchestrator.triggers,
            }
        )

        yield CreationStep("orchestrator", "complete", proposal.orchestrator.name, agent_id=orchestrator.id)

        return CreationResult(
            orchestrator_id=orchestrator.id,
            created_agents=created_agents,
            agent_id_map=agent_id_map
        )
```

### 9.3 State Management (Frontend)

```typescript
// Using Zustand for state management
interface AIBuilderStore {
  // State
  state: AIBuilderState;

  // Actions
  startSession: (mode: 'create' | 'modify', prompt: string, targetId?: string) => Promise<void>;
  updateCustomization: (path: string, value: any) => void;
  confirmCreation: () => Promise<void>;
  sendModification: (message: string) => Promise<void>;
  applyModification: () => Promise<void>;
  reset: () => void;

  // SSE handlers
  handleAnalysisEvent: (event: AnalysisEvent) => void;
  handleCreationEvent: (event: CreationEvent) => void;
}

const useAIBuilderStore = create<AIBuilderStore>((set, get) => ({
  state: initialState,

  startSession: async (mode, prompt, targetId) => {
    set({ state: { ...initialState, step: 'analyzing', mode, userPrompt: prompt } });

    const response = await api.post('/ai-builder/sessions', { mode, prompt, target_orchestrator_id: targetId });
    const sessionId = response.session_id;

    // Connect to SSE for analysis progress
    const eventSource = new EventSource(`/api/v1/ai-builder/sessions/${sessionId}/analysis/stream`);
    eventSource.onmessage = (event) => get().handleAnalysisEvent(JSON.parse(event.data));
  },

  // ... other actions
}));
```

---

## 10. Edge Cases & Error Handling

### 10.1 Input Edge Cases

| Scenario | Handling |
|----------|----------|
| Empty/too short prompt | Show inline validation, don't submit |
| Gibberish/unclear prompt | AI asks for clarification |
| Request for unsupported features | AI explains limitation, suggests alternative |
| Multiple distinct systems in one prompt | AI asks to focus on one, or proposes multiple orchestrators |
| Prompt in non-English | Attempt to understand, may ask for English clarification |

### 10.2 Analysis Edge Cases

| Scenario | Handling |
|----------|----------|
| No existing agents match | Proceed with all new agents |
| All capabilities already exist | Suggest reusing existing orchestrator, offer to create new anyway |
| Required integration not connected | Show warning, offer to proceed without or connect first |
| Low confidence analysis | Show warning, ask for clarification |

### 10.3 Creation Edge Cases

| Scenario | Handling |
|----------|----------|
| Agent creation fails | Retry once, then show error with option to skip or retry |
| Duplicate agent name | Auto-suffix with number (e.g., "Billing Agent 2") |
| Tool not available | Skip tool, show warning in results |
| Orchestrator creation fails | Clean up created agents, show error |
| Session timeout | Save progress, allow resume |

### 10.4 Error Recovery

```typescript
interface RecoverableError {
  type: 'agent_creation_failed' | 'orchestrator_creation_failed' | 'timeout' | 'network';
  message: string;
  context: {
    step: string;
    agentName?: string;
    retryable: boolean;
  };
  actions: {
    retry: () => Promise<void>;
    skip: () => Promise<void>;  // If applicable
    cancel: () => void;
  };
}

// Error UI
<ErrorRecoveryDialog error={error}>
  <p>{error.message}</p>
  <p>Failed while: {error.context.step}</p>

  {error.context.retryable && (
    <Button onClick={error.actions.retry}>Retry</Button>
  )}
  {error.actions.skip && (
    <Button variant="outline" onClick={error.actions.skip}>Skip & Continue</Button>
  )}
  <Button variant="ghost" onClick={error.actions.cancel}>Cancel</Button>
</ErrorRecoveryDialog>
```

---

## 11. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

| Task | Priority | Effort |
|------|----------|--------|
| Database schema for sessions | P0 | 1 day |
| Basic API endpoints (start, get status) | P0 | 2 days |
| Analyzer module (intent + capabilities) | P0 | 3 days |
| Basic UI shell (input + progress) | P0 | 2 days |
| SSE infrastructure | P0 | 1 day |

**Milestone**: User can enter prompt and see analysis progress

### Phase 2: Architecture Design (Week 3-4)

| Task | Priority | Effort |
|------|----------|--------|
| Architect module | P0 | 3 days |
| Proposal API endpoints | P0 | 1 day |
| Architecture diagram component (React Flow) | P0 | 3 days |
| Proposal summary UI | P0 | 2 days |
| Existing agent matching | P1 | 2 days |

**Milestone**: User can see visual architecture proposal

### Phase 3: Customization (Week 5-6)

| Task | Priority | Effort |
|------|----------|--------|
| Customization API endpoints | P0 | 2 days |
| Agent card component | P0 | 2 days |
| Flow rule editor | P0 | 2 days |
| Trigger configuration | P1 | 1 day |
| Validation logic | P0 | 2 days |

**Milestone**: User can customize proposal before creation

### Phase 4: Creation (Week 7-8)

| Task | Priority | Effort |
|------|----------|--------|
| Creator module | P0 | 3 days |
| Creation progress UI | P0 | 2 days |
| Error handling + recovery | P0 | 2 days |
| Completion UI + next steps | P1 | 1 day |
| End-to-end testing | P0 | 2 days |

**Milestone**: User can create complete agent architecture

### Phase 5: Modification (Week 9-10)

| Task | Priority | Effort |
|------|----------|--------|
| Modification API endpoints | P0 | 2 days |
| Change preview logic | P0 | 2 days |
| Modification chat UI | P0 | 2 days |
| Apply changes logic | P0 | 2 days |
| Integration testing | P0 | 2 days |

**Milestone**: User can modify existing orchestrators via chat

### Phase 6: Polish (Week 11-12)

| Task | Priority | Effort |
|------|----------|--------|
| Template prompts | P1 | 1 day |
| Clarification flow | P1 | 2 days |
| Mobile responsive | P2 | 2 days |
| Performance optimization | P1 | 2 days |
| Analytics + feedback | P2 | 1 day |
| Documentation | P1 | 2 days |

**Milestone**: Production-ready AI Agent Builder

---

## 12. Success Metrics

### 12.1 Usage Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Sessions started / week | 100+ | Count of new sessions |
| Completion rate | > 70% | Sessions reaching "complete" state |
| Average time to complete | < 3 min | Median session duration |
| Modifications per orchestrator | > 2 | Average modification requests |

### 12.2 Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| First-attempt success | > 80% | Users not needing retry/redo |
| Customization rate | 30-60% | Users who customize before creating |
| Agent reuse rate | > 40% | Existing agents included in proposals |
| Error rate | < 5% | Sessions ending in error state |

### 12.3 Satisfaction Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Post-creation rating | > 4.5/5 | In-app feedback prompt |
| Feature NPS | > 50 | Quarterly survey |
| Time saved (perceived) | > 70% | User survey |

### 12.4 Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| New user activation | > 60% | New users creating via AI Builder |
| Upgrade conversion | +20% | Free→Paid after using AI Builder |
| Feature retention | > 50% | Users returning to AI Builder |

---

## Appendix A: Example Prompts & Outputs

### A.1 Customer Support System

**Prompt:**
```
Build a customer support system that handles billing questions, technical issues,
and order tracking. It should escalate complex issues to human agents and send
email confirmations after resolution.
```

**Generated Architecture:**
- Orchestrator: Customer Support System (Hybrid mode)
- Router: Intent Router (billing_*, technical_*, order_*)
- Worker: Billing Agent (Stripe tools)
- Worker: Technical Agent (Doc search)
- Worker: Orders Agent (Shopify tools)
- Human: Escalation Handler
- Tool: Email Sender

### A.2 Sales Pipeline

**Prompt:**
```
Create a sales assistant that qualifies inbound leads, schedules demos with
qualified prospects, updates our CRM, and hands off hot leads to sales reps
immediately.
```

**Generated Architecture:**
- Orchestrator: Sales Pipeline (Hybrid mode)
- Worker: Lead Qualifier (scoring logic)
- Worker: Demo Scheduler (Calendly tools)
- Worker: CRM Updater (Salesforce tools)
- Human: Hot Lead Handoff
- Tool: Slack Notifier

### A.3 Content Moderation

**Prompt:**
```
Build a content moderation system that reviews user submissions, auto-approves
safe content, flags potentially problematic content for human review, and
notifies users of decisions.
```

**Generated Architecture:**
- Orchestrator: Content Moderation System (Sequential mode)
- Worker: Content Analyzer (classification)
- Router: Decision Router (safe, review, reject)
- Human: Content Reviewer
- Tool: User Notifier
- Tool: Analytics Logger

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Orchestrator** | An agent that coordinates other agents |
| **Sub-Agent** | An agent managed by an orchestrator |
| **Router** | An agent that classifies intent and routes to targets |
| **Worker** | An agent that performs tasks using LLM + tools |
| **Flow Rule** | A condition-based routing rule between agents |
| **Trigger** | An event that starts orchestrator execution |
| **Proposal** | AI-generated architecture before user confirmation |
| **Session** | A single AI Builder interaction from start to finish |

---

**Document Version:** 1.0
**Last Updated:** January 2, 2026
**Authors:** Product & Engineering Team
**Status:** Ready for Development

# MagoneAI Platform Documentation

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Core Concepts](#2-core-concepts)
   - [Agents](#21-agents)
   - [Skills](#22-skills)
   - [Workflows](#23-workflows)
   - [Integrations (MCP)](#24-integrations-mcp)
3. [Getting Started](#3-getting-started)
4. [How-To Guides](#4-how-to-guides)
5. [API Reference](#5-api-reference)
6. [Troubleshooting](#6-troubleshooting)
7. [FAQ](#7-faq)

---

# 1. Platform Overview

## What is MagoneAI?

MagoneAI is a **dynamic AI agent platform** that enables you to build, deploy, and manage sophisticated AI-powered automation without deep AI expertise. Think of it as a toolkit for creating intelligent assistants that can:

- **Understand natural language** and respond intelligently
- **Execute tasks** by calling APIs, tools, and external services
- **Search knowledge bases** for accurate, context-aware responses
- **Orchestrate complex workflows** involving multiple AI agents
- **Integrate with external services** like Google Calendar, Gmail, Slack, and more

## Key Benefits

| Benefit | Description |
|---------|-------------|
| **No-Code Agent Building** | Create sophisticated AI agents through a visual interface |
| **Durable Workflows** | Built on Temporal for automatic retries and failure recovery |
| **Multi-LLM Support** | Use OpenAI GPT-4, Anthropic Claude, or switch between them |
| **Domain Expertise** | Add specialized knowledge through Skills system |
| **External Integrations** | Connect to Google, Microsoft, Slack via MCP protocol |
| **Production Ready** | Built-in monitoring, analytics, and security |

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Interface (Next.js)                  │
│         Agents | Skills | Workflows | Integrations          │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                   API Layer (FastAPI)                        │
│     Authentication | Validation | Rate Limiting              │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│              Workflow Engine (Temporal)                      │
│       Durable Execution | Retries | Persistence             │
└───────────┬─────────────────────────────────┬───────────────┘
            │                                 │
┌───────────▼───────────┐       ┌─────────────▼───────────────┐
│     Agent Workers     │       │      External Services       │
│  LLM | Tools | RAG    │       │  MCP | Google | Slack       │
└───────────┬───────────┘       └─────────────────────────────┘
            │
┌───────────▼───────────────────────────────────────────────┐
│                   Data Layer                               │
│     PostgreSQL | Knowledge Base | Secrets Vault           │
└───────────────────────────────────────────────────────────┘
```

---

# 2. Core Concepts

## 2.1 Agents

### What is an Agent?

An **Agent** is an AI entity configured to perform specific tasks. Each agent has a defined personality, goals, and capabilities. When you send a message to an agent, it processes your request and returns an intelligent response.

### Agent Types

MagoneAI supports **7 different agent types**, each designed for specific use cases:

| Type | Best For | Capabilities |
|------|----------|--------------|
| **Simple Agent** | Rule-based responses | Pattern matching, no LLM needed |
| **LLM Agent** | Conversations, analysis | Direct LLM calls, no tools |
| **RAG Agent** | Knowledge Q&A | Searches knowledge base, then responds |
| **Tool Agent** | Task automation | LLM + function calling (APIs, calculations) |
| **Full Agent** | Complex automation | Combines RAG + LLM + Tools |
| **Router Agent** | Multi-domain systems | Classifies intent, routes to other agents |
| **Orchestrator Agent** | Complex workflows | Coordinates multiple agents |

### Agent Configuration

Every agent consists of:

```
Agent
├── Identity
│   ├── Name (e.g., "Customer Support Agent")
│   ├── Description
│   └── Type (LLM, Tool, RAG, etc.)
│
├── Persona
│   ├── Role (who the agent is)
│   ├── Goal (what it aims to achieve)
│   └── Instructions (how it should behave)
│
├── Capabilities
│   ├── LLM Configuration (model, temperature)
│   ├── Tools (what actions it can take)
│   ├── Skills (domain expertise)
│   └── Knowledge Base (for RAG agents)
│
└── Safety
    ├── Content filtering
    └── Blocked topics
```

### Example: Creating a Support Agent

```yaml
Name: Customer Support Agent
Type: ToolAgent
Role:
  Title: Customer Support Specialist
  Expertise: Product knowledge, issue resolution
  Personality: Friendly, patient, professional

Goal:
  Objective: Help customers resolve issues quickly
  Success Criteria: Customer satisfaction, resolution rate

Instructions:
  Steps:
    - Greet the customer warmly
    - Understand their issue by asking clarifying questions
    - Search the knowledge base for solutions
    - Provide step-by-step guidance
    - Confirm the issue is resolved

Tools:
  - Knowledge Base Search
  - Ticket Creation
  - Email Notification
```

---

## 2.2 Skills

### What is a Skill?

A **Skill** is a reusable domain expertise module that enhances agents with specialized knowledge. Skills bundle:

- **Terminology**: Domain-specific terms and definitions
- **Reasoning Patterns**: Step-by-step frameworks for solving problems
- **Examples**: Input/output demonstrations
- **Resources**: Reference documents, templates, code snippets
- **Parameters**: Configurable settings

### Why Use Skills?

| Without Skills | With Skills |
|----------------|-------------|
| Generic responses | Domain-specific expertise |
| May use wrong terminology | Uses correct domain language |
| Basic reasoning | Structured problem-solving |
| No references | Access to templates and docs |

### Skill Categories

| Category | Use Case | Example |
|----------|----------|---------|
| **Domain Expertise** | Subject matter knowledge | Legal, Medical, Financial |
| **Document Generation** | Template-based creation | Contracts, Reports, Emails |
| **Data Analysis** | Data processing | Financial Analysis, Metrics |
| **Communication** | Style guidance | Sales, Support, Executive |
| **Research** | Methodology | Academic, Market Research |
| **Coding** | Programming patterns | Python, JavaScript, SQL |

### Skill Structure

```yaml
Skill: Legal Contract Analysis
Category: domain_expertise

Terminology:
  - Term: Force Majeure
    Definition: Unforeseeable circumstances preventing contract fulfillment
    Aliases: [act of god, uncontrollable event]

  - Term: Indemnification
    Definition: Protection against loss or legal liability

Reasoning Patterns:
  - Name: Contract Review Process
    Steps:
      1. Identify parties and effective date
      2. Review key terms and definitions
      3. Analyze obligations of each party
      4. Check for liability limitations
      5. Review termination clauses
      6. Identify potential risks

Examples:
  - Input: "Review this NDA for any red flags"
    Output: |
      Key observations:
      1. Non-compete clause extends 3 years (unusually long)
      2. Definition of "Confidential Information" is very broad
      3. No mutual confidentiality - one-sided protection
      Recommendation: Negotiate narrower scope and shorter duration

Resources:
  - NDA Template.docx
  - Contract Checklist.pdf
```

### How Skills Work with Agents

1. When creating an agent, you attach one or more skills
2. During execution, skill content is injected into the agent's context
3. The LLM gains access to terminology, reasoning frameworks, and examples
4. Agent responses become domain-aware and use proper terminology

---

## 2.3 Workflows

### What is a Workflow?

A **Workflow** is an orchestrated sequence of steps that can involve multiple agents, parallel execution, conditional branching, and loops. Workflows enable complex multi-step processes.

### Workflow vs Single Agent

| Single Agent | Workflow |
|--------------|----------|
| One-shot response | Multi-step process |
| One agent | Multiple agents |
| Simple tasks | Complex pipelines |
| Sequential | Parallel execution possible |

### Step Types

#### 1. Agent Step
Execute a single agent:
```yaml
Step: Analyze Customer Request
Type: agent
Agent: customer-intent-classifier
Input: ${user_input}
```

#### 2. Parallel Step
Execute multiple agents simultaneously:
```yaml
Step: Gather Information
Type: parallel
Branches:
  - Agent: product-lookup
    Input: ${product_id}
  - Agent: customer-history
    Input: ${customer_id}
  - Agent: inventory-check
    Input: ${product_id}
Aggregation: merge
```

#### 3. Conditional Step
Branch based on conditions:
```yaml
Step: Route by Sentiment
Type: conditional
Condition: ${steps.sentiment_analysis.result}
Branches:
  positive: upsell-agent
  negative: escalation-agent
  neutral: standard-response
```

#### 4. Loop Step
Iterate until condition:
```yaml
Step: Refine Response
Type: loop
Steps:
  - Agent: quality-checker
  - Agent: response-improver
Max Iterations: 3
Exit Condition: ${context.quality_score > 0.9}
```

### Example Workflow: Customer Support Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    Customer Message                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│           Step 1: Intent Classification                      │
│           Agent: intent-classifier                           │
│           Output: {intent: "technical_issue"}               │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
     [billing]      [technical]      [general]
          │               │               │
          ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Billing    │  │  Technical  │  │  General    │
│  Agent      │  │  Agent      │  │  Agent      │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           Step 3: Response Quality Check                     │
│           Agent: quality-checker                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Final Response                             │
└─────────────────────────────────────────────────────────────┘
```

### Creating Workflows

You can create workflows in three ways:

1. **From Scratch**: Use the visual builder to drag and drop steps
2. **From Template**: Copy an existing workflow and customize it
3. **AI Generated**: Describe what you need in natural language, and AI creates the workflow

---

## 2.4 Integrations (MCP)

### What is MCP?

**MCP (Model Context Protocol)** is a standardized way to connect AI agents with external services. MCP servers expose tools that agents can call during execution.

### Available Integrations

| Service | Tools Available |
|---------|-----------------|
| **Google Calendar** | List events, create event, update event, delete event |
| **Gmail** | List emails, send email, search emails |
| **Google Drive** | List files, upload file, download file |
| **Outlook Calendar** | List events, create event, update event |
| **Outlook Email** | List emails, send email |
| **Slack** | Send message, list channels, search messages |

### How MCP Works

1. **Connect**: Add an MCP server (e.g., Google Calendar)
2. **Authenticate**: Complete OAuth flow to authorize access
3. **Register Tools**: MCP server tools become available to agents
4. **Use in Agents**: Enable MCP tools for your agents
5. **Execute**: Agent calls tools during conversation

### Example: Calendar Agent

```yaml
Agent: Meeting Scheduler
Type: ToolAgent
Tools:
  - google-calendar:list_events
  - google-calendar:create_event
  - google-calendar:update_event

User: "Schedule a meeting with John tomorrow at 2pm"

Agent Process:
  1. Calls google-calendar:list_events to check availability
  2. Finds 2pm is free
  3. Calls google-calendar:create_event with:
     - Title: "Meeting with John"
     - Start: Tomorrow 2:00 PM
     - Duration: 1 hour
  4. Returns confirmation to user
```

---

# 3. Getting Started

## Quick Start Guide

### Step 1: Create Your First Agent

1. Navigate to **Agents** in the sidebar
2. Click **Create New Agent**
3. Fill in basic info:
   - **Name**: "My First Assistant"
   - **Type**: LLM Agent (simplest type)
   - **Description**: "A helpful assistant for general questions"
4. Configure the persona:
   - **Role**: "Helpful Assistant"
   - **Goal**: "Answer user questions accurately and helpfully"
5. Save the agent

### Step 2: Test Your Agent

1. Go to the agent detail page
2. Find the "Test Agent" section
3. Type a message: "Hello! What can you help me with?"
4. Click Send
5. See the agent's response

### Step 3: Add a Tool

1. Edit your agent
2. Change type to **Tool Agent**
3. In the Tools section, enable "Calculator"
4. Save
5. Test with: "What is 15% of 847?"

### Step 4: Create a Skill

1. Navigate to **Skills**
2. Click **Create New Skill**
3. Name it "Polite Assistant"
4. Add terminology:
   - "Customer" = "The person we're helping"
5. Add a reasoning pattern:
   - "Always greet warmly before answering"
   - "Thank the customer at the end"
6. Save and attach to your agent

### Step 5: Connect an Integration

1. Navigate to **Integrations** → **Servers**
2. Click **Add Server**
3. Select "Google Calendar"
4. Complete OAuth authorization
5. Enable calendar tools on your agent

---

# 4. How-To Guides

## 4.1 How to Create an Agent

### Basic Agent Creation

1. **Navigate**: Go to Agents → Create New Agent
2. **Basic Info**:
   - Enter a descriptive name
   - Select the appropriate agent type
   - Add a description
3. **Configure Persona**:
   - **Role**: Define who the agent is (title, expertise, personality)
   - **Goal**: Set the objective and success criteria
   - **Instructions**: Add step-by-step guidance
4. **Select LLM**: Choose provider (OpenAI/Anthropic) and model
5. **Save**: Click Create Agent

### Adding Tools to an Agent

1. Edit your agent
2. Scroll to "Tools" section
3. Browse available tools
4. Toggle tools ON/OFF
5. Configure tool-specific parameters if needed
6. Save changes

### Adding Skills to an Agent

1. Edit your agent
2. Scroll to "Skills" section
3. Browse available skills
4. Enable relevant skills
5. Configure skill parameters if available
6. Save changes

### AI-Powered Agent Generation

1. Go to Agents → Create New Agent
2. Click "Generate with AI"
3. Enter a natural language description:
   ```
   "Create a customer support agent that helps users
   troubleshoot software issues. It should be patient,
   technical, and always offer to escalate if needed."
   ```
4. Review the generated configuration
5. Customize as needed
6. Save

---

## 4.2 How to Create a Skill

### Creating a Domain Expertise Skill

1. **Navigate**: Go to Skills → Create New Skill
2. **Basic Info**:
   - Name: "Financial Analysis"
   - Category: Domain Expertise
   - Tags: finance, analysis, reporting
3. **Add Terminology**:
   ```
   Term: EBITDA
   Definition: Earnings Before Interest, Taxes, Depreciation, and Amortization
   Aliases: operating profit, operating earnings
   ```
4. **Add Reasoning Patterns**:
   ```
   Pattern: Financial Statement Analysis
   Steps:
   1. Review revenue trends (YoY, QoQ)
   2. Analyze gross margin and operating margin
   3. Evaluate cash flow from operations
   4. Check debt-to-equity ratio
   5. Compare against industry benchmarks
   6. Identify red flags or opportunities
   ```
5. **Add Examples**:
   ```
   Input: "Analyze this company's financial health"
   Output: "Based on the financial statements:
   - Revenue grew 15% YoY, indicating strong demand
   - Gross margin of 42% is above industry average (35%)
   - Operating cash flow positive for 8 consecutive quarters
   - Debt-to-equity ratio of 0.3 shows conservative leverage
   Overall Assessment: Strong financial position with room for growth investment"
   ```
6. **Upload Resources** (optional):
   - Financial analysis templates
   - Reference documents
7. **Save**

### Skill Parameters

Add configurable parameters:

```yaml
Parameter: analysis_depth
Type: select
Options: [quick, standard, comprehensive]
Default: standard
Description: Level of detail in the analysis
```

When agents use this skill, they can customize the analysis depth.

---

## 4.3 How to Create a Workflow

### Creating a Simple Sequential Workflow

1. **Navigate**: Go to Workflows → Create New Workflow
2. **Basic Info**:
   - Name: "Document Processing Pipeline"
   - Description: "Extracts, summarizes, and categorizes documents"
3. **Add Steps**:

   **Step 1**: Document Extraction
   ```yaml
   Type: agent
   Agent: document-extractor
   Input: ${user_input}
   ```

   **Step 2**: Summarization
   ```yaml
   Type: agent
   Agent: summarizer
   Input: ${steps.step1.output}
   ```

   **Step 3**: Categorization
   ```yaml
   Type: agent
   Agent: categorizer
   Input: ${steps.step2.output}
   ```

4. **Connect Steps**: Step 1 → Step 2 → Step 3
5. **Set Entry Point**: Step 1
6. **Save**

### Creating a Workflow with Parallel Execution

1. Create a new workflow
2. Add a parallel step:
   ```yaml
   Step: Research Phase
   Type: parallel
   Branches:
     - Agent: market-research
       Input: ${context.topic}
     - Agent: competitor-analysis
       Input: ${context.topic}
     - Agent: trend-analyzer
       Input: ${context.topic}
   Aggregation: merge
   ```
3. Add aggregation step:
   ```yaml
   Step: Compile Report
   Type: agent
   Agent: report-compiler
   Input: ${steps.research_phase.outputs}
   ```
4. Connect and save

### AI-Generated Workflows

1. Go to Workflows → Create New Workflow
2. Click "Generate with AI"
3. Describe your workflow:
   ```
   "Create a customer onboarding workflow that:
   1. Validates customer information
   2. Creates accounts in multiple systems (CRM, billing, support)
   3. Sends welcome email
   4. Schedules kickoff call
   Handle errors by notifying the ops team"
   ```
4. Review generated workflow and agents
5. Customize as needed
6. Save

---

## 4.4 How to Connect Integrations

### Connecting Google Calendar

1. **Navigate**: Integrations → Servers → Add Server
2. **Select Template**: Google Calendar
3. **Name**: "My Work Calendar"
4. **Authorize**:
   - Click "Connect to Google"
   - Sign in with your Google account
   - Grant calendar permissions
   - Return to MagoneAI
5. **Verify**: Status should show "Active"
6. **Use in Agent**:
   - Edit any Tool Agent
   - Enable calendar tools:
     - `google-calendar:list_events`
     - `google-calendar:create_event`
     - `google-calendar:update_event`
     - `google-calendar:delete_event`

### Connecting Gmail

1. **Navigate**: Integrations → Servers → Add Server
2. **Select Template**: Gmail
3. **Authorize**: Complete OAuth flow with Gmail permissions
4. **Enable Tools**:
   - `gmail:list_emails`
   - `gmail:send_email`
   - `gmail:search_emails`

### Using MCP Tools in Agents

Once connected, tools are available in agents:

```yaml
Agent: Executive Assistant
Type: ToolAgent
Tools:
  - google-calendar:list_events
  - google-calendar:create_event
  - gmail:send_email

User: "Check my calendar for tomorrow and email Sarah the agenda"

Agent Process:
1. Calls google-calendar:list_events for tomorrow
2. Compiles agenda from events
3. Calls gmail:send_email to Sarah with agenda
4. Confirms completion
```

---

## 4.5 How to Set Up a RAG Agent

### Creating a Knowledge Base

1. **Navigate**: Integrations → Knowledge → Create Collection
2. **Name**: "Product Documentation"
3. **Upload Documents**:
   - User guides
   - FAQ documents
   - Technical specifications
4. **Wait for Processing**: Documents are chunked and embedded

### Creating a RAG Agent

1. **Navigate**: Agents → Create New Agent
2. **Type**: RAG Agent
3. **Configure**:
   - Name: "Product Expert"
   - Knowledge Base: "Product Documentation"
   - Top K Results: 5 (how many chunks to retrieve)
4. **Set Persona**:
   - Role: Product specialist with deep knowledge
   - Goal: Answer questions using product documentation
   - Instructions: Always cite sources when possible

### How RAG Works

```
User Question: "How do I reset my password?"
        │
        ▼
┌───────────────────────┐
│   Embed Question      │
│   (Convert to vector) │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Search Knowledge    │
│   Base for Similar    │
│   Content             │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Retrieve Top 5      │
│   Relevant Chunks     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Add to LLM Context  │
│   + User Question     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Generate Answer     │
│   Based on Retrieved  │
│   Information         │
└───────────────────────┘
```

---

## 4.6 How to Monitor Agent Performance

### Viewing Analytics

1. **Navigate**: Monitoring
2. **Dashboard Shows**:
   - Total executions
   - Success rate
   - Average response time
   - Token usage
   - Tool usage breakdown

### Execution History

1. Go to an agent's detail page
2. View "Execution History" section
3. Click any execution to see:
   - Full conversation
   - Tools called
   - Response time
   - Token count
   - Any errors

### Setting Up Alerts

Configure alerts for:
- Error rate exceeds threshold
- Response time degradation
- Token usage spikes

---

# 5. API Reference

## Base URL
```
https://your-instance.magoneai.com/api/v1
```

## Authentication
```
Authorization: Bearer <your_jwt_token>
```

## Core Endpoints

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/agents` | List all agents |
| `POST` | `/agents` | Create new agent |
| `GET` | `/agents/{id}` | Get agent details |
| `PUT` | `/agents/{id}` | Update agent |
| `DELETE` | `/agents/{id}` | Delete agent |
| `POST` | `/agents/generate` | AI-generate agent config |

### Execute Agent

```bash
POST /workflow/execute
Content-Type: application/json

{
  "agent_id": "my-agent",
  "user_input": "What is the weather today?",
  "conversation_history": [],
  "session_id": "optional-session-id"
}
```

**Response**:
```json
{
  "content": "I don't have access to real-time weather data...",
  "success": true,
  "metadata": {
    "tools_used": [],
    "execution_time_ms": 1234,
    "tokens_used": 150
  }
}
```

### Skills

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/skills` | List all skills |
| `POST` | `/skills` | Create new skill |
| `GET` | `/skills/{id}` | Get skill details |
| `PUT` | `/skills/{id}` | Update skill |
| `DELETE` | `/skills/{id}` | Delete skill |
| `POST` | `/skills/{id}/files` | Upload skill resource |

### Workflows

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/workflows` | List all workflows |
| `POST` | `/workflows` | Create new workflow |
| `GET` | `/workflows/{id}` | Get workflow details |
| `PUT` | `/workflows/{id}` | Update workflow |
| `DELETE` | `/workflows/{id}` | Delete workflow |
| `GET` | `/workflows/{id}/executions` | List execution history |

### MCP Servers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/mcp/servers` | List connected servers |
| `POST` | `/mcp/servers` | Add new server |
| `DELETE` | `/mcp/servers/{id}` | Remove server |
| `GET` | `/mcp/catalog` | List available templates |
| `GET` | `/mcp/health` | Check server health |

### OAuth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/oauth/google/authorize-url` | Get OAuth URL |
| `GET` | `/oauth/google/callback` | OAuth callback handler |

---

# 6. Troubleshooting

## Common Issues

### Agent Not Responding

**Symptoms**: Agent hangs or times out

**Solutions**:
1. Check if the LLM provider (OpenAI/Anthropic) is accessible
2. Verify API keys are configured correctly
3. Check if Temporal workers are running
4. Review agent logs for errors

### Tool Execution Fails

**Symptoms**: "Tool execution failed" error

**Solutions**:
1. Verify MCP server is connected (check Integrations → Servers)
2. Re-authenticate if OAuth token expired
3. Check tool permissions
4. Review tool parameters in agent config

### Knowledge Base Search Returns Nothing

**Symptoms**: RAG agent doesn't find relevant content

**Solutions**:
1. Verify documents were uploaded successfully
2. Check if documents were processed (embedding complete)
3. Try rephrasing the question
4. Increase Top K results setting
5. Verify document content is relevant to question

### OAuth Connection Failed

**Symptoms**: Cannot connect Google services

**Solutions**:
1. Ensure popup blockers are disabled
2. Check if correct Google account is selected
3. Verify OAuth credentials in settings
4. Try disconnecting and reconnecting

### Workflow Stuck

**Symptoms**: Workflow execution doesn't complete

**Solutions**:
1. Check Temporal UI for workflow status
2. Review step configurations
3. Check for circular dependencies
4. Verify all referenced agents exist
5. Check timeout settings

---

# 7. FAQ

### General Questions

**Q: What's the difference between an Agent and a Workflow?**
A: An Agent is a single AI entity that handles one interaction. A Workflow orchestrates multiple agents and steps to handle complex, multi-stage processes.

**Q: Which agent type should I use?**
A:
- Simple questions → LLM Agent
- Knowledge-based Q&A → RAG Agent
- Task automation → Tool Agent
- Complex automation → Full Agent
- Multi-domain routing → Router Agent
- Multi-agent orchestration → Orchestrator Agent

**Q: How many skills can I attach to one agent?**
A: You can attach multiple skills, but keep in mind that more skills = more context for the LLM. We recommend 3-5 highly relevant skills per agent.

**Q: What LLM providers are supported?**
A: Currently OpenAI (GPT-4, GPT-4o, GPT-3.5-turbo) and Anthropic (Claude 3 Opus, Sonnet, Haiku).

### Skills Questions

**Q: What's the difference between Skills and Tools?**
A: Skills provide knowledge and reasoning (they enhance how the agent thinks). Tools provide actions (they enable what the agent can do).

**Q: Can I share skills across agents?**
A: Yes! Skills are designed to be reusable. Create once, use in many agents.

**Q: How do skill parameters work?**
A: Parameters let you customize skill behavior per agent. For example, a "writing style" skill might have a parameter for tone (formal/casual).

### Integration Questions

**Q: Is my data sent to external services?**
A: Only when you explicitly use MCP tools. Your data stays within MagoneAI unless an agent calls an external tool like Google Calendar.

**Q: How are OAuth tokens stored?**
A: OAuth tokens are stored encrypted in our secure vault. They're never exposed in the UI or API responses.

**Q: Can I connect custom APIs?**
A: Yes! You can add custom MCP servers by providing the server URL and credentials.

### Workflow Questions

**Q: What happens if a workflow step fails?**
A: You can configure error handling per step: retry, skip, or jump to an error handler.

**Q: Can workflows run on a schedule?**
A: Scheduled workflows are planned for a future release. Currently, workflows are triggered via API.

**Q: How long can workflows run?**
A: Workflows can run for hours thanks to Temporal's durable execution. Individual steps have configurable timeouts (default 5 minutes).

---

# Appendix: Glossary

| Term | Definition |
|------|------------|
| **Agent** | An AI entity configured to perform specific tasks |
| **Skill** | Reusable domain expertise module for agents |
| **Workflow** | Orchestrated sequence of steps involving agents |
| **MCP** | Model Context Protocol - standard for external integrations |
| **RAG** | Retrieval Augmented Generation - search before generate |
| **Tool** | An action an agent can perform (API call, calculation) |
| **LLM** | Large Language Model (GPT-4, Claude) |
| **Temporal** | Durable workflow execution engine |
| **Knowledge Base** | Collection of documents for RAG agents |
| **OAuth** | Authentication protocol for external services |

---

*Last updated: December 2024*
*Version: 2.0*

# MagoneAI Orchestrator Test Scenarios

> **Purpose**: Validate that the autonomous agent orchestration system works as envisioned - agents dynamically selected, chained, and coordinated by the OrchestratorAgent without rigid workflow definitions.

> **Focus Areas**: Documents, Calendar, Emails
> **Date**: December 2025
> **Last Updated**: 2026-01-02

---

## EXECUTION STATUS TRACKER

### Overall Progress
| Phase | Status | Notes |
|-------|--------|-------|
| Test Data Created | ✅ DONE | `tests/data/documents/`, `emails.json`, `calendar_events.json` |
| Knowledge Base Setup | ✅ DONE | `kb-1638ec52b443` - 13 docs indexed |
| Core Agents Created | ✅ DONE | research-agent, writer-agent, main-orchestrator, summarizer-agent, file-agent |
| MCP Servers Setup | ✅ DONE | OAuth resolved! All 3 MCP servers active |
| KB Enhancement | ✅ DONE | Added team-directory.md, company-contacts.md, updated client profiles |
| MCP Agents (email/calendar) | ✅ DONE | email-agent + calendar-agent created |
| Single-Domain Tests (D, E, C) | ⏳ PENDING | Ready to execute |
| Multi-Domain Tests | ⏳ PENDING | Ready to execute |
| Real-World Workflow Tests | ⏳ PENDING | Ready to execute |
| Results Report | ⏳ PENDING | Will generate after tests complete |

### Infrastructure Status
| Component | Status | Details |
|-----------|--------|---------|
| Docker Containers | ✅ Running | 18 services (API, Temporal, Postgres, Redis, Qdrant, MCPs, Monitoring) |
| API Server | ✅ Healthy | http://localhost:8000 |
| Web Frontend | ✅ Running | http://localhost:3000 |
| Temporal UI | ✅ Running | http://localhost:8080 |
| MCP Outlook Email | ✅ ACTIVE | srv_0de807a6136f |
| MCP Outlook Calendar | ✅ ACTIVE | srv_3110e8c1ce5b |
| MCP Filesystem | ✅ ACTIVE | srv_1dc8e1535b21 |
| Grafana | ✅ Running | http://localhost:3002 |

### MCP Server Status
| MCP Server | ID | Status | Last Used |
|------------|-----|--------|-----------|
| My Outlook Email | srv_0de807a6136f | ✅ ACTIVE | 2026-01-01 |
| My Outlook Calendar | srv_3110e8c1ce5b | ✅ ACTIVE | 2026-01-01 |
| Local Filesystem | srv_1dc8e1535b21 | ✅ ACTIVE | 2026-01-01 |

### Agent Setup Status
| Agent ID | Type | Status | Tools/KB |
|----------|------|--------|-----------|
| `research-agent` | RAGAgent | ✅ CREATED | KB: `kb-1638ec52b443` |
| `writer-agent` | LLMAgent | ✅ CREATED | Text generation (GPT-4o) |
| `main-orchestrator` | OrchestratorAgent | ✅ CREATED | Coordinates all agents |
| `summarizer-agent` | LLMAgent | ✅ CREATED | Summarization |
| `file-agent` | ToolAgent | ✅ CREATED | MCP: filesystem (srv_1dc8e1535b21) |
| `email-agent` | ToolAgent | ✅ CREATED | MCP: outlook-email (srv_0de807a6136f) |
| `calendar-agent` | ToolAgent | ✅ CREATED | MCP: outlook-calendar (srv_3110e8c1ce5b) |
| `mag-products-chatbot` | RAGAgent | ✅ CREATED | KB: mag products |

### Test Execution Progress
| Category | Total | Passed | Failed | Pending |
|----------|-------|--------|--------|---------|
| D (Documents) | 10 | 0 | 0 | 10 |
| C (Calendar) | 12 | 0 | 0 | 12 |
| E (Email) | 14 | 0 | 0 | 14 |
| DE (Doc+Email) | 10 | 0 | 0 | 10 |
| DC (Doc+Calendar) | 10 | 0 | 0 | 10 |
| EC (Email+Calendar) | 12 | 0 | 0 | 12 |
| DEC (All Three) | 10 | 0 | 0 | 10 |
| DECW (Full Stack) | 10 | 0 | 0 | 10 |
| RW (Real-World) | 12 | 0 | 0 | 12 |
| **TOTAL** | **100** | **0** | **0** | **100** |

---

## PREREQUISITES CHECKLIST

### Phase 1: Knowledge Base Enhancement ✅ COMPLETED

The KB now has **contact resolution** capabilities for scenarios like "Send email to Yash" or "Email Acme Corp".

#### 1.1 Team Directory ✅
- [x] Create `tests/data/documents/contacts/team-directory.md`
- [x] Index in KB

**Created Content:**
- Yash Karande (SDE) - yash.k@magureinc.com
- Pranav Agarwal (CTO) - pranav.ag@magureinc.com
- Quick lookup tables and contact guidelines

#### 1.2 Company Contacts Directory ✅
- [x] Create `tests/data/documents/contacts/company-contacts.md`
- [x] Index in KB

**Created Content:**
- Acme Corp → Account Manager: Yash Karande (yash.k@magureinc.com)
- Globex International → Account Manager: Pranav Agarwal (pranav.ag@magureinc.com)
- Quick lookup tables and escalation paths

#### 1.3 Updated Client Profiles ✅
- [x] Update `acme-corp-profile.md` - Added Internal Account Manager: Yash Karande
- [x] Update `globex-history.md` - Added Internal Account Manager: Pranav Agarwal
- [x] Re-indexed updated documents

### Phase 2: Agent Creation ✅ COMPLETED

#### 2.1 Email Agent ✅
- [x] Create `email-agent` (ToolAgent)
- [x] Connected to MCP: `srv_0de807a6136f` (outlook-email)
- [x] Tools enabled: send_email, list_emails, search_emails, get_email
- [x] Includes contact resolution rules (Yash → yash.k@magureinc.com, etc.)

#### 2.2 Calendar Agent ✅
- [x] Create `calendar-agent` (ToolAgent)
- [x] Connected to MCP: `srv_3110e8c1ce5b` (outlook-calendar)
- [x] Tools enabled: create_event, list_events, update_event, delete_event
- [x] Includes attendee resolution rules

### Phase 3: Validation Tests ⏳ PENDING

| Test | Input | Expected Output | Status |
|------|-------|-----------------|--------|
| Name Resolution | "What is Yash's email?" | yash.k@magureinc.com | ⏳ |
| Name Resolution | "What is Pranav's email?" | pranav.ag@magureinc.com | ⏳ |
| Role Lookup | "Who is the CTO?" | Pranav Agarwal | ⏳ |
| Company Contact | "Who manages Acme Corp?" | Yash Karande (yash.k@magureinc.com) | ⏳ |
| Company Contact | "Globex contact?" | Pranav Agarwal (pranav.ag@magureinc.com) | ⏳ |

---

## TEST EMAILS FOR MOCKING

| Name | Email | Role | Use For |
|------|-------|------|---------|
| Yash Karande | yash.k@magureinc.com | SDE | Primary test recipient |
| Pranav Agarwal | pranav.ag@magureinc.com | CTO | Secondary test recipient |

---

## REAL-WORLD WORKFLOW TEST SCENARIOS (NEW)

These scenarios test **context-aware, multi-step workflows** that simulate actual business use cases.

### Tier 1: Basic Contact Resolution
| ID | Scenario | Agents Used | Expected |
|----|----------|-------------|----------|
| RW1 | "What is Yash's email?" | research | yash.k@magureinc.com |
| RW2 | "Who is the CTO and what's their email?" | research | Pranav Agarwal, pranav.ag@magureinc.com |
| RW3 | "Find contact for Acme Corp" | research | Yash Karande, yash.k@magureinc.com |

### Tier 2: Document + Contact Resolution
| ID | Scenario | Agents Used | Expected |
|----|----------|-------------|----------|
| RW4 | "Send the return policy to Yash" | research → email | Lookup Yash email, send policy doc |
| RW5 | "Email project alpha specs to the CTO" | research → email | Lookup CTO (Pranav), send specs |
| RW6 | "Send Acme Corp profile to their account manager" | research → email | Find Yash, send acme-corp-profile.md |

### Tier 3: Document + Contact + Calendar
| ID | Scenario | Agents Used | Expected |
|----|----------|-------------|----------|
| RW7 | "Send project alpha to Yash and schedule a discussion" | research → writer → email → calendar | Full workflow |
| RW8 | "Email the contract terms to Acme and set up a call" | research → writer → email → calendar | Lookup Acme contact, send, schedule |
| RW9 | "Share Q4 planning with Pranav and block time to review" | research → email → calendar | Multi-step |

### Tier 4: Complex Business Workflows
| ID | Scenario | Agents Used | Expected |
|----|----------|-------------|----------|
| RW10 | "Prepare for Acme meeting: send them latest docs and create calendar invite" | research → writer → email → calendar | Full prep workflow |
| RW11 | "Onboard Globex: send welcome docs to their contact and schedule kickoff" | research → writer → email → calendar | Onboarding workflow |
| RW12 | "I want to discuss the privacy policy updates with the CTO - send the doc and schedule time" | research → email → calendar | Policy review workflow |

---

### Next Steps (Current Action Items)

**✅ COMPLETED:**
- [x] Create knowledge base with test documents (13 docs indexed)
- [x] Create research-agent (RAGAgent)
- [x] Create writer-agent (LLMAgent)
- [x] Create main-orchestrator (OrchestratorAgent)
- [x] Create summarizer-agent (LLMAgent)
- [x] Create file-agent (ToolAgent)
- [x] Resolve Microsoft OAuth issue
- [x] Connect Outlook Email MCP (srv_0de807a6136f)
- [x] Connect Outlook Calendar MCP (srv_3110e8c1ce5b)
- [x] Create team-directory.md with employee contacts
- [x] Create company-contacts.md with client contacts
- [x] Update acme-corp-profile.md with contact email
- [x] Update globex-history.md with contact email
- [x] Index new/updated documents in KB (13 total docs)
- [x] Create email-agent (ToolAgent with outlook-email MCP)
- [x] Create calendar-agent (ToolAgent with outlook-calendar MCP)

**⏳ PENDING (Ready to Execute):**
1. [ ] Run validation tests (name/company resolution) - Phase 3
2. [ ] Run D1-D10 (Document-only tests)
3. [ ] Run C1-C12 (Calendar-only tests)
4. [ ] Run E1-E14 (Email-only tests)
5. [ ] Run Multi-Domain tests (DE, DC, EC, DEC, DECW)
6. [ ] Run Real-World Workflow tests (RW1-RW12)
7. [ ] Generate test results report

### Test Data Locations ✅ CREATED
```
tests/data/
├── documents/
│   ├── policies/          # return-policy.md, privacy-policy.md, employee-handbook.md, support-sla.md (4 files)
│   ├── projects/          # project-alpha-specs.md, q4-planning.md (2 files)
│   ├── clients/           # acme-corp-profile.md (→Yash), globex-history.md (→Pranav) (2 files)
│   ├── contacts/          # team-directory.md, company-contacts.md ✅ (2 files)
│   ├── templates/         # meeting-notes-template.md, email-response-template.md (2 files)
│   └── knowledge-base/    # faq.md (1 file)
├── emails.json            # 10 test emails with various labels
└── calendar_events.json   # 8 test calendar events

Total: 13 documents indexed in KB (kb-1638ec52b443)
```

### API Credentials
- **Login**: `admin@magure.ai` / `admin123`
- **API Base**: `http://localhost:8000/api/v1`

---

## Table of Contents

1. [Test Environment Setup](#1-test-environment-setup)
2. [Single Domain Scenarios](#2-single-domain-scenarios)
3. [Two-Domain Combinations](#3-two-domain-combinations)
4. [Three-Domain Combinations](#4-three-domain-combinations)
5. [Full Stack Scenarios](#5-full-stack-scenarios)
6. [Agent Chaining Patterns](#6-agent-chaining-patterns)
7. [MCP Integration Deep Dive](#7-mcp-integration-deep-dive)
8. [Real-World Business Scenarios](#8-real-world-business-scenarios)
9. [Error Handling & Recovery](#9-error-handling--recovery)
10. [Quality Assurance Scenarios](#10-quality-assurance-scenarios)
11. [Performance & Observability](#11-performance--observability)
12. [User Experience Scenarios](#12-user-experience-scenarios)
13. [Edge Cases](#13-edge-cases)

---

## 1. Test Environment Setup

### 1.1 Required Agents

| Agent Name | Type | Purpose | MCP/Tools | Status |
|------------|------|---------|-----------|--------|
| `research-agent` | RAGAgent | Document search & retrieval | KB: kb-1638ec52b443 | ✅ |
| `writer-agent` | LLMAgent | Content creation & formatting | Text generation (GPT-4o) | ✅ |
| `email-agent` | ToolAgent | Email operations | MCP: outlook-email | ✅ |
| `calendar-agent` | ToolAgent | Schedule management | MCP: outlook-calendar | ✅ |
| `file-agent` | ToolAgent | File operations | MCP: filesystem | ✅ |
| `summarizer-agent` | LLMAgent | Condensing information | Summarization | ✅ |
| `main-orchestrator` | OrchestratorAgent | Central coordinator | All above as sub-agents | ✅ |
| `mag-products-chatbot` | RAGAgent | Product knowledge | KB: mag products | ✅ |

**Note:** Web search agent and classifier agent are not yet implemented but can be added later for scenarios requiring internet research or advanced intent routing.

### 1.2 Required MCP Servers

| MCP Server | ID | Purpose | Key Operations | Status |
|------------|-----|---------|----------------|--------|
| **Filesystem** | srv_1dc8e1535b21 | Document storage & retrieval | read_file, write_file, list_directory | ✅ ACTIVE |
| **Outlook Email** | srv_0de807a6136f | Email communication | send_email, list_emails, search_emails, get_email | ✅ ACTIVE |
| **Outlook Calendar** | srv_3110e8c1ce5b | Schedule management | create_event, list_events, update_event, delete_event | ✅ ACTIVE |

**Note:** Web Search MCP is not yet configured but can be added for scenarios requiring internet research.

### 1.3 Test Data Requirements ✅ CREATED

```
tests/data/
├── documents/
│   ├── policies/
│   │   ├── return-policy.md        ✅ Indexed
│   │   ├── privacy-policy.md       ✅ Indexed
│   │   ├── employee-handbook.md    ✅ Indexed
│   │   └── support-sla.md          ✅ Indexed
│   ├── projects/
│   │   ├── project-alpha-specs.md  ✅ Indexed
│   │   └── q4-planning.md          ✅ Indexed
│   ├── clients/
│   │   ├── acme-corp-profile.md    ✅ Indexed (with internal account manager)
│   │   └── globex-history.md       ✅ Indexed (with internal account manager)
│   ├── contacts/                   ✅ NEW
│   │   ├── team-directory.md       ✅ Indexed (Yash SDE, Pranav CTO)
│   │   └── company-contacts.md     ✅ Indexed (Acme→Yash, Globex→Pranav)
│   ├── templates/
│   │   ├── meeting-notes-template.md   ✅ Indexed
│   │   └── email-response-template.md  ✅ Indexed
│   └── knowledge-base/
│       └── faq.md                  ✅ Indexed
├── calendar_events.json            ✅ Created (8 test events)
└── emails.json                     ✅ Created (10 test emails)
```

**Total KB Documents: 13 (all indexed in kb-1638ec52b443)**

### 1.4 Sample Calendar Events

```json
{
  "events": [
    {
      "id": "evt-001",
      "title": "Weekly Team Standup",
      "start": "2025-01-06T09:00:00",
      "end": "2025-01-06T09:30:00",
      "attendees": ["alice@company.com", "bob@company.com"],
      "recurring": "weekly",
      "description": "Weekly sync on project progress"
    },
    {
      "id": "evt-002",
      "title": "Client Meeting - Acme Corp",
      "start": "2025-01-07T14:00:00",
      "end": "2025-01-07T15:00:00",
      "attendees": ["john@acmecorp.com", "sales@company.com"],
      "description": "Q1 contract renewal discussion"
    },
    {
      "id": "evt-003",
      "title": "Project Alpha Review",
      "start": "2025-01-08T11:00:00",
      "end": "2025-01-08T12:00:00",
      "attendees": ["dev-team@company.com"],
      "description": "Sprint review and demo"
    },
    {
      "id": "evt-004",
      "title": "1:1 with Manager",
      "start": "2025-01-09T10:00:00",
      "end": "2025-01-09T10:30:00",
      "attendees": ["manager@company.com"],
      "recurring": "weekly"
    },
    {
      "id": "evt-005",
      "title": "Q4 Planning Session",
      "start": "2025-01-10T13:00:00",
      "end": "2025-01-10T16:00:00",
      "attendees": ["leadership@company.com"],
      "description": "Strategic planning for next quarter"
    }
  ]
}
```

### 1.5 Sample Emails

```json
{
  "emails": [
    {
      "id": "email-001",
      "from": "customer@example.com",
      "to": "support@company.com",
      "subject": "How do I reset my password?",
      "body": "I forgot my password and can't log in. Can you help me reset it?",
      "date": "2025-01-05T08:30:00",
      "read": false,
      "labels": ["support", "unread"]
    },
    {
      "id": "email-002",
      "from": "john@acmecorp.com",
      "to": "sales@company.com",
      "subject": "Re: Contract Renewal",
      "body": "Thanks for sending the proposal. We'd like to discuss a few points before our meeting next week. Can you send the updated pricing sheet?",
      "date": "2025-01-05T10:15:00",
      "read": false,
      "labels": ["client", "important"]
    },
    {
      "id": "email-003",
      "from": "manager@company.com",
      "to": "employee@company.com",
      "subject": "Project Alpha Update Needed",
      "body": "Hi, can you prepare a status update on Project Alpha before our 1:1 this week? Include any blockers and timeline updates.",
      "date": "2025-01-05T11:00:00",
      "read": true,
      "labels": ["internal", "action-required"]
    },
    {
      "id": "email-004",
      "from": "frustrated@user.com",
      "to": "support@company.com",
      "subject": "URGENT: Service Down for 2 Hours!",
      "body": "This is unacceptable! Our service has been down for 2 hours and we're losing money. I need someone to call me immediately at 555-1234.",
      "date": "2025-01-05T14:20:00",
      "read": false,
      "labels": ["support", "urgent", "escalation"]
    },
    {
      "id": "email-005",
      "from": "newsletter@industry.com",
      "to": "employee@company.com",
      "subject": "Weekly AI Industry Digest",
      "body": "This week in AI: New developments in agentic systems, LLM benchmarks, and more...",
      "date": "2025-01-05T06:00:00",
      "read": true,
      "labels": ["newsletter"]
    },
    {
      "id": "email-006",
      "from": "hr@company.com",
      "to": "all@company.com",
      "subject": "Updated PTO Policy",
      "body": "Please review the updated PTO policy attached. Key changes include...",
      "date": "2025-01-04T09:00:00",
      "read": true,
      "labels": ["hr", "policy"],
      "attachments": ["pto-policy-2025.pdf"]
    },
    {
      "id": "email-007",
      "from": "partner@globex.com",
      "to": "partnerships@company.com",
      "subject": "Integration Proposal",
      "body": "We're interested in exploring an integration between our platforms. Would you be available for a call next week?",
      "date": "2025-01-05T15:45:00",
      "read": false,
      "labels": ["partnership", "opportunity"]
    },
    {
      "id": "email-008",
      "from": "dev@company.com",
      "to": "team@company.com",
      "subject": "Sprint Retrospective Notes",
      "body": "Attached are the notes from yesterday's retro. Action items: 1. Improve test coverage, 2. Document API changes, 3. Schedule knowledge sharing session.",
      "date": "2025-01-03T17:00:00",
      "read": true,
      "labels": ["team", "meeting-notes"]
    }
  ]
}
```

---

## 2. Single Domain Scenarios

### 2.1 Documents Only (D)

| ID | Input | Expected Agent(s) | Expected Behavior |
|----|-------|-------------------|-------------------|
| D1 | "What is our return policy?" | research-agent | RAG search on policy docs, return answer |
| D2 | "Find all documents about Project Alpha" | research-agent | Search and list relevant docs |
| D3 | "Summarize the employee handbook" | research-agent → summarizer-agent | Retrieve doc, summarize key points |
| D4 | "What's the SLA for enterprise customers?" | research-agent | Search support-sla.md |
| D5 | "List all client profiles we have" | file-agent | List files in clients/ directory |
| D6 | "Read the Q4 planning document" | file-agent | Read and return content |
| D7 | "Create a new document with meeting notes" | file-agent | Write new file |
| D8 | "Search for 'pricing' in all documents" | research-agent | Full-text search |
| D9 | "What do we know about Acme Corp?" | research-agent | Search client profile |
| D10 | "Compare our privacy policy with return policy" | research-agent → writer-agent | Retrieve both, create comparison |

**Validation Checklist for Documents:**
- [ ] RAG search returns relevant results
- [ ] File operations work correctly
- [ ] Summarization is accurate
- [ ] Search across multiple docs works
- [ ] New document creation works

---

### 2.2 Calendar Only (C)

| ID | Input | Expected Agent(s) | Expected Behavior |
|----|-------|-------------------|-------------------|
| C1 | "What meetings do I have today?" | calendar-agent | Query today's events |
| C2 | "What's on my schedule this week?" | calendar-agent | Query week's events |
| C3 | "When is my next meeting with Acme Corp?" | calendar-agent | Search by attendee/title |
| C4 | "Find a free 1-hour slot tomorrow" | calendar-agent | Check availability |
| C5 | "Schedule a meeting with Bob at 2pm Friday" | calendar-agent | Create new event |
| C6 | "Move the Project Alpha Review to Thursday" | calendar-agent | Update event |
| C7 | "Cancel my 1:1 with Manager this week" | calendar-agent | Delete event |
| C8 | "Who is attending the Q4 Planning Session?" | calendar-agent | Get event details |
| C9 | "What recurring meetings do I have?" | calendar-agent | Filter recurring events |
| C10 | "Block 2 hours for deep work tomorrow morning" | calendar-agent | Create focus time event |
| C11 | "When am I free to meet with the dev team?" | calendar-agent | Find overlapping availability |
| C12 | "List all client meetings this month" | calendar-agent | Filter by label/attendee |

**Validation Checklist for Calendar:**
- [ ] Event queries return correct results
- [ ] Event creation works
- [ ] Event updates work
- [ ] Event deletion works
- [ ] Free time calculation is accurate
- [ ] Recurring events handled correctly

---

### 2.3 Email Only (E)

| ID | Input | Expected Agent(s) | Expected Behavior |
|----|-------|-------------------|-------------------|
| E1 | "Check my inbox for unread emails" | email-agent | List unread emails |
| E2 | "Show me emails from Acme Corp" | email-agent | Search by sender |
| E3 | "Find urgent emails" | email-agent | Filter by label/priority |
| E4 | "Read the email from my manager" | email-agent | Get specific email content |
| E5 | "Send email to john@acme.com saying 'Meeting confirmed'" | email-agent | Send new email |
| E6 | "Reply to the password reset request" | email-agent → writer-agent | Read, draft, send |
| E7 | "Forward the contract email to legal team" | email-agent | Forward email |
| E8 | "Mark all newsletters as read" | email-agent | Bulk update |
| E9 | "Search for emails containing 'proposal'" | email-agent | Full-text search |
| E10 | "What support requests came in today?" | email-agent | Filter by label + date |
| E11 | "Draft a response to the frustrated customer" | email-agent → writer-agent | Compose empathetic response |
| E12 | "Summarize all unread emails" | email-agent → summarizer-agent | List and summarize |
| E13 | "Find emails with attachments" | email-agent | Filter by attachment |
| E14 | "Archive all emails older than 30 days" | email-agent | Bulk archive |

**Validation Checklist for Email:**
- [ ] Inbox query works
- [ ] Search by various criteria works
- [ ] Send email works
- [ ] Reply works
- [ ] Forward works
- [ ] Bulk operations work

---

## 3. Two-Domain Combinations

### 3.1 Documents + Email (D+E)

| ID | Input | Agent Chain | Data Flow |
|----|-------|-------------|-----------|
| DE1 | "Find our return policy and email it to customer@example.com" | research → email | Policy text → Email body |
| DE2 | "What does the email from Acme say, and do we have docs about them?" | email → research | Email context → Doc search |
| DE3 | "Search emails for Project Alpha updates, compare with project docs" | email → research → writer | Email content + Doc content → Comparison |
| DE4 | "Save the contract email as a document" | email → file | Email content → New file |
| DE5 | "Find FAQ answer and reply to support email" | research → email | FAQ answer → Email reply |
| DE6 | "Email the employee handbook to new hire" | research → email | Document → Email attachment |
| DE7 | "Check if email mentions anything in our knowledge base" | email → research | Email keywords → KB search |
| DE8 | "Create document summarizing all client emails this week" | email → summarizer → file | Emails → Summary doc |
| DE9 | "Find template for support response and use it to reply" | research → writer → email | Template + context → Email |
| DE10 | "What policies are mentioned in HR emails?" | email → research | Email refs → Policy lookup |

**Detailed Test Case DE1:**
```
Input: "Find our return policy and email it to customer@example.com"

Expected Execution:
1. Orchestrator analyzes: need document retrieval + email send
2. research-agent: Search for "return policy"
3. Returns: return-policy.md content
4. email-agent: send_email(
     to="customer@example.com",
     subject="Our Return Policy",
     body=policy_content
   )
5. Confirm email sent

Validation:
- [ ] Correct document found
- [ ] Email contains accurate policy text
- [ ] Email sent successfully
- [ ] Temporal trace shows both agents
```

---

### 3.2 Documents + Calendar (D+C)

| ID | Input | Agent Chain | Data Flow |
|----|-------|-------------|-----------|
| DC1 | "What docs should I review before my Acme meeting?" | calendar → research | Meeting context → Relevant docs |
| DC2 | "Find Project Alpha docs and schedule review meeting" | research → calendar | Docs found → Create meeting |
| DC3 | "What was discussed in Q4 planning? When is the next session?" | research → calendar | Doc lookup + Event query |
| DC4 | "Prepare briefing doc for tomorrow's client meeting" | calendar → research → writer | Meeting → Relevant info → Doc |
| DC5 | "Schedule time to review the new privacy policy" | research → calendar | Policy doc → Calendar event |
| DC6 | "What meetings relate to documents I updated this week?" | file → calendar | File metadata → Meeting search |
| DC7 | "Create meeting notes template for Project Alpha Review" | calendar → file | Meeting details → Template doc |
| DC8 | "Find free time this week to work on Q4 planning doc" | calendar | Free time for doc work |
| DC9 | "What documentation is due before the sprint review?" | calendar → research | Meeting deadline → Doc search |
| DC10 | "Check if we have prep docs for all meetings tomorrow" | calendar → research | Tomorrow's meetings → Doc check |

**Detailed Test Case DC4:**
```
Input: "Prepare briefing doc for tomorrow's client meeting"

Expected Execution:
1. calendar-agent: Get tomorrow's meetings
2. Identify client meeting (Acme Corp)
3. research-agent: Search for Acme Corp docs, previous meeting notes
4. research-agent: Get relevant product docs
5. writer-agent: Compile briefing document
6. file-agent: Save as "acme-meeting-briefing-2025-01-07.md"

Validation:
- [ ] Correct meeting identified
- [ ] Relevant client info found
- [ ] Briefing is comprehensive
- [ ] Document saved correctly
```

---

### 3.3 Email + Calendar (E+C)

| ID | Input | Agent Chain | Data Flow |
|----|-------|-------------|-----------|
| EC1 | "Check for meeting requests in my email" | email → calendar | Meeting emails → Create events |
| EC2 | "Email attendees of tomorrow's meeting with agenda" | calendar → email | Attendee list → Email send |
| EC3 | "Find emails related to my next meeting" | calendar → email | Meeting topic → Email search |
| EC4 | "Send meeting invite for next week's review" | calendar → email | Create event + Send invites |
| EC5 | "What did John email about before our meeting?" | calendar → email | Meeting context → Email search |
| EC6 | "Reschedule meeting and notify attendees" | calendar → email | Update event → Send update emails |
| EC7 | "Cancel meeting and email apology to attendees" | calendar → email | Delete event → Send cancellation |
| EC8 | "Find a time that works for email sender to meet" | email → calendar | Sender context → Free time |
| EC9 | "Create follow-up meeting from email discussion" | email → calendar | Email content → New meeting |
| EC10 | "Send reminder email for meetings tomorrow" | calendar → email | Tomorrow's events → Reminder emails |
| EC11 | "Check if partner@globex meeting request conflicts" | email → calendar | Proposed time → Conflict check |
| EC12 | "Email weekly schedule summary to team" | calendar → email | Week's events → Summary email |

**Detailed Test Case EC6:**
```
Input: "Reschedule the Project Alpha Review to Friday and notify everyone"

Expected Execution:
1. calendar-agent: Find "Project Alpha Review" event
2. calendar-agent: Update event to Friday
3. calendar-agent: Get attendee list
4. email-agent: Send reschedule notification to each attendee
5. Confirm completion

Validation:
- [ ] Correct event found
- [ ] Event updated to Friday
- [ ] All attendees notified
- [ ] Email contains old and new times
```

---

### 3.4 Documents + Writer (D+W)

| ID | Input | Agent Chain | Data Flow |
|----|-------|-------------|-----------|
| DW1 | "Summarize the employee handbook in bullet points" | research → writer | Full doc → Summary |
| DW2 | "Rewrite the return policy in simpler terms" | research → writer | Policy → Simplified version |
| DW3 | "Create FAQ from our knowledge base articles" | research → writer | KB docs → FAQ format |
| DW4 | "Translate the privacy policy to plain English" | research → writer | Legal doc → Plain language |
| DW5 | "Combine all project docs into executive summary" | research → writer | Multiple docs → Summary |
| DW6 | "Extract action items from meeting notes" | file → writer | Notes → Action list |
| DW7 | "Create onboarding guide from handbook" | research → writer | Handbook → Guide format |
| DW8 | "Generate report from project specs" | research → writer | Specs → Report |
| DW9 | "Make the troubleshooting guide more user-friendly" | research → writer | Tech doc → User-friendly |
| DW10 | "Create comparison table of all client contracts" | research → writer | Contracts → Table format |

---

### 3.5 Email + Writer (E+W)

| ID | Input | Agent Chain | Data Flow |
|----|-------|-------------|-----------|
| EW1 | "Draft professional response to angry customer" | email → writer → email | Angry email → Empathetic response |
| EW2 | "Summarize this email thread" | email → writer | Thread → Summary |
| EW3 | "Write follow-up email based on previous exchange" | email → writer → email | Context → Follow-up |
| EW4 | "Improve the tone of this draft email" | email → writer | Draft → Polished |
| EW5 | "Create template from this good response" | email → writer → file | Good email → Template |
| EW6 | "Translate this email to formal business English" | email → writer | Casual → Formal |
| EW7 | "Write apology email for service outage" | writer → email | Context → Apology email |
| EW8 | "Condense this long email into key points" | email → writer | Long email → Bullets |
| EW9 | "Draft responses to all unread support emails" | email → writer | Multiple emails → Responses |
| EW10 | "Write thank you email after meeting" | writer → email | Meeting context → Thanks |

---

### 3.6 Calendar + Writer (C+W)

| ID | Input | Agent Chain | Data Flow |
|----|-------|-------------|-----------|
| CW1 | "Write agenda for tomorrow's team meeting" | calendar → writer | Meeting info → Agenda |
| CW2 | "Create meeting notes template for client call" | calendar → writer | Meeting type → Template |
| CW3 | "Summarize my week's schedule" | calendar → writer | Week events → Summary |
| CW4 | "Write meeting invitation message" | calendar → writer | Event details → Invite text |
| CW5 | "Generate weekly schedule report" | calendar → writer | Events → Report |
| CW6 | "Create calendar description for new event" | writer → calendar | Context → Event description |
| CW7 | "Write prep checklist for client meeting" | calendar → writer | Meeting → Checklist |
| CW8 | "Summarize meeting purpose for attendees" | calendar → writer | Event → Summary |
| CW9 | "Create post-meeting action items template" | calendar → writer | Meeting type → Template |
| CW10 | "Write schedule overview for stakeholders" | calendar → writer | Events → Overview |

---

## 4. Three-Domain Combinations

### 4.1 Documents + Email + Calendar (D+E+C)

| ID | Input | Agent Chain | Scenario |
|----|-------|-------------|----------|
| DEC1 | "Prepare for Acme meeting: find docs, check emails, confirm time" | calendar → research → email | Full meeting prep |
| DEC2 | "Email client profile to attendees before meeting" | calendar → research → email | Doc to meeting attendees |
| DEC3 | "Find what was discussed in emails, docs, and meetings about Project Alpha" | research → email → calendar | Cross-domain search |
| DEC4 | "Create meeting summary doc and email to attendees" | calendar → writer → file → email | Post-meeting workflow |
| DEC5 | "Check if email topic is covered in docs, schedule meeting if not" | email → research → calendar | Gap analysis + action |
| DEC6 | "Find policy mentioned in email, schedule review meeting" | email → research → calendar | Email trigger → meeting |
| DEC7 | "Email meeting prep docs to all attendees tomorrow" | calendar → research → email | Batch prep |
| DEC8 | "Search docs and emails for context, add to meeting description" | research → email → calendar | Enrich meeting |
| DEC9 | "After meeting, file notes and email summary to team" | calendar → file → email | Post-meeting |
| DEC10 | "What client docs relate to today's meetings? Email gaps to team" | calendar → research → email | Prep check |

**Detailed Test Case DEC1:**
```
Input: "Prepare me for my Acme Corp meeting"

Expected Execution:
1. calendar-agent: Find next Acme Corp meeting
   → Returns: Tuesday 2pm, Contract renewal discussion
2. research-agent: Search for Acme Corp docs
   → Returns: acme-corp-profile.md, previous meeting notes
3. email-agent: Search recent Acme emails
   → Returns: Contract email thread
4. writer-agent: Compile briefing
5. Return comprehensive preparation summary

Validation:
- [ ] Meeting correctly identified
- [ ] Relevant docs found
- [ ] Recent emails included
- [ ] Briefing is coherent and useful
- [ ] All three domains represented
```

---

### 4.2 Documents + Email + Writer (D+E+W)

| ID | Input | Agent Chain | Scenario |
|----|-------|-------------|----------|
| DEW1 | "Find FAQ, draft response to support email" | research → writer → email | KB-powered response |
| DEW2 | "Summarize email thread, compare with docs, write report" | email → research → writer | Cross-reference report |
| DEW3 | "Read template, customize for this email, send" | research → writer → email | Template usage |
| DEW4 | "Find doc, summarize, email summary to team" | research → writer → email | Doc distribution |
| DEW5 | "Analyze email, find related policies, draft response" | email → research → writer → email | Policy-informed response |
| DEW6 | "Create email newsletter from recent doc updates" | research → writer → email | Content curation |
| DEW7 | "Compare email proposal with our docs, write analysis" | email → research → writer | Proposal analysis |
| DEW8 | "Find onboarding docs, create welcome email for new hire" | research → writer → email | Onboarding |
| DEW9 | "Extract info from email, update relevant doc" | email → research → writer → file | Doc update |
| DEW10 | "Find similar past responses, draft reply based on them" | email → research → writer → email | Pattern-based response |

**Detailed Test Case DEW5:**
```
Input: "The customer is asking about refunds - find our policy and draft a helpful response"

Expected Execution:
1. email-agent: Get customer email about refunds
2. research-agent: Search for refund/return policy
3. writer-agent: Draft response incorporating:
   - Empathy for customer
   - Clear policy information
   - Steps to proceed
4. email-agent: Send response (or save as draft)

Validation:
- [ ] Customer email understood
- [ ] Correct policy found
- [ ] Response is helpful and accurate
- [ ] Policy correctly cited
```

---

### 4.3 Documents + Calendar + Writer (D+C+W)

| ID | Input | Agent Chain | Scenario |
|----|-------|-------------|----------|
| DCW1 | "Create meeting agenda from project docs" | research → writer → calendar | Doc-driven agenda |
| DCW2 | "Write prep doc for all meetings this week" | calendar → research → writer | Batch prep |
| DCW3 | "Generate weekly planning doc from calendar" | calendar → writer → file | Calendar to doc |
| DCW4 | "Find docs for meeting, summarize key points" | calendar → research → writer | Meeting prep |
| DCW5 | "Create training schedule from handbook chapters" | research → writer → calendar | Learning path |
| DCW6 | "Write meeting minutes template for recurring meetings" | calendar → research → writer | Template creation |
| DCW7 | "Compile docs mentioned in calendar events" | calendar → research → file | Doc compilation |
| DCW8 | "Create executive briefing for board meeting" | calendar → research → writer | High-level prep |
| DCW9 | "Generate timeline doc from project calendar" | calendar → writer → file | Project timeline |
| DCW10 | "Write project status update for review meeting" | calendar → research → writer | Status report |

---

### 4.4 Email + Calendar + Writer (E+C+W)

| ID | Input | Agent Chain | Scenario |
|----|-------|-------------|----------|
| ECW1 | "Write meeting summary, email to attendees" | calendar → writer → email | Post-meeting |
| ECW2 | "Draft meeting request email for next week" | calendar → writer → email | Meeting request |
| ECW3 | "Create email recap of today's meetings" | calendar → writer → email | Daily recap |
| ECW4 | "Write thank you emails after all meetings today" | calendar → writer → email | Batch thanks |
| ECW5 | "Email schedule summary for the week" | calendar → writer → email | Schedule sharing |
| ECW6 | "Draft rescheduling email based on conflicts" | calendar → writer → email | Conflict resolution |
| ECW7 | "Create meeting action items, email to responsible parties" | calendar → writer → email | Action distribution |
| ECW8 | "Write prep email for attendees before meeting" | calendar → writer → email | Pre-meeting |
| ECW9 | "Summarize email requests, schedule accordingly" | email → calendar → writer → email | Request handling |
| ECW10 | "Create email template for meeting follow-ups" | calendar → writer → file | Template |

---

## 5. Full Stack Scenarios

### 5.1 All Four Domains (D+E+C+W)

| ID | Input | Full Chain | Business Scenario |
|----|-------|------------|-------------------|
| DECW1 | "Prepare fully for client meeting: docs, emails, agenda, send prep to team" | calendar → research → email → writer → email | Complete meeting prep |
| DECW2 | "After meeting, create notes doc, email summary to attendees" | calendar → writer → file → email | Post-meeting workflow |
| DECW3 | "Find all info about Project Alpha across docs and emails, create report, schedule review, notify team" | research → email → writer → file → calendar → email | Comprehensive project review |
| DECW4 | "Handle support email: find KB answer, check related meetings, draft response, log for follow-up" | email → research → calendar → writer → file → email | Complete support handling |
| DECW5 | "Create weekly team update: calendar events, doc changes, email highlights, send to team" | calendar → research → email → writer → email | Weekly digest |
| DECW6 | "Onboard new client: find templates, create custom docs, schedule kickoff, send welcome email" | research → writer → file → calendar → email | Client onboarding |
| DECW7 | "End of day: summarize meetings, pending emails, doc changes, email summary to myself" | calendar → email → research → writer → email | Daily review |
| DECW8 | "Research topic from docs and emails, write report, schedule presentation, invite stakeholders" | research → email → writer → file → calendar → email | Research to presentation |
| DECW9 | "Audit project: check docs vs emails vs meetings for consistency, create gap analysis" | research → email → calendar → writer → file | Compliance audit |
| DECW10 | "Create and distribute meeting prep pack for leadership meeting" | calendar → research → email → writer → file → email | Leadership prep |

**Detailed Test Case DECW1:**
```
Input: "I have a meeting with Acme Corp tomorrow - prepare everything I need and send a briefing to my team"

Expected Execution:
1. calendar-agent: Get tomorrow's Acme meeting details
   → Meeting at 2pm, attendees: [list]
2. research-agent: Search Acme docs
   → Client profile, contract history, previous notes
3. email-agent: Search recent Acme emails
   → Contract renewal thread, pricing discussion
4. writer-agent: Create comprehensive briefing
   → Combines all context into structured prep doc
5. file-agent: Save briefing as file
   → acme-prep-2025-01-07.md
6. email-agent: Send briefing to team
   → To: team members, attach or include prep

Validation:
- [ ] All four domains engaged
- [ ] Information coherently combined
- [ ] Briefing is actionable
- [ ] Team receives prep material
- [ ] Temporal trace complete
- [ ] Total time reasonable (<30s)
```

---

## 6. Agent Chaining Patterns

### 6.1 Sequential Chains

| Pattern | Example | Agents |
|---------|---------|--------|
| Simple 2-step | Find → Send | research → email |
| Transform | Get → Process → Store | email → writer → file |
| Enrich | Get → Lookup → Combine | calendar → research → writer |
| Workflow | Get → Decide → Act → Confirm | email → classifier → writer → email |

### 6.2 Parallel Execution

| ID | Input | Parallel Tasks | Aggregation |
|----|-------|----------------|-------------|
| PAR1 | "Find info in docs AND emails about topic X" | research ∥ email | writer combines |
| PAR2 | "Check calendar AND email for client context" | calendar ∥ email | writer merges |
| PAR3 | "Search all sources for Project Alpha" | research ∥ email ∥ calendar | orchestrator aggregates |
| PAR4 | "Send meeting prep to attendees AND save to file" | email ∥ file | Both complete |

### 6.3 Conditional Branches

| ID | Condition | Branch A | Branch B |
|----|-----------|----------|----------|
| COND1 | Doc found? | Return doc | Search email |
| COND2 | Meeting conflict? | Suggest alternatives | Confirm scheduling |
| COND3 | Urgent email? | Escalate immediately | Queue for response |
| COND4 | Answer in KB? | Auto-respond | Create ticket + escalate |
| COND5 | Calendar free? | Schedule meeting | Offer alternatives |

### 6.4 Iterative Patterns

| ID | Scenario | Loop | Exit Condition |
|----|----------|------|----------------|
| ITER1 | Process all unread emails | For-each email | All processed |
| ITER2 | Send prep to all meeting attendees | For-each attendee | All sent |
| ITER3 | Find docs for each meeting | For-each meeting | All meetings covered |
| ITER4 | Refine response until quality met | Retry | Quality > threshold |
| ITER5 | Search until answer found | While not found | Found OR max attempts |

---

## 7. MCP Integration Deep Dive

### 7.1 File System MCP

| Operation | Test | Expected |
|-----------|------|----------|
| list_directory | "List all policy docs" | Returns file list |
| read_file | "Read the return policy" | Returns file content |
| write_file | "Save meeting notes" | Creates/updates file |
| search_files | "Find docs containing 'pricing'" | Returns matching files |
| get_metadata | "When was handbook last updated?" | Returns file info |
| copy_file | "Copy template to new file" | Duplicates file |
| delete_file | "Remove draft document" | Deletes file |

### 7.2 Email MCP

| Operation | Test | Expected |
|-----------|------|----------|
| list_emails | "Show unread emails" | Returns email list |
| get_email | "Read the Acme email" | Returns email content |
| search_emails | "Find emails about contracts" | Returns matching emails |
| send_email | "Email john@example.com" | Sends email |
| reply_email | "Reply to support request" | Sends reply |
| forward_email | "Forward to legal team" | Forwards email |
| update_labels | "Mark as read" | Updates email |
| get_thread | "Show full conversation" | Returns thread |

### 7.3 Calendar MCP

| Operation | Test | Expected |
|-----------|------|----------|
| list_events | "What's on my calendar today?" | Returns events |
| get_event | "Details of Acme meeting" | Returns event info |
| create_event | "Schedule meeting at 2pm" | Creates event |
| update_event | "Move meeting to Thursday" | Updates event |
| delete_event | "Cancel the 1:1" | Removes event |
| find_free_time | "When am I free tomorrow?" | Returns slots |
| search_events | "Find all client meetings" | Returns matches |
| get_attendees | "Who's in the planning meeting?" | Returns attendee list |

### 7.4 Web Search MCP

| Operation | Test | Expected |
|-----------|------|----------|
| search | "Search for AI agent trends 2025" | Returns results |
| fetch_page | "Get content from this URL" | Returns page text |
| summarize_results | "Top 3 results about topic" | Returns summary |

---

## 8. Real-World Business Scenarios

### 8.1 Customer Support Automation

```
Scenario: "Handle all incoming support emails automatically"

Flow:
1. email-agent: Get unread support emails (label: support)
2. FOR EACH email:
   a. classifier-agent: Categorize (FAQ, Technical, Billing, Complaint)
   b. IF FAQ:
      - research-agent: Search knowledge base
      - IF answer found with high confidence:
        - writer-agent: Draft response
        - email-agent: Send response
      - ELSE:
        - Create follow-up task
   c. IF Complaint:
      - Escalate to manager
      - writer-agent: Draft acknowledgment
      - email-agent: Send acknowledgment
   d. IF Technical/Billing:
      - Forward to appropriate team

Test Cases:
- Simple FAQ → Auto-respond
- Complex question → Escalate
- Angry customer → Acknowledge + Escalate
- Duplicate question → Recognize and batch
```

### 8.2 Meeting Preparation Workflow

```
Scenario: "Prepare for all meetings tomorrow"

Flow:
1. calendar-agent: Get tomorrow's meetings
2. FOR EACH meeting:
   a. research-agent: Find relevant docs (attendees, topics)
   b. email-agent: Find related emails (last 2 weeks)
   c. writer-agent: Create prep summary
   d. file-agent: Save prep doc
3. writer-agent: Create daily briefing combining all preps
4. email-agent: Send briefing to self

Test Cases:
- Client meeting → Full client research
- Internal 1:1 → Previous meeting notes
- Team standup → Project status docs
- No meetings → Report "no meetings tomorrow"
```

### 8.3 Weekly Report Generation

```
Scenario: "Generate and send weekly team report"

Flow:
1. calendar-agent: Get this week's meetings
2. email-agent: Get this week's important emails
3. research-agent: Get recently updated docs
4. writer-agent: Create weekly summary report:
   - Meetings held + outcomes
   - Key email communications
   - Documentation updates
   - Upcoming items
5. file-agent: Save report
6. email-agent: Send to team/stakeholders

Test Cases:
- Normal week → Complete report
- No meetings → Adjust report format
- Many updates → Prioritize key items
```

### 8.4 Client Onboarding

```
Scenario: "Onboard new client: TechStart Inc"

Flow:
1. research-agent: Find onboarding templates
2. writer-agent: Customize for TechStart Inc
3. file-agent: Create client folder and docs
4. calendar-agent: Schedule kickoff meeting
5. email-agent: Send welcome email with:
   - Introduction
   - Meeting invite
   - Onboarding docs attached/linked
6. research-agent: Create client profile

Test Cases:
- Standard client → Full workflow
- Client with specific requirements → Customize
- Scheduling conflict → Offer alternatives
```

### 8.5 Email Digest and Prioritization

```
Scenario: "Summarize and prioritize my inbox"

Flow:
1. email-agent: Get all unread emails
2. classifier-agent: Categorize each:
   - Urgent / Action Required / FYI / Newsletter
3. FOR EACH category:
   - writer-agent: Create summary
4. writer-agent: Create prioritized digest:
   - Urgent: [list with summaries]
   - Action Required: [list]
   - FYI: [summaries]
   - Skip: [newsletters filtered]
5. email-agent: Send digest to self (or display)

Test Cases:
- Mixed inbox → Proper categorization
- All urgent → Flag appropriately
- Mostly newsletters → Quick processing
```

### 8.6 Document Update Workflow

```
Scenario: "Policy doc was mentioned in email thread - update doc and notify stakeholders"

Flow:
1. email-agent: Get email thread about policy
2. research-agent: Find current policy doc
3. writer-agent: Identify needed updates from email
4. file-agent: Update document
5. calendar-agent: Check if policy review meeting exists
   - IF NOT: Schedule review meeting
6. email-agent: Notify stakeholders of update

Test Cases:
- Minor update → Just update and notify
- Major change → Schedule review
- Conflicting feedback → Flag for human review
```

---

## 9. Error Handling & Recovery

### 9.1 Single Agent Failures

| ID | Failure | Expected Behavior |
|----|---------|-------------------|
| ERR1 | Email MCP unavailable | Graceful message: "Email service unavailable" |
| ERR2 | Calendar MCP timeout | Retry once, then report partial results |
| ERR3 | Document not found | Clear message: "Document X not found" |
| ERR4 | File write permission denied | Report error, suggest alternatives |
| ERR5 | Email send failed | Retry, then save as draft |

### 9.2 Chain Failures

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| ERR6 | First agent fails | Abort with clear explanation |
| ERR7 | Middle agent fails | Return partial results: "Found docs but couldn't send email" |
| ERR8 | Last agent fails | Save progress: "Created doc but email failed - saved as draft" |
| ERR9 | Parallel branch fails | Complete other branches, note failure |

### 9.3 Recovery Strategies

| Scenario | Recovery |
|----------|----------|
| MCP temporary failure | Retry with exponential backoff |
| Invalid input | Ask for clarification |
| Ambiguous request | Present options to user |
| Partial completion | Save progress, allow resume |
| Conflicting information | Flag for human decision |

### 9.4 Error Test Cases

| ID | Setup | Expected |
|----|-------|----------|
| ERRT1 | Disable email MCP, request "send email" | Graceful failure message |
| ERRT2 | File path doesn't exist | "File not found" + suggest alternatives |
| ERRT3 | Calendar event in past | "Cannot schedule in the past" |
| ERRT4 | Email to invalid address | Validation error before send |
| ERRT5 | Search returns no results | "No results found" + suggest broader search |

---

## 10. Quality Assurance Scenarios

### 10.1 Accuracy Validation

| ID | Test | Validation |
|----|------|------------|
| QA1 | Document quote accuracy | Quoted text matches source |
| QA2 | Email content accuracy | Summarized content matches original |
| QA3 | Calendar event accuracy | Times and attendees correct |
| QA4 | Cross-reference accuracy | Referenced items actually exist |

### 10.2 Hallucination Detection

| ID | Potential Hallucination | Detection Method |
|----|------------------------|------------------|
| QA5 | Claims email was sent | Verify MCP was called |
| QA6 | Cites non-existent doc | Verify doc exists |
| QA7 | References future meeting | Verify event in calendar |
| QA8 | Quotes policy not in source | Cross-check with actual doc |

### 10.3 Confidence Scoring

| Scenario | Expected Confidence |
|----------|---------------------|
| Direct doc quote | High (>0.9) |
| Doc summarization | Medium-High (0.7-0.9) |
| Cross-domain synthesis | Medium (0.5-0.7) |
| Inference/assumption | Low (<0.5) - flag |

### 10.4 Loop Detection

| ID | Scenario | Expected |
|----|----------|----------|
| LOOP1 | Agent A → B → A cycle | Detect and break |
| LOOP2 | Same search repeated | Flag after 2 repeats |
| LOOP3 | Infinite "refine" loop | Cap at N iterations |

---

## 11. Performance & Observability

### 11.1 Latency Targets

| Scenario | Target | Maximum |
|----------|--------|---------|
| Single agent, no MCP | < 2s | 5s |
| Single agent + MCP | < 4s | 10s |
| Two-agent chain | < 8s | 15s |
| Three-agent chain | < 12s | 25s |
| Complex multi-agent | < 20s | 45s |
| Parallel execution | < max(branches) + 3s | - |

### 11.2 Temporal Trace Requirements

For each test, verify:

- [ ] Workflow ID traceable
- [ ] Each agent call visible as activity
- [ ] MCP calls logged within activities
- [ ] Input/output captured per step
- [ ] Timing per step recorded
- [ ] Errors with stack traces
- [ ] Retry attempts visible
- [ ] Final status accurate

### 11.3 Metrics to Track

| Metric | Purpose |
|--------|---------|
| Agent selection accuracy | How often is right agent chosen first? |
| Chain completion rate | % of chains that complete fully |
| MCP success rate | % of MCP calls that succeed |
| Average chain length | Typical number of agents used |
| Token usage | Cost tracking |
| User intervention rate | How often does user need to clarify? |

---

## 12. User Experience Scenarios

### 12.1 Conversational Context

| ID | Initial | Follow-up | Expected |
|----|---------|-----------|----------|
| UX1 | "Find the return policy" | "Email it to John" | Knows "it" = policy |
| UX2 | "Schedule meeting with Bob" | "Add Alice too" | Updates same meeting |
| UX3 | "Draft email to client" | "Make it shorter" | Refines same email |
| UX4 | "What's on my calendar?" | "Cancel the 3pm" | Uses calendar context |

### 12.2 Clarification Requests

| Ambiguous Input | Expected Clarification |
|-----------------|----------------------|
| "Send the doc" | "Which document?" |
| "Email John" | "John Smith or John Doe?" |
| "Schedule a meeting" | "When? With whom?" |
| "Find the policy" | "Which policy? We have 5." |

### 12.3 Progress Visibility

| Scenario | User Should See |
|----------|-----------------|
| Multi-step task | Current step + progress |
| Long-running search | "Searching documents..." |
| Waiting for MCP | "Sending email..." |
| Completed step | Checkmark + brief result |

---

## 13. Edge Cases

### 13.1 Resource Limits

| ID | Edge Case | Expected |
|----|-----------|----------|
| EDGE1 | Very large document (1MB+) | Summarize or chunk |
| EDGE2 | 500 unread emails | Batch with progress |
| EDGE3 | Calendar with 50 events/day | Prioritize or filter |
| EDGE4 | Deep nested folders | Limit depth or paginate |

### 13.2 Boundary Conditions

| ID | Condition | Expected |
|----|-----------|----------|
| EDGE5 | Empty inbox | "No unread emails" |
| EDGE6 | No meetings today | "No meetings scheduled" |
| EDGE7 | No matching documents | "No documents found for X" |
| EDGE8 | All-day event | Handle correctly |
| EDGE9 | Past meeting | "Meeting already occurred" |
| EDGE10 | Future date far out | Accept or warn |

### 13.3 Input Variations

| ID | Input | Expected |
|----|-------|----------|
| EDGE11 | Empty string | Ask for input |
| EDGE12 | Very long request | Process or truncate |
| EDGE13 | Multiple requests in one | Handle sequentially or ask to clarify |
| EDGE14 | Contradictory request | Ask for clarification |
| EDGE15 | Non-standard date formats | Parse intelligently |

### 13.4 Security Boundaries

| ID | Attempt | Expected |
|----|---------|----------|
| SEC1 | Access other tenant's docs | Denied |
| SEC2 | Email to blocked domain | Blocked |
| SEC3 | Read sensitive calendar | Permission check |
| SEC4 | Bulk delete operations | Confirmation required |

---

## Test Execution Tracking

### Priority Matrix

| Priority | Scenarios | Count | Rationale |
|----------|-----------|-------|-----------|
| **P0 Critical** | D1-D10, C1-C12, E1-E14 | ~36 | Core single-domain |
| **P1 High** | All two-domain combos | ~60 | Key integrations |
| **P2 Medium** | Three-domain, full stack | ~40 | Complex flows |
| **P3 Lower** | Error, QA, edge cases | ~40 | Robustness |

### Test Result Template

```markdown
## Test: [ID]
**Date**:
**Tester**:
**Environment**:

### Input
[Exact input used]

### Expected
[Expected behavior]

### Actual
[What happened]

### Agent Chain
[Agents invoked in order]

### MCP Calls
[MCP operations performed]

### Temporal Trace
[Link or summary]

### Status
[ ] Pass / [ ] Fail / [ ] Partial

### Issues Found
[Any bugs or unexpected behavior]

### Notes
[Observations]
```

---

## Appendix: MCP Server Configurations

### File System MCP

```yaml
name: filesystem
allowed_paths:
  - /test-data/documents/
operations:
  - read_file
  - write_file
  - list_directory
  - search_files
  - get_metadata
  - copy_file
  - delete_file
```

### Email MCP

```yaml
name: email
mode: mock  # or 'live' for real testing
config:
  inbox_file: /test-data/emails/test-inbox.json
operations:
  - list_emails
  - get_email
  - search_emails
  - send_email
  - reply_email
  - forward_email
  - update_labels
  - get_thread
```

### Calendar MCP

```yaml
name: calendar
mode: mock
config:
  events_file: /test-data/calendar/test-events.json
operations:
  - list_events
  - get_event
  - create_event
  - update_event
  - delete_event
  - find_free_time
  - search_events
  - get_attendees
```

### Web Search MCP

```yaml
name: websearch
config:
  provider: google  # or bing, duckduckgo
  max_results: 10
operations:
  - search
  - fetch_page
```

---

## Summary: Test Coverage Matrix

| Domain 1 | Domain 2 | Domain 3 | Domain 4 | Scenarios |
|----------|----------|----------|----------|-----------|
| Docs | - | - | - | D1-D10 |
| Calendar | - | - | - | C1-C12 |
| Email | - | - | - | E1-E14 |
| Docs | Email | - | - | DE1-DE10 |
| Docs | Calendar | - | - | DC1-DC10 |
| Email | Calendar | - | - | EC1-EC12 |
| Docs | Writer | - | - | DW1-DW10 |
| Email | Writer | - | - | EW1-EW10 |
| Calendar | Writer | - | - | CW1-CW10 |
| Docs | Email | Calendar | - | DEC1-DEC10 |
| Docs | Email | Writer | - | DEW1-DEW10 |
| Docs | Calendar | Writer | - | DCW1-DCW10 |
| Email | Calendar | Writer | - | ECW1-ECW10 |
| Docs | Email | Calendar | Writer | DECW1-DECW10 |

**Total Unique Test Scenarios: ~180**

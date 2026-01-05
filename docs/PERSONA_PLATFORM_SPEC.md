# MagoneAI Platform UX Revamp Specification

## Persona-Centric Architecture

**Version:** 1.0
**Date:** January 2026
**Status:** Draft

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision](#2-product-vision)
3. [User Personas](#3-user-personas)
4. [Information Architecture](#4-information-architecture)
5. [User Flows](#5-user-flows)
6. [Data Models](#6-data-models)
7. [API Specification](#7-api-specification)
8. [Frontend Components](#8-frontend-components)
9. [Backend Mapping](#9-backend-mapping)
10. [Migration Strategy](#10-migration-strategy)
11. [Success Metrics](#11-success-metrics)

---

## 1. Executive Summary

### 1.1 Problem Statement

The current MagoneAI platform exposes technical primitives (agents, skills, workflows, knowledge bases) directly to users. This creates:

- **For Business Users:** Overwhelming complexity, unclear mental model
- **For Developers:** Adequate but could be more streamlined

### 1.2 Solution

Introduce a **Persona Layer** that abstracts complexity:

| Technical Concept | User-Friendly Concept |
|-------------------|----------------------|
| Agent | Team Member / Assistant |
| Skills/Tools | Capabilities ("Can send emails") |
| Knowledge Base | Documents / "Knows about" |
| Workflows | Invisible (auto-triggered) |
| LLM Config | Personality (careful ↔ creative) |
| Orchestrator | Team coordination (hidden) |

### 1.3 Key Principles

1. **Progressive Disclosure:** Simple by default, power when needed
2. **No Backend Changes:** Persona is a frontend abstraction layer
3. **Dual Interface:** "My Team" for business users, "Developer Studio" for technical users
4. **Connection-First Onboarding:** Connect tools before creating personas

---

## 2. Product Vision

### 2.1 Vision Statement

> "Build your AI team as easily as describing the help you need."

### 2.2 Goals

| Goal | Metric | Target |
|------|--------|--------|
| Reduce time to first persona | Onboarding completion time | < 5 minutes |
| Increase activation rate | Users who create first persona | > 80% |
| Reduce support tickets | Questions about agents/skills | -50% |
| Enable non-technical users | No-code persona creation rate | > 60% |

### 2.3 Non-Goals (v1)

- Changing backend APIs
- Removing Developer Studio access
- Migrating existing agents automatically
- Multi-tenant persona sharing

---

## 3. User Personas

### 3.1 Business User ("Sarah")

**Profile:**
- Operations Manager at a mid-size company
- Non-technical, comfortable with SaaS tools
- Needs AI to handle repetitive tasks

**Goals:**
- Automate email responses, scheduling, document processing
- Not interested in "how it works"
- Wants to talk to AI naturally

**Pain Points with Current UI:**
- "What's an agent type?"
- "What's an MCP?"
- "Why do I need to configure LLM temperature?"

**Success Criteria:**
- Creates first AI assistant in < 5 minutes
- Never sees technical configuration
- Can add capabilities with checkboxes

### 3.2 Power User ("Mike")

**Profile:**
- Tech-savvy business analyst
- Comfortable with no-code tools
- Wants customization without coding

**Goals:**
- Create specialized assistants for different workflows
- Upload custom documents for AI to reference
- Customize how AI responds

**Success Criteria:**
- Can create custom persona templates
- Can fine-tune personality settings
- Can connect multiple data sources

### 3.3 Developer ("Alex")

**Profile:**
- Full-stack developer
- Building custom integrations
- Needs full control over agent behavior

**Goals:**
- Create custom skills/MCPs
- Define complex workflows
- Debug and monitor agent execution

**Success Criteria:**
- Full access to current technical UI
- Can export/import configurations
- Can access APIs directly

---

## 4. Information Architecture

### 4.1 Navigation Structure

```
MagoneAI Platform
├── 🏠 Home (Dashboard)
│   ├── Quick actions
│   ├── Recent conversations
│   └── Team activity
│
├── 👥 My Team (Business Users)
│   ├── Team Members (Personas)
│   │   ├── [Persona] Chat
│   │   ├── [Persona] Settings
│   │   └── [Persona] Activity
│   ├── + Add Team Member
│   └── Templates Gallery
│
├── 🔗 Connections (Integrations)
│   ├── Connected Apps
│   ├── + Add Connection
│   └── Connection Health
│
├── 📁 Knowledge (Documents)
│   ├── Document Library
│   ├── + Upload Documents
│   └── Connected Sources
│
├── 💬 Conversations
│   ├── Active Chats
│   └── History
│
├── ⚙️ Settings
│   ├── Account
│   ├── Team Settings
│   └── Developer Studio →
│
└── 🛠️ Developer Studio (Technical Users)
    ├── Agents
    ├── Skills & MCPs
    ├── Knowledge Bases
    ├── Workflows
    ├── API Keys
    └── Logs & Monitoring
```

### 4.2 Terminology Mapping

| Developer Studio | My Team | Description |
|-----------------|---------|-------------|
| Agent | Team Member | AI entity that performs tasks |
| Skill / MCP | Capability | What the AI can do |
| Knowledge Base | Documents | What the AI knows |
| Workflow | (hidden) | How complex tasks are executed |
| LLM Config | Personality | How the AI behaves |
| Orchestrator | Team Lead | AI that coordinates others |

---

## 5. User Flows

### 5.1 Onboarding Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Welcome                                                 │
│  ─────────────────                                               │
│                                                                  │
│  "Welcome to MagoneAI! Let's build your AI team."               │
│                                                                  │
│  3 simple steps:                                                 │
│  ① Connect your tools                                           │
│  ② Create your first team member                                │
│  ③ Start delegating work                                        │
│                                                                  │
│  [Get Started →]                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Connect Tools                                           │
│  ─────────────────────                                           │
│                                                                  │
│  "What tools should your AI team have access to?"               │
│                                                                  │
│  COMMUNICATION          PRODUCTIVITY         STORAGE             │
│  ┌─────────────┐       ┌─────────────┐      ┌─────────────┐     │
│  │ 📧 Gmail    │       │ 📅 Calendar │      │ 📁 Drive    │     │
│  │ [Connect]   │       │ [Connect]   │      │ [Connect]   │     │
│  └─────────────┘       └─────────────┘      └─────────────┘     │
│  ┌─────────────┐       ┌─────────────┐      ┌─────────────┐     │
│  │ 📨 Outlook  │       │ 💬 Slack    │      │ 📝 Notion   │     │
│  │ [Connect]   │       │ [Connect]   │      │ [Connect]   │     │
│  └─────────────┘       └─────────────┘      └─────────────┘     │
│                                                                  │
│  ✅ Gmail connected                                              │
│  ✅ Google Calendar connected                                    │
│                                                                  │
│  [Skip for now]                    [Continue →]                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Choose Template                                         │
│  ───────────────────────                                         │
│                                                                  │
│  "What kind of help do you need?"                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │     👩‍💼       │  │     👨‍💼       │  │     👩‍🔬       │           │
│  │  Executive   │  │    Sales     │  │   Research   │           │
│  │  Assistant   │  │  Assistant   │  │  Assistant   │           │
│  │              │  │              │  │              │           │
│  │ Emails,      │  │ Outreach,    │  │ Analysis,    │           │
│  │ Calendar,    │  │ Follow-ups,  │  │ Reports,     │           │
│  │ Tasks        │  │ Pipeline     │  │ Summaries    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │     👨‍⚖️       │  │     👩‍💻       │  │     ✨       │           │
│  │    Legal     │  │   Support    │  │   Custom     │           │
│  │  Assistant   │  │  Assistant   │  │              │           │
│  │              │  │              │  │  Start from  │           │
│  │ Contracts,   │  │ Tickets,     │  │  scratch     │           │
│  │ Reviews      │  │ Responses    │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Customize Persona                                       │
│  ─────────────────────────                                       │
│                                                                  │
│  "Let's personalize your Executive Assistant"                   │
│                                                                  │
│  Name: [Alex_________________________]                           │
│                                                                  │
│  Avatar: 👩‍💼 👨‍💼 👩‍💻 👨‍💻 🤖 [Upload]                                │
│                                                                  │
│  ───────────────────────────────────────────────                 │
│  Capabilities (based on your connected tools):                   │
│                                                                  │
│  ✅ Available:                                                   │
│     ☑️ Read & send emails (Gmail)                               │
│     ☑️ Manage calendar (Google Calendar)                        │
│     ☐ Search & summarize documents                              │
│                                                                  │
│  🔒 Requires connection:                                         │
│     ☐ Manage tasks (Asana)        [Connect →]                   │
│     ☐ Send Slack messages         [Connect →]                   │
│                                                                  │
│  ───────────────────────────────────────────────                 │
│  Personality:                                                    │
│                                                                  │
│  Careful ●──────────○ Creative                                  │
│  Concise ○─────●────○ Detailed                                  │
│  Formal  ○───●──────○ Casual                                    │
│                                                                  │
│  [← Back]                         [Create Alex →]                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Success                                                 │
│  ───────────────                                                 │
│                                                                  │
│                    🎉                                            │
│                                                                  │
│         "Alex is ready to help!"                                │
│                                                                  │
│              ┌───────────┐                                       │
│              │    👩‍💼     │                                       │
│              │   Alex    │                                       │
│              │ Executive │                                       │
│              │ Assistant │                                       │
│              └───────────┘                                       │
│                                                                  │
│  Try asking:                                                     │
│  • "What's on my calendar today?"                               │
│  • "Draft an email to the team about the meeting"               │
│  • "Schedule lunch with Sarah next week"                        │
│                                                                  │
│  [Start Chatting →]        [Add Another Team Member]            │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Create Persona Flow (Post-Onboarding)

```
┌─────────────────────────────────────────────────────────────────┐
│  My Team                                           [+ Add Member]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                          │
│  │  👩‍💼     │  │  👨‍💻     │  │   ➕    │                          │
│  │  Alex   │  │  Sam    │  │  Add    │                          │
│  │Executive│  │ Sales   │  │  New    │                          │
│  └─────────┘  └─────────┘  └─────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Click "+ Add Member"
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Add Team Member                                          [×]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 💬 Describe what you need help with...                      ││
│  │                                                             ││
│  │ "I need someone to review legal contracts and flag          ││
│  │  any non-standard clauses"                                  ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ─── OR choose a template ───                                   │
│                                                                  │
│  [Executive] [Sales] [Legal] [Research] [Support] [Custom]      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ AI analyzes description
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Add Team Member                                          [×]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Based on your needs, I suggest:                                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  👨‍⚖️ Legal Reviewer                                         ││
│  │                                                             ││
│  │  Capabilities:                                              ││
│  │  ✅ Review & analyze documents                              ││
│  │  ✅ Compare against templates                               ││
│  │  ✅ Flag non-standard clauses                               ││
│  │  ☐ Send emails (requires Gmail)                             ││
│  │                                                             ││
│  │  Knowledge needed:                                          ││
│  │  📁 Upload your standard contract templates                 ││
│  │     [Upload Files] or [Connect Google Drive]                ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [Customize More]                     [Create Legal Reviewer →] │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Chat with Persona Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  👩‍💼 Alex - Executive Assistant                     ⚙️  •••     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 👤 You                                            10:30 AM  ││
│  │ Review this NDA and send it to john@client.com              ││
│  │ 📎 NDA_Draft_v2.pdf                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 👩‍💼 Alex                                           10:30 AM  ││
│  │                                                             ││
│  │ I've reviewed the NDA. Here's my analysis:                  ││
│  │                                                             ││
│  │ ✅ Standard clauses (matching your templates):              ││
│  │    • Confidentiality period: 3 years                        ││
│  │    • Jurisdiction: Delaware                                 ││
│  │                                                             ││
│  │ ⚠️ Non-standard clauses requiring attention:                ││
│  │    • Section 3.2: Liability cap ($50k) is below your        ││
│  │      minimum ($100k)                                        ││
│  │    • Section 5.1: Non-compete extends to 3 years            ││
│  │      (your standard is 2 years)                             ││
│  │                                                             ││
│  │ I've drafted an email to john@client.com with the NDA       ││
│  │ attached and notes about these clauses.                     ││
│  │                                                             ││
│  │ [📧 Preview Email]  [✏️ Edit Draft]  [✅ Send Now]          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Type a message...                               [Send 📤]   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [📎 Attach] [📋 Templates] [⚡ Quick Actions]                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Data Models

### 6.1 Core Models

#### 6.1.1 Persona

```python
class Persona(BaseModel):
    """
    User-friendly wrapper around Agent configuration.
    This is the ONLY new table needed.
    """
    id: str = Field(default_factory=lambda: f"persona_{uuid4().hex[:8]}")

    # ─────────────────────────────────────────────────────────────
    # User-Facing Fields
    # ─────────────────────────────────────────────────────────────
    display_name: str                    # "Alex"
    avatar: str                          # Emoji "👩‍💼" or image URL
    role: str                            # "Executive Assistant"
    tagline: Optional[str] = None        # "Handles emails & scheduling"
    description: Optional[str] = None    # Longer description

    # ─────────────────────────────────────────────────────────────
    # Capability Selection (maps to skills)
    # ─────────────────────────────────────────────────────────────
    capabilities: List[str] = []         # ["send_emails", "manage_calendar"]

    # ─────────────────────────────────────────────────────────────
    # Knowledge Sources (maps to KB collections)
    # ─────────────────────────────────────────────────────────────
    knowledge_sources: List[str] = []    # ["contracts-kb", "policies-kb"]

    # ─────────────────────────────────────────────────────────────
    # Personality Settings (maps to LLM config)
    # ─────────────────────────────────────────────────────────────
    personality: PersonalityConfig = PersonalityConfig()

    # ─────────────────────────────────────────────────────────────
    # Underlying Technical Config (hidden from business users)
    # ─────────────────────────────────────────────────────────────
    agent_id: str                        # Links to actual Agent
    template_id: Optional[str] = None    # Template used to create

    # ─────────────────────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────────────────────
    created_by: str                      # user_id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "id": "persona_abc123",
                "display_name": "Alex",
                "avatar": "👩‍💼",
                "role": "Executive Assistant",
                "tagline": "Handles emails, calendar, and document tasks",
                "capabilities": ["send_emails", "manage_calendar", "search_documents"],
                "knowledge_sources": ["company-policies"],
                "personality": {
                    "creativity": 0.3,
                    "verbosity": 0.5,
                    "formality": 0.7
                },
                "agent_id": "alex-exec-orchestrator",
                "template_id": "executive-assistant",
                "created_by": "user_123"
            }
        }


class PersonalityConfig(BaseModel):
    """
    User-friendly personality settings that map to LLM configuration.
    All values are 0.0 to 1.0 scale.
    """
    creativity: float = Field(default=0.3, ge=0.0, le=1.0)   # Maps to temperature
    verbosity: float = Field(default=0.5, ge=0.0, le=1.0)    # Maps to max_tokens
    formality: float = Field(default=0.5, ge=0.0, le=1.0)    # Affects system prompt

    def to_llm_config(self) -> dict:
        """Convert personality to LLM configuration."""
        return {
            "temperature": 0.1 + (self.creativity * 0.8),  # 0.1 to 0.9
            "max_tokens": 512 + int(self.verbosity * 1536), # 512 to 2048
        }

    def to_system_prompt_modifier(self) -> str:
        """Generate system prompt additions based on personality."""
        modifiers = []

        if self.formality > 0.7:
            modifiers.append("Use professional, formal language.")
        elif self.formality < 0.3:
            modifiers.append("Use casual, friendly language.")

        if self.verbosity > 0.7:
            modifiers.append("Provide detailed, comprehensive responses.")
        elif self.verbosity < 0.3:
            modifiers.append("Be concise and to the point.")

        return " ".join(modifiers)
```

#### 6.1.2 UserIntegration

```python
class IntegrationStatus(str, Enum):
    CONNECTED = "connected"
    EXPIRED = "expired"
    DISCONNECTED = "disconnected"
    PENDING = "pending"


class UserIntegration(BaseModel):
    """
    Tracks user's connected external services (MCPs).
    """
    id: str = Field(default_factory=lambda: f"int_{uuid4().hex[:8]}")
    user_id: str

    # ─────────────────────────────────────────────────────────────
    # Integration Identity
    # ─────────────────────────────────────────────────────────────
    provider: str                        # "google", "microsoft", "slack"
    service: str                         # "gmail", "calendar", "drive"
    mcp_id: str                          # "gmail", "google-calendar"

    # ─────────────────────────────────────────────────────────────
    # Connection Status
    # ─────────────────────────────────────────────────────────────
    status: IntegrationStatus = IntegrationStatus.PENDING
    connected_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # ─────────────────────────────────────────────────────────────
    # Credentials (reference only, actual creds in secure storage)
    # ─────────────────────────────────────────────────────────────
    credential_id: Optional[str] = None  # Reference to vault/secret manager
    scopes: List[str] = []               # OAuth scopes granted

    # ─────────────────────────────────────────────────────────────
    # Display Info
    # ─────────────────────────────────────────────────────────────
    account_email: Optional[str] = None  # "user@gmail.com"
    account_name: Optional[str] = None   # "John's Gmail"

    class Config:
        json_schema_extra = {
            "example": {
                "id": "int_xyz789",
                "user_id": "user_123",
                "provider": "google",
                "service": "gmail",
                "mcp_id": "gmail",
                "status": "connected",
                "connected_at": "2025-01-15T10:30:00Z",
                "scopes": ["gmail.send", "gmail.read"],
                "account_email": "john@company.com"
            }
        }
```

#### 6.1.3 PersonaTemplate

```python
class PersonaTemplate(BaseModel):
    """
    Pre-configured persona templates for quick creation.
    Can be system-provided or user-created.
    """
    id: str

    # ─────────────────────────────────────────────────────────────
    # Display Info
    # ─────────────────────────────────────────────────────────────
    name: str                            # "Executive Assistant"
    description: str                     # "Handles emails, scheduling..."
    avatar: str                          # "👩‍💼"
    category: str                        # "productivity", "sales", "legal"

    # ─────────────────────────────────────────────────────────────
    # Default Configuration
    # ─────────────────────────────────────────────────────────────
    default_capabilities: List[str]      # ["send_emails", "manage_calendar"]
    suggested_integrations: List[str]    # ["gmail", "google-calendar"]
    suggested_knowledge: List[str]       # ["company-policies"]
    default_personality: PersonalityConfig

    # ─────────────────────────────────────────────────────────────
    # Underlying Agent Config
    # ─────────────────────────────────────────────────────────────
    agent_type: str = "orchestrator"     # Default agent type
    agent_config_template: dict = {}     # Base agent configuration

    # ─────────────────────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────────────────────
    is_system: bool = True               # System vs user-created
    created_by: Optional[str] = None     # user_id if user-created
    usage_count: int = 0                 # Popularity tracking

    class Config:
        json_schema_extra = {
            "example": {
                "id": "executive-assistant",
                "name": "Executive Assistant",
                "description": "Handles emails, calendar management, and document tasks",
                "avatar": "👩‍💼",
                "category": "productivity",
                "default_capabilities": ["send_emails", "manage_calendar", "search_documents"],
                "suggested_integrations": ["gmail", "google-calendar", "google-drive"],
                "suggested_knowledge": ["company-policies"],
                "default_personality": {
                    "creativity": 0.3,
                    "verbosity": 0.5,
                    "formality": 0.7
                },
                "agent_type": "orchestrator",
                "is_system": True
            }
        }
```

#### 6.1.4 Capability Definition

```python
class CapabilityDefinition(BaseModel):
    """
    Maps user-friendly capabilities to technical skills.
    This is configuration data, not stored per-user.
    """
    id: str                              # "send_emails"

    # ─────────────────────────────────────────────────────────────
    # Display
    # ─────────────────────────────────────────────────────────────
    label: str                           # "Send & read emails"
    description: str                     # "Read inbox, send emails, draft messages"
    icon: str                            # "📧"
    category: str                        # "communication"

    # ─────────────────────────────────────────────────────────────
    # Requirements
    # ─────────────────────────────────────────────────────────────
    required_integrations: List[str]     # ["gmail"] or ["outlook"]
    alternative_integrations: List[List[str]] = []  # [["gmail"], ["outlook"]]

    # ─────────────────────────────────────────────────────────────
    # Technical Mapping
    # ─────────────────────────────────────────────────────────────
    skills: Dict[str, List[str]]         # {"gmail": ["gmail:send", "gmail:read"]}

    class Config:
        json_schema_extra = {
            "example": {
                "id": "send_emails",
                "label": "Send & read emails",
                "description": "Read your inbox, send emails, and draft messages",
                "icon": "📧",
                "category": "communication",
                "required_integrations": ["gmail"],
                "alternative_integrations": [["gmail"], ["outlook"]],
                "skills": {
                    "gmail": ["gmail:send", "gmail:read", "gmail:draft"],
                    "outlook": ["outlook:send", "outlook:read", "outlook:draft"]
                }
            }
        }


# ─────────────────────────────────────────────────────────────────
# Capability Registry (Configuration - loaded at startup)
# ─────────────────────────────────────────────────────────────────

CAPABILITY_REGISTRY: Dict[str, CapabilityDefinition] = {
    "send_emails": CapabilityDefinition(
        id="send_emails",
        label="Send & read emails",
        description="Read your inbox, send emails, and draft messages",
        icon="📧",
        category="communication",
        required_integrations=["gmail"],
        alternative_integrations=[["gmail"], ["outlook"]],
        skills={
            "gmail": ["gmail:send", "gmail:read", "gmail:draft"],
            "outlook": ["outlook:send", "outlook:read", "outlook:draft"]
        }
    ),
    "manage_calendar": CapabilityDefinition(
        id="manage_calendar",
        label="Manage calendar",
        description="View, create, and manage calendar events",
        icon="📅",
        category="productivity",
        required_integrations=["google-calendar"],
        alternative_integrations=[["google-calendar"], ["outlook-calendar"]],
        skills={
            "google-calendar": [
                "google-calendar:list_events",
                "google-calendar:create_event",
                "google-calendar:update_event"
            ],
            "outlook-calendar": [
                "outlook-calendar:list_events",
                "outlook-calendar:create_event"
            ]
        }
    ),
    "search_documents": CapabilityDefinition(
        id="search_documents",
        label="Search & read documents",
        description="Find and read files from your connected storage",
        icon="📁",
        category="productivity",
        required_integrations=["google-drive"],
        alternative_integrations=[["google-drive"], ["dropbox"], ["notion"]],
        skills={
            "google-drive": ["google-drive:search", "google-drive:read"],
            "dropbox": ["dropbox:search", "dropbox:read"],
            "notion": ["notion:search", "notion:read"]
        }
    ),
    "review_documents": CapabilityDefinition(
        id="review_documents",
        label="Review & analyze documents",
        description="Analyze documents, extract information, compare versions",
        icon="🔍",
        category="analysis",
        required_integrations=[],  # No external integration required
        skills={
            "_builtin": ["document-parser:extract", "document-analysis:analyze"]
        }
    ),
    "send_slack": CapabilityDefinition(
        id="send_slack",
        label="Send Slack messages",
        description="Send messages and updates to Slack channels",
        icon="💬",
        category="communication",
        required_integrations=["slack"],
        skills={
            "slack": ["slack:send_message", "slack:list_channels"]
        }
    ),
}
```

### 6.2 Database Schema

```sql
-- ─────────────────────────────────────────────────────────────────
-- NEW TABLES (minimal additions)
-- ─────────────────────────────────────────────────────────────────

-- Personas table
CREATE TABLE personas (
    id VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    avatar VARCHAR(200),
    role VARCHAR(100),
    tagline VARCHAR(200),
    description TEXT,

    capabilities JSONB DEFAULT '[]',
    knowledge_sources JSONB DEFAULT '[]',
    personality JSONB DEFAULT '{}',

    agent_id VARCHAR(50) NOT NULL REFERENCES agents(id),
    template_id VARCHAR(50),

    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT fk_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX idx_personas_created_by ON personas(created_by);
CREATE INDEX idx_personas_agent_id ON personas(agent_id);


-- User integrations table
CREATE TABLE user_integrations (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,

    provider VARCHAR(50) NOT NULL,
    service VARCHAR(50) NOT NULL,
    mcp_id VARCHAR(100) NOT NULL,

    status VARCHAR(20) DEFAULT 'pending',
    connected_at TIMESTAMP,
    expires_at TIMESTAMP,

    credential_id VARCHAR(100),
    scopes JSONB DEFAULT '[]',

    account_email VARCHAR(200),
    account_name VARCHAR(200),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, mcp_id)
);

CREATE INDEX idx_integrations_user ON user_integrations(user_id);
CREATE INDEX idx_integrations_status ON user_integrations(status);


-- Persona templates table (could also be seeded config)
CREATE TABLE persona_templates (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    avatar VARCHAR(200),
    category VARCHAR(50),

    default_capabilities JSONB DEFAULT '[]',
    suggested_integrations JSONB DEFAULT '[]',
    suggested_knowledge JSONB DEFAULT '[]',
    default_personality JSONB DEFAULT '{}',

    agent_type VARCHAR(50) DEFAULT 'orchestrator',
    agent_config_template JSONB DEFAULT '{}',

    is_system BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(50),
    usage_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_category ON persona_templates(category);
CREATE INDEX idx_templates_system ON persona_templates(is_system);
```

---

## 7. API Specification

### 7.1 Personas API

```yaml
# ─────────────────────────────────────────────────────────────────
# PERSONAS ENDPOINTS
# ─────────────────────────────────────────────────────────────────

/api/v1/personas:

  GET:
    summary: List user's personas
    parameters:
      - name: active_only
        in: query
        type: boolean
        default: true
    responses:
      200:
        schema:
          type: array
          items:
            $ref: '#/definitions/Persona'
    example_response:
      - id: "persona_abc123"
        display_name: "Alex"
        avatar: "👩‍💼"
        role: "Executive Assistant"
        tagline: "Handles emails & scheduling"
        capabilities: ["send_emails", "manage_calendar"]
        is_active: true

  POST:
    summary: Create a new persona
    description: |
      Creates a persona and underlying agent.
      Frontend should map capabilities to skills before calling.
    requestBody:
      schema:
        $ref: '#/definitions/CreatePersonaRequest'
    responses:
      201:
        schema:
          $ref: '#/definitions/Persona'
    example_request:
      display_name: "Alex"
      avatar: "👩‍💼"
      role: "Executive Assistant"
      capabilities: ["send_emails", "manage_calendar"]
      knowledge_sources: []
      personality:
        creativity: 0.3
        verbosity: 0.5
        formality: 0.7
      template_id: "executive-assistant"  # Optional


/api/v1/personas/{persona_id}:

  GET:
    summary: Get persona details
    responses:
      200:
        schema:
          $ref: '#/definitions/PersonaDetail'

  PATCH:
    summary: Update persona
    requestBody:
      schema:
        $ref: '#/definitions/UpdatePersonaRequest'
    responses:
      200:
        schema:
          $ref: '#/definitions/Persona'

  DELETE:
    summary: Delete persona and underlying agent
    responses:
      204:
        description: Deleted successfully


/api/v1/personas/{persona_id}/chat:

  POST:
    summary: Send message to persona
    description: |
      This is a convenience endpoint that routes to the underlying
      agent's execution. Equivalent to POST /agents/{agent_id}/execute
    requestBody:
      schema:
        type: object
        properties:
          message:
            type: string
          attachments:
            type: array
            items:
              type: object
              properties:
                type: string  # "file", "url"
                content: string
    responses:
      200:
        schema:
          $ref: '#/definitions/ChatResponse'
    example_request:
      message: "What's on my calendar today?"
      attachments: []
    example_response:
      persona_id: "persona_abc123"
      response: "You have 3 meetings today:\n- 9:00 AM: Team Standup\n- 2:00 PM: Client Call\n- 4:00 PM: 1:1 with Sarah"
      metadata:
        agent_id: "alex-exec-orchestrator"
        tools_used: ["google-calendar:list_events"]
        execution_time_ms: 1250
```

### 7.2 Integrations API

```yaml
# ─────────────────────────────────────────────────────────────────
# INTEGRATIONS ENDPOINTS
# ─────────────────────────────────────────────────────────────────

/api/v1/integrations:

  GET:
    summary: List user's connected integrations
    responses:
      200:
        schema:
          type: array
          items:
            $ref: '#/definitions/UserIntegration'
    example_response:
      - id: "int_xyz789"
        provider: "google"
        service: "gmail"
        mcp_id: "gmail"
        status: "connected"
        account_email: "john@company.com"
      - id: "int_abc456"
        provider: "google"
        service: "calendar"
        mcp_id: "google-calendar"
        status: "connected"


/api/v1/integrations/available:

  GET:
    summary: List all available integrations
    description: Returns integrations user CAN connect
    responses:
      200:
        schema:
          type: array
          items:
            $ref: '#/definitions/AvailableIntegration'
    example_response:
      - id: "gmail"
        provider: "google"
        name: "Gmail"
        description: "Read and send emails"
        icon: "📧"
        category: "communication"
        is_connected: true
      - id: "slack"
        provider: "slack"
        name: "Slack"
        description: "Send messages to channels"
        icon: "💬"
        category: "communication"
        is_connected: false


/api/v1/integrations/{mcp_id}/connect:

  POST:
    summary: Initiate OAuth connection
    responses:
      200:
        schema:
          type: object
          properties:
            auth_url:
              type: string
              description: Redirect user to this URL for OAuth
    example_response:
      auth_url: "https://accounts.google.com/oauth2/auth?..."


/api/v1/integrations/{mcp_id}/callback:

  GET:
    summary: OAuth callback handler
    parameters:
      - name: code
        in: query
        type: string
      - name: state
        in: query
        type: string
    responses:
      302:
        description: Redirect to app with success/failure


/api/v1/integrations/{integration_id}:

  DELETE:
    summary: Disconnect integration
    responses:
      204:
        description: Disconnected successfully
```

### 7.3 Templates API

```yaml
# ─────────────────────────────────────────────────────────────────
# TEMPLATES ENDPOINTS
# ─────────────────────────────────────────────────────────────────

/api/v1/persona-templates:

  GET:
    summary: List available persona templates
    parameters:
      - name: category
        in: query
        type: string
      - name: include_user_created
        in: query
        type: boolean
        default: true
    responses:
      200:
        schema:
          type: array
          items:
            $ref: '#/definitions/PersonaTemplate'
    example_response:
      - id: "executive-assistant"
        name: "Executive Assistant"
        description: "Handles emails, calendar, and tasks"
        avatar: "👩‍💼"
        category: "productivity"
        is_system: true
        usage_count: 1250
      - id: "legal-assistant"
        name: "Legal Assistant"
        description: "Reviews contracts and legal documents"
        avatar: "👨‍⚖️"
        category: "legal"
        is_system: true


/api/v1/persona-templates/{template_id}:

  GET:
    summary: Get template details with default config
    responses:
      200:
        schema:
          $ref: '#/definitions/PersonaTemplateDetail'


/api/v1/capabilities:

  GET:
    summary: List all available capabilities
    description: |
      Returns capabilities with availability based on
      user's connected integrations
    responses:
      200:
        schema:
          type: array
          items:
            $ref: '#/definitions/CapabilityWithStatus'
    example_response:
      - id: "send_emails"
        label: "Send & read emails"
        icon: "📧"
        category: "communication"
        is_available: true
        connected_via: "gmail"
      - id: "send_slack"
        label: "Send Slack messages"
        icon: "💬"
        category: "communication"
        is_available: false
        requires: ["slack"]
```

### 7.4 API Implementation Notes

```python
# ─────────────────────────────────────────────────────────────────
# PERSONA CREATION - Maps to existing Agent APIs
# ─────────────────────────────────────────────────────────────────

async def create_persona(request: CreatePersonaRequest, user_id: str) -> Persona:
    """
    Create a persona by:
    1. Resolving capabilities to skills
    2. Creating underlying agent
    3. Storing persona metadata
    """

    # 1. Get user's connected integrations
    integrations = await get_user_integrations(user_id)
    connected_mcps = {i.mcp_id for i in integrations if i.status == "connected"}

    # 2. Resolve capabilities to skills
    skills = []
    for cap_id in request.capabilities:
        cap = CAPABILITY_REGISTRY.get(cap_id)
        if cap:
            # Find which integration provides this capability
            for mcp_id, mcp_skills in cap.skills.items():
                if mcp_id in connected_mcps or mcp_id == "_builtin":
                    skills.extend(mcp_skills)
                    break

    # 3. Build agent configuration
    personality = request.personality or PersonalityConfig()
    llm_config = personality.to_llm_config()

    agent_config = AgentConfig(
        id=f"{slugify(request.display_name)}-{uuid4().hex[:6]}",
        name=request.display_name,
        description=request.tagline or f"{request.role} persona",
        type=AgentType.ORCHESTRATOR,  # Personas use orchestrator by default
        llm_config=LLMConfig(
            provider="openai",
            model="gpt-4o",
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
        ),
        skills=skills,
        knowledge_collection=request.knowledge_sources[0] if request.knowledge_sources else None,
        system_prompt=build_persona_system_prompt(request, personality),
        orchestrator_config=OrchestratorConfig(
            mode=OrchestratorMode.HYBRID,
            available_agents=[],  # Will be populated based on capabilities
        ),
    )

    # 4. Create agent via existing API
    agent = await agent_repository.create(agent_config)

    # 5. Store persona metadata
    persona = Persona(
        display_name=request.display_name,
        avatar=request.avatar,
        role=request.role,
        tagline=request.tagline,
        capabilities=request.capabilities,
        knowledge_sources=request.knowledge_sources,
        personality=personality,
        agent_id=agent.id,
        template_id=request.template_id,
        created_by=user_id,
    )

    await persona_repository.create(persona)

    return persona


def build_persona_system_prompt(request: CreatePersonaRequest, personality: PersonalityConfig) -> str:
    """Build system prompt for persona's agent."""

    base_prompt = f"""You are {request.display_name}, a {request.role}.

{request.description or request.tagline or "You help the user with their tasks."}

{personality.to_system_prompt_modifier()}

Always be helpful, accurate, and proactive. If you need clarification, ask.
When performing actions (sending emails, scheduling events), confirm with the user first unless they've indicated urgency.
"""

    return base_prompt
```

---

## 8. Frontend Components

### 8.1 Component Hierarchy

```
src/
├── app/
│   ├── (public)/
│   │   ├── login/
│   │   └── signup/
│   │
│   ├── (onboarding)/
│   │   ├── welcome/
│   │   ├── connect/
│   │   ├── create-persona/
│   │   └── success/
│   │
│   ├── (protected)/
│   │   ├── team/                    # "My Team" - Business Users
│   │   │   ├── page.tsx             # Team overview
│   │   │   ├── [personaId]/
│   │   │   │   ├── page.tsx         # Chat with persona
│   │   │   │   └── settings/
│   │   │   └── new/
│   │   │       └── page.tsx         # Create new persona
│   │   │
│   │   ├── connections/             # Integrations
│   │   │   ├── page.tsx
│   │   │   └── [provider]/
│   │   │       └── callback/
│   │   │
│   │   ├── knowledge/               # Documents
│   │   │   ├── page.tsx
│   │   │   └── upload/
│   │   │
│   │   ├── conversations/           # Chat history
│   │   │   └── page.tsx
│   │   │
│   │   ├── settings/
│   │   │   └── page.tsx
│   │   │
│   │   └── studio/                  # Developer Studio
│   │       ├── agents/
│   │       ├── skills/
│   │       ├── knowledge/
│   │       ├── workflows/
│   │       └── api-keys/
│   │
│   └── layout.tsx
│
├── components/
│   ├── personas/
│   │   ├── persona-card.tsx
│   │   ├── persona-avatar.tsx
│   │   ├── persona-grid.tsx
│   │   ├── persona-create-wizard.tsx
│   │   ├── persona-chat.tsx
│   │   ├── persona-settings.tsx
│   │   ├── capability-selector.tsx
│   │   ├── personality-sliders.tsx
│   │   └── template-picker.tsx
│   │
│   ├── integrations/
│   │   ├── integration-card.tsx
│   │   ├── integration-grid.tsx
│   │   ├── connect-button.tsx
│   │   └── connection-status.tsx
│   │
│   ├── knowledge/
│   │   ├── document-uploader.tsx
│   │   ├── document-list.tsx
│   │   └── source-connector.tsx
│   │
│   ├── chat/
│   │   ├── chat-interface.tsx
│   │   ├── message-bubble.tsx
│   │   ├── action-buttons.tsx
│   │   └── attachment-preview.tsx
│   │
│   ├── onboarding/
│   │   ├── onboarding-wizard.tsx
│   │   ├── step-indicator.tsx
│   │   └── welcome-screen.tsx
│   │
│   └── ui/                          # Shared UI components
│       └── ...
│
├── lib/
│   ├── api/
│   │   ├── personas.ts
│   │   ├── integrations.ts
│   │   ├── templates.ts
│   │   └── capabilities.ts
│   │
│   ├── hooks/
│   │   ├── use-personas.ts
│   │   ├── use-integrations.ts
│   │   └── use-capabilities.ts
│   │
│   └── mappings/
│       ├── capability-to-skills.ts
│       └── personality-to-llm.ts
│
└── types/
    ├── persona.ts
    ├── integration.ts
    └── template.ts
```

### 8.2 Key Components

#### 8.2.1 PersonaCard

```tsx
// components/personas/persona-card.tsx

interface PersonaCardProps {
  persona: Persona;
  onChat: () => void;
  onSettings: () => void;
}

export function PersonaCard({ persona, onChat, onSettings }: PersonaCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer">
      <CardContent className="p-6">
        {/* Avatar */}
        <div className="flex items-center gap-4 mb-4">
          <PersonaAvatar
            avatar={persona.avatar}
            name={persona.display_name}
            size="lg"
          />
          <div>
            <h3 className="font-semibold text-lg">{persona.display_name}</h3>
            <p className="text-muted-foreground text-sm">{persona.role}</p>
          </div>
        </div>

        {/* Tagline */}
        {persona.tagline && (
          <p className="text-sm text-muted-foreground mb-4">
            {persona.tagline}
          </p>
        )}

        {/* Capabilities */}
        <div className="flex flex-wrap gap-2 mb-4">
          {persona.capabilities.slice(0, 3).map(capId => {
            const cap = CAPABILITY_REGISTRY[capId];
            return (
              <Badge key={capId} variant="secondary">
                {cap?.icon} {cap?.label}
              </Badge>
            );
          })}
          {persona.capabilities.length > 3 && (
            <Badge variant="outline">+{persona.capabilities.length - 3}</Badge>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button onClick={onChat} className="flex-1">
            <MessageSquare className="w-4 h-4 mr-2" />
            Chat
          </Button>
          <Button variant="outline" onClick={onSettings}>
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### 8.2.2 CapabilitySelector

```tsx
// components/personas/capability-selector.tsx

interface CapabilitySelectorProps {
  selected: string[];
  onChange: (capabilities: string[]) => void;
  connectedIntegrations: string[];
}

export function CapabilitySelector({
  selected,
  onChange,
  connectedIntegrations
}: CapabilitySelectorProps) {
  const capabilities = useCapabilities(connectedIntegrations);

  const groupedCapabilities = groupBy(capabilities, 'category');

  return (
    <div className="space-y-6">
      {Object.entries(groupedCapabilities).map(([category, caps]) => (
        <div key={category}>
          <h4 className="font-medium mb-3 capitalize">{category}</h4>

          <div className="space-y-2">
            {caps.map(cap => (
              <CapabilityItem
                key={cap.id}
                capability={cap}
                checked={selected.includes(cap.id)}
                disabled={!cap.isAvailable}
                missingIntegration={cap.requires?.[0]}
                onChange={(checked) => {
                  if (checked) {
                    onChange([...selected, cap.id]);
                  } else {
                    onChange(selected.filter(id => id !== cap.id));
                  }
                }}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function CapabilityItem({
  capability,
  checked,
  disabled,
  missingIntegration,
  onChange
}: CapabilityItemProps) {
  return (
    <div className={cn(
      "flex items-center justify-between p-3 rounded-lg border",
      disabled ? "bg-muted opacity-60" : "hover:bg-accent"
    )}>
      <div className="flex items-center gap-3">
        <Checkbox
          checked={checked}
          disabled={disabled}
          onCheckedChange={onChange}
        />
        <span className="text-xl">{capability.icon}</span>
        <div>
          <p className="font-medium">{capability.label}</p>
          <p className="text-sm text-muted-foreground">
            {capability.description}
          </p>
        </div>
      </div>

      {disabled && missingIntegration && (
        <Button variant="outline" size="sm" asChild>
          <Link href={`/connections?connect=${missingIntegration}`}>
            Connect {missingIntegration}
          </Link>
        </Button>
      )}
    </div>
  );
}
```

#### 8.2.3 PersonalitySliders

```tsx
// components/personas/personality-sliders.tsx

interface PersonalitySlidersProps {
  value: PersonalityConfig;
  onChange: (config: PersonalityConfig) => void;
}

export function PersonalitySliders({ value, onChange }: PersonalitySlidersProps) {
  return (
    <div className="space-y-6">
      <div>
        <div className="flex justify-between mb-2">
          <span className="text-sm">Careful</span>
          <span className="text-sm">Creative</span>
        </div>
        <Slider
          value={[value.creativity * 100]}
          onValueChange={([v]) => onChange({ ...value, creativity: v / 100 })}
          max={100}
          step={10}
        />
        <p className="text-xs text-muted-foreground mt-1 text-center">
          {value.creativity < 0.3
            ? "Precise and consistent responses"
            : value.creativity > 0.7
              ? "More varied and creative responses"
              : "Balanced approach"}
        </p>
      </div>

      <div>
        <div className="flex justify-between mb-2">
          <span className="text-sm">Concise</span>
          <span className="text-sm">Detailed</span>
        </div>
        <Slider
          value={[value.verbosity * 100]}
          onValueChange={([v]) => onChange({ ...value, verbosity: v / 100 })}
          max={100}
          step={10}
        />
      </div>

      <div>
        <div className="flex justify-between mb-2">
          <span className="text-sm">Casual</span>
          <span className="text-sm">Formal</span>
        </div>
        <Slider
          value={[value.formality * 100]}
          onValueChange={([v]) => onChange({ ...value, formality: v / 100 })}
          max={100}
          step={10}
        />
      </div>
    </div>
  );
}
```

#### 8.2.4 IntegrationGrid

```tsx
// components/integrations/integration-grid.tsx

interface IntegrationGridProps {
  integrations: AvailableIntegration[];
  onConnect: (mcpId: string) => void;
  onDisconnect: (integrationId: string) => void;
}

export function IntegrationGrid({
  integrations,
  onConnect,
  onDisconnect
}: IntegrationGridProps) {
  const grouped = groupBy(integrations, 'category');

  return (
    <div className="space-y-8">
      {Object.entries(grouped).map(([category, items]) => (
        <div key={category}>
          <h3 className="font-semibold mb-4 capitalize">{category}</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map(integration => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onConnect={() => onConnect(integration.id)}
                onDisconnect={() => onDisconnect(integration.connectionId!)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function IntegrationCard({
  integration,
  onConnect,
  onDisconnect
}: IntegrationCardProps) {
  const isConnected = integration.status === 'connected';

  return (
    <Card className={cn(
      "relative",
      isConnected && "border-green-500/50"
    )}>
      {isConnected && (
        <div className="absolute top-2 right-2">
          <Badge variant="success" className="gap-1">
            <Check className="w-3 h-3" />
            Connected
          </Badge>
        </div>
      )}

      <CardContent className="p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="text-3xl">{integration.icon}</div>
          <div>
            <h4 className="font-medium">{integration.name}</h4>
            <p className="text-sm text-muted-foreground">
              {integration.description}
            </p>
          </div>
        </div>

        {isConnected ? (
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              {integration.accountEmail}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={onDisconnect}
            >
              Disconnect
            </Button>
          </div>
        ) : (
          <Button
            className="w-full"
            onClick={onConnect}
          >
            Connect
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
```

---

## 9. Backend Mapping

### 9.1 Capability to Skills Mapping

```typescript
// lib/mappings/capability-to-skills.ts

export const CAPABILITY_SKILL_MAP: Record<string, SkillMapping> = {

  // ─────────────────────────────────────────────────────────────
  // Communication
  // ─────────────────────────────────────────────────────────────

  send_emails: {
    integrations: {
      gmail: ['gmail:send', 'gmail:read', 'gmail:draft', 'gmail:search'],
      outlook: ['outlook:send', 'outlook:read', 'outlook:draft'],
    },
    fallback: null,
  },

  send_slack: {
    integrations: {
      slack: ['slack:send_message', 'slack:list_channels', 'slack:search'],
    },
    fallback: null,
  },

  // ─────────────────────────────────────────────────────────────
  // Calendar & Scheduling
  // ─────────────────────────────────────────────────────────────

  manage_calendar: {
    integrations: {
      'google-calendar': [
        'google-calendar:list_events',
        'google-calendar:create_event',
        'google-calendar:update_event',
        'google-calendar:delete_event',
        'google-calendar:check_availability',
      ],
      'outlook-calendar': [
        'outlook-calendar:list_events',
        'outlook-calendar:create_event',
      ],
    },
    fallback: null,
  },

  // ─────────────────────────────────────────────────────────────
  // Documents & Storage
  // ─────────────────────────────────────────────────────────────

  search_documents: {
    integrations: {
      'google-drive': ['google-drive:search', 'google-drive:read', 'google-drive:list'],
      dropbox: ['dropbox:search', 'dropbox:read'],
      notion: ['notion:search', 'notion:read'],
    },
    fallback: null,
  },

  create_documents: {
    integrations: {
      'google-docs': ['google-docs:create', 'google-docs:update'],
      notion: ['notion:create_page', 'notion:update_page'],
    },
    fallback: ['document-gen:generate'],  // Built-in fallback
  },

  // ─────────────────────────────────────────────────────────────
  // Analysis (no integration required)
  // ─────────────────────────────────────────────────────────────

  review_documents: {
    integrations: {},
    fallback: ['document-parser:extract', 'document-analysis:analyze'],
  },

  summarize_content: {
    integrations: {},
    fallback: ['text-analysis:summarize'],
  },

  research_web: {
    integrations: {},
    fallback: ['web-search:search', 'web-fetch:fetch'],
  },
};

export function resolveCapabilitiesToSkills(
  capabilities: string[],
  connectedIntegrations: string[]
): string[] {
  const skills: Set<string> = new Set();

  for (const capId of capabilities) {
    const mapping = CAPABILITY_SKILL_MAP[capId];
    if (!mapping) continue;

    // Check connected integrations first
    let resolved = false;
    for (const [integration, integrationSkills] of Object.entries(mapping.integrations)) {
      if (connectedIntegrations.includes(integration)) {
        integrationSkills.forEach(s => skills.add(s));
        resolved = true;
        break;  // Use first matching integration
      }
    }

    // Use fallback if no integration matched
    if (!resolved && mapping.fallback) {
      mapping.fallback.forEach(s => skills.add(s));
    }
  }

  return Array.from(skills);
}
```

### 9.2 Personality to LLM Config Mapping

```typescript
// lib/mappings/personality-to-llm.ts

export interface PersonalityConfig {
  creativity: number;  // 0-1: maps to temperature
  verbosity: number;   // 0-1: maps to max_tokens
  formality: number;   // 0-1: affects system prompt
}

export function personalityToLLMConfig(personality: PersonalityConfig): LLMConfig {
  return {
    provider: 'openai',
    model: 'gpt-4o',
    temperature: 0.1 + (personality.creativity * 0.8),  // 0.1 to 0.9
    max_tokens: 512 + Math.floor(personality.verbosity * 1536),  // 512 to 2048
  };
}

export function personalityToSystemPromptModifier(personality: PersonalityConfig): string {
  const modifiers: string[] = [];

  // Formality
  if (personality.formality > 0.7) {
    modifiers.push('Use professional, formal language. Address the user respectfully.');
  } else if (personality.formality < 0.3) {
    modifiers.push('Use casual, friendly language. Be conversational and approachable.');
  }

  // Verbosity
  if (personality.verbosity > 0.7) {
    modifiers.push('Provide detailed, comprehensive responses with examples when helpful.');
  } else if (personality.verbosity < 0.3) {
    modifiers.push('Be concise and to the point. Avoid unnecessary elaboration.');
  }

  // Creativity
  if (personality.creativity > 0.7) {
    modifiers.push('Feel free to suggest creative alternatives and think outside the box.');
  } else if (personality.creativity < 0.3) {
    modifiers.push('Stick to proven approaches and standard procedures.');
  }

  return modifiers.join(' ');
}
```

### 9.3 Template to Agent Config Mapping

```typescript
// lib/mappings/template-to-agent.ts

export const PERSONA_TEMPLATES: Record<string, PersonaTemplateConfig> = {

  'executive-assistant': {
    name: 'Executive Assistant',
    role: 'Executive Assistant',
    avatar: '👩‍💼',
    description: 'Handles emails, calendar management, and administrative tasks',

    defaultCapabilities: ['send_emails', 'manage_calendar', 'search_documents'],
    suggestedIntegrations: ['gmail', 'google-calendar', 'google-drive'],

    defaultPersonality: {
      creativity: 0.3,
      verbosity: 0.5,
      formality: 0.7,
    },

    agentConfig: {
      type: 'orchestrator',
      orchestrator_config: {
        mode: 'hybrid',
        routing_rules: {
          rules: [
            {
              pattern: '(schedule|meeting|calendar|appointment)',
              condition: 'contains',
              target_workflow: null,  // Direct skill execution
            },
            {
              pattern: '(email|send|reply|draft)',
              condition: 'contains',
              target_workflow: null,
            },
          ],
          fallback_to_llm: true,
        },
      },
    },
  },

  'legal-assistant': {
    name: 'Legal Assistant',
    role: 'Legal Assistant',
    avatar: '👨‍⚖️',
    description: 'Reviews contracts, analyzes legal documents, and ensures compliance',

    defaultCapabilities: ['review_documents', 'search_documents', 'send_emails'],
    suggestedIntegrations: ['gmail', 'google-drive'],
    suggestedKnowledge: ['contract-templates', 'legal-policies'],

    defaultPersonality: {
      creativity: 0.2,  // More careful/precise
      verbosity: 0.7,   // More detailed
      formality: 0.8,   // More formal
    },

    agentConfig: {
      type: 'orchestrator',
      orchestrator_config: {
        mode: 'hybrid',
        routing_rules: {
          rules: [
            {
              pattern: '(review|analyze).*(contract|nda|agreement)',
              condition: 'regex',
              target_workflow: 'contract-review',
            },
            {
              pattern: '(review|check).*(nda|contract).*send',
              condition: 'regex',
              target_workflow: 'contract-review-and-send',
            },
          ],
          fallback_to_llm: true,
        },
      },
    },
  },

  'sales-assistant': {
    name: 'Sales Assistant',
    role: 'Sales Assistant',
    avatar: '👨‍💼',
    description: 'Manages outreach, follow-ups, and sales pipeline activities',

    defaultCapabilities: ['send_emails', 'manage_calendar', 'research_web'],
    suggestedIntegrations: ['gmail', 'google-calendar', 'salesforce'],

    defaultPersonality: {
      creativity: 0.6,
      verbosity: 0.5,
      formality: 0.5,
    },

    agentConfig: {
      type: 'orchestrator',
      orchestrator_config: {
        mode: 'llm_driven',  // More flexible for sales conversations
      },
    },
  },
};
```

---

## 10. Migration Strategy

### 10.1 Phase 1: Add Persona Layer (Non-Breaking)

**Duration:** 2 weeks

**Changes:**
- Add `personas` table
- Add `user_integrations` table
- Add `persona_templates` table (seed with defaults)
- Implement Persona CRUD API endpoints
- Implement Integration connection endpoints

**Backward Compatibility:**
- Existing agents remain unchanged
- Developer Studio continues to work
- No migration of existing data required

### 10.2 Phase 2: Frontend Routes

**Duration:** 2 weeks

**Changes:**
- Add `/team` routes for business users
- Add `/connections` routes for integrations
- Add onboarding flow
- Keep `/studio` (Developer Studio) unchanged

**Backward Compatibility:**
- Existing users land on original dashboard
- New flag to opt-in to new experience
- Both UIs coexist

### 10.3 Phase 3: Onboarding & Templates

**Duration:** 1 week

**Changes:**
- Implement onboarding wizard
- Create persona templates library
- Add AI-assisted persona creation
- Implement capability → skill mapping

### 10.4 Phase 4: Default Experience

**Duration:** 1 week

**Changes:**
- New users get "My Team" by default
- Add "Switch to Developer Studio" option
- Track usage analytics

### 10.5 Data Migration (Optional)

For users who want to see existing agents as personas:

```python
async def migrate_agent_to_persona(agent_id: str, user_id: str) -> Persona:
    """
    Create a persona wrapper for an existing agent.
    Non-destructive - agent remains unchanged.
    """
    agent = await agent_repository.get(agent_id)

    # Infer capabilities from skills
    inferred_capabilities = infer_capabilities_from_skills(agent.skills)

    # Create persona wrapper
    persona = Persona(
        display_name=agent.name,
        avatar="🤖",  # Default, user can change
        role=infer_role_from_agent(agent),
        tagline=agent.description,
        capabilities=inferred_capabilities,
        knowledge_sources=[agent.knowledge_collection] if agent.knowledge_collection else [],
        personality=PersonalityConfig(),  # Default
        agent_id=agent.id,
        created_by=user_id,
    )

    await persona_repository.create(persona)
    return persona
```

---

## 11. Success Metrics

### 11.1 Onboarding Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Time to first persona | N/A | < 5 min | Onboarding timestamp delta |
| Onboarding completion rate | N/A | > 80% | Funnel analytics |
| Integration connection rate | N/A | > 2 per user | Average connections |
| Template usage rate | N/A | > 60% | Template vs custom |

### 11.2 Engagement Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Daily active personas | N/A | > 1.5 per user | Chat sessions |
| Messages per session | N/A | > 5 | Average conversation length |
| Capability utilization | N/A | > 70% | Used vs enabled capabilities |
| Return user rate (D7) | N/A | > 40% | Cohort analysis |

### 11.3 Satisfaction Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Support tickets (confusion) | Baseline | -50% | Ticket categorization |
| NPS score | Baseline | +20 points | Survey |
| "Too technical" feedback | Baseline | -70% | Feedback tagging |

---

## Appendix A: Seeded Templates

```json
[
  {
    "id": "executive-assistant",
    "name": "Executive Assistant",
    "avatar": "👩‍💼",
    "category": "productivity",
    "description": "Handles emails, calendar, and administrative tasks",
    "default_capabilities": ["send_emails", "manage_calendar", "search_documents"],
    "suggested_integrations": ["gmail", "google-calendar", "google-drive"],
    "is_system": true
  },
  {
    "id": "sales-assistant",
    "name": "Sales Assistant",
    "avatar": "👨‍💼",
    "category": "sales",
    "description": "Manages outreach, follow-ups, and pipeline activities",
    "default_capabilities": ["send_emails", "manage_calendar", "research_web"],
    "suggested_integrations": ["gmail", "google-calendar", "salesforce"],
    "is_system": true
  },
  {
    "id": "legal-assistant",
    "name": "Legal Assistant",
    "avatar": "👨‍⚖️",
    "category": "legal",
    "description": "Reviews contracts and ensures compliance",
    "default_capabilities": ["review_documents", "search_documents", "send_emails"],
    "suggested_integrations": ["gmail", "google-drive"],
    "is_system": true
  },
  {
    "id": "research-assistant",
    "name": "Research Assistant",
    "avatar": "👩‍🔬",
    "category": "research",
    "description": "Gathers information, analyzes data, creates reports",
    "default_capabilities": ["research_web", "summarize_content", "create_documents"],
    "suggested_integrations": ["google-drive", "notion"],
    "is_system": true
  },
  {
    "id": "support-assistant",
    "name": "Support Assistant",
    "avatar": "👩‍💻",
    "category": "support",
    "description": "Handles customer inquiries and support tickets",
    "default_capabilities": ["send_emails", "search_documents", "summarize_content"],
    "suggested_integrations": ["gmail", "zendesk", "intercom"],
    "is_system": true
  }
]
```

---

## Appendix B: Available Integrations

```json
[
  {
    "id": "gmail",
    "provider": "google",
    "name": "Gmail",
    "icon": "📧",
    "category": "communication",
    "scopes": ["gmail.send", "gmail.read", "gmail.modify"]
  },
  {
    "id": "google-calendar",
    "provider": "google",
    "name": "Google Calendar",
    "icon": "📅",
    "category": "productivity",
    "scopes": ["calendar.events", "calendar.readonly"]
  },
  {
    "id": "google-drive",
    "provider": "google",
    "name": "Google Drive",
    "icon": "📁",
    "category": "storage",
    "scopes": ["drive.readonly", "drive.file"]
  },
  {
    "id": "outlook",
    "provider": "microsoft",
    "name": "Outlook",
    "icon": "📨",
    "category": "communication",
    "scopes": ["Mail.ReadWrite", "Mail.Send"]
  },
  {
    "id": "outlook-calendar",
    "provider": "microsoft",
    "name": "Outlook Calendar",
    "icon": "📆",
    "category": "productivity",
    "scopes": ["Calendars.ReadWrite"]
  },
  {
    "id": "slack",
    "provider": "slack",
    "name": "Slack",
    "icon": "💬",
    "category": "communication",
    "scopes": ["chat:write", "channels:read"]
  },
  {
    "id": "notion",
    "provider": "notion",
    "name": "Notion",
    "icon": "📝",
    "category": "productivity",
    "scopes": ["read_content", "update_content"]
  },
  {
    "id": "salesforce",
    "provider": "salesforce",
    "name": "Salesforce",
    "icon": "☁️",
    "category": "crm",
    "scopes": ["api", "refresh_token"]
  }
]
```

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | Team | Initial specification |

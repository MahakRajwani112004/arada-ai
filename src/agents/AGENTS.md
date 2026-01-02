# Agent Architecture Documentation

## Overview

This document describes the agent system architecture, component injection flow, and how each agent type works.

## Agent Type Hierarchy

```
BaseAgent (abstract)
├── SimpleAgent      - Template/rule-based responses (no LLM)
├── LLMAgent         - Pure LLM responses
├── RAGAgent         - LLM + Knowledge Base retrieval
├── ToolAgent        - LLM + Tool calling
├── FullAgent        - LLM + Knowledge Base + Tools
├── RouterAgent      - Classifies input and routes to target agent
└── OrchestratorAgent - Coordinates multiple agents via tool calling
```

## Component Injection System

### Components Available to Agents

| Component | Description | Injection Point |
|-----------|-------------|-----------------|
| **Skills** | Domain expertise, terminology, reasoning patterns | System prompt via `build_system_prompt()` |
| **Tools** | MCP tools, custom functions | LLM `tools` parameter via native function calling |
| **Knowledge Base** | RAG retrieval from vector store | Retrieved docs added to system prompt |
| **Sub-Agents** | Child agents for orchestration | Loaded as tool definitions |

### Component Flow

```
AgentConfig
    ├── skills: List[SkillConfig]      → Loaded from DB → Injected into system prompt
    ├── tools: List[ToolConfig]        → Resolved from MCP registry → Passed to LLM
    ├── knowledge_base: KBConfig       → Vector retrieval → Added to prompt context
    └── orchestrator_config            → Child agents loaded → Available as tools
           └── available_agents        → Each gets its own skills/tools/KB
```

## Agent Types Detailed

### 1. SimpleAgent
**Purpose**: Rule-based responses without LLM calls.
**Components Used**: None (template matching only)
**Use Cases**: FAQ bots, simple routing, canned responses

```python
# No LLM, no tools, no KB, no skills
# Uses pattern matching against config.examples
```

### 2. LLMAgent
**Purpose**: Pure conversational AI using LLM.
**Components Used**:
- Skills: YES (injected into system prompt)
- Tools: NO
- KB: NO

**Use Cases**: Chat, content generation, text analysis

```python
def __init__(self, config, skills=None):
    # Skills accepted and injected via build_system_prompt()
```

### 3. RAGAgent
**Purpose**: LLM with knowledge base retrieval.
**Components Used**:
- Skills: YES
- Tools: NO
- KB: YES (retrieval before LLM call)

**Use Cases**: Document Q&A, knowledge assistants

**Execution Flow**:
1. Receive user input
2. Search knowledge base for relevant documents
3. Inject retrieved docs into system prompt
4. Call LLM with augmented context
5. Return response

### 4. ToolAgent
**Purpose**: LLM with function calling capabilities.
**Components Used**:
- Skills: YES
- Tools: YES (native function calling)
- KB: NO

**Use Cases**: Task automation, API integrations, multi-step workflows

**Execution Flow**:
1. Build messages with system prompt (includes skills)
2. Get tool definitions from registry
3. Call LLM with tools
4. If tool_calls in response, execute tools
5. Add tool results to messages
6. Loop until no more tool calls or max iterations

```python
response = await self._provider.complete(
    messages,
    tools=tool_definitions,  # Native function calling
    ...
)
```

### 5. FullAgent
**Purpose**: Most capable agent with RAG + LLM + Tools.
**Components Used**:
- Skills: YES
- Tools: YES (native function calling)
- KB: YES (retrieval before tool loop)

**Use Cases**: Complex research assistants, enterprise systems

**Execution Flow**:
1. Retrieve relevant documents from KB
2. Build messages with skills + retrieved context
3. Call LLM with tool definitions
4. Execute tools if requested
5. Loop until complete

### 6. RouterAgent
**Purpose**: Classifies input and routes to target agents.
**Components Used**:
- Skills: YES (for classification guidance)
- Tools: NO
- KB: NO
- Routing Table: YES

**Execution Flow**:
1. Build classification prompt with routing categories
2. LLM classifies user intent
3. Match to routing table entry
4. Return target agent ID (not executed, just identified)

### 7. OrchestratorAgent
**Purpose**: Coordinates multiple agents via tool calling.
**Components Used**:
- Skills: YES
- Tools: YES (regular tools + agent-as-tools)
- KB: NO (child agents may have KB)
- Available Agents: YES (loaded as tool definitions)

**Execution Flow**:
1. Load available agents as tool definitions
2. Build orchestration prompt
3. LLM decides which agents to call
4. Execute agent calls (parallel supported)
5. Aggregate results
6. Continue until LLM returns final response

## Deterministic Component Injection

### The Problem
Components must be injected consistently regardless of execution path:
- Direct execution (in-process)
- Temporal workflow execution
- Nested execution (orchestrator → child agent)

### The Solution: ComponentLoader

All component loading happens through a centralized `ComponentLoader`:

```python
class ComponentLoader:
    """Deterministic component loading for agents."""

    @staticmethod
    async def load_skills(config: AgentConfig, session) -> List[Skill]:
        """Load skills from database."""

    @staticmethod
    async def load_tools(config: AgentConfig) -> List[ToolDefinition]:
        """Load tool definitions from registry."""

    @staticmethod
    async def load_knowledge_base(config: AgentConfig) -> Optional[KnowledgeBase]:
        """Initialize knowledge base if configured."""

    @staticmethod
    async def load_child_agents(config: OrchestratorConfig, session) -> Dict[str, AgentConfig]:
        """Load child agent configs for orchestrator."""
```

### Injection Points

1. **Skills**: Always in `build_system_prompt()`
2. **Tools**: Always in LLM `complete()` call
3. **KB Context**: Always before first LLM call
4. **Child Agents**: Always during orchestrator initialization

## Validation

### AgentValidator

Validates that agent configuration matches agent type requirements:

```python
class AgentValidator:
    @staticmethod
    def validate(config: AgentConfig) -> List[str]:
        """Returns list of warnings/errors."""

        # ToolAgent without tools = warning
        # FullAgent without KB = error
        # OrchestratorAgent without available_agents = error
        # RouterAgent without routing_table = error
```

## Execution Paths

### 1. Direct Execution (Testing/Simple)
```
API → AgentFactory.create(config, skills) → agent.execute(context)
```

### 2. Temporal Workflow (Production)
```
API → Temporal Workflow → Activity → Agent execution
```

### 3. Orchestrator Child Execution
```
OrchestratorAgent → AgentFactory.create(child_config, child_skills) → child.execute()
```

## Common Patterns

### Adding a New Agent Type

1. Create class extending `BaseAgent`
2. Accept `skills` parameter in `__init__`
3. Call `super().__init__(config, skills=skills)`
4. Use `build_system_prompt()` for system message (includes skills)
5. Pass tools to LLM if tool-capable
6. Add to `AgentFactory` type mapping

### Ensuring Component Consistency

```python
# ALWAYS load components before creating agent
skills = await ComponentLoader.load_skills(config, session)
agent = AgentFactory.create(config, skills=skills)

# NEVER create agent without loading its components
# BAD: agent = AgentFactory.create(config)  # Skills missing!
```

## Files Reference

| File | Purpose |
|------|---------|
| `base.py` | BaseAgent with skills injection |
| `factory.py` | AgentFactory for creating agents |
| `component_loader.py` | Centralized component loading |
| `validator.py` | Agent config validation |
| `types/llm_agent.py` | LLMAgent implementation |
| `types/rag_agent.py` | RAGAgent implementation |
| `types/tool_agent.py` | ToolAgent implementation |
| `types/full_agent.py` | FullAgent implementation |
| `types/router_agent.py` | RouterAgent implementation |
| `types/orchestrator_agent.py` | OrchestratorAgent implementation |

## Troubleshooting

### Skills Not Working
- Check: Is `skills` parameter passed to agent?
- Check: Is `build_system_prompt()` being used?
- Check: Are skills loaded from database before agent creation?

### Tools Not Working
- Check: Is `tools` parameter passed to LLM `complete()` call?
- Check: Are tool definitions loaded from registry?
- Check: Is MCP server connected for MCP tools?

### KB Not Working
- Check: Is `knowledge_base` in agent config?
- Check: Is KB initialized before use?
- Check: Is collection populated with documents?

### Child Agents Not Working
- Check: Are child configs loaded from database?
- Check: Are child agent skills loaded?
- Check: Is `AgentFactory.create()` called with skills?

"""AI-powered workflow generation from natural language prompts."""
import json
import re
import secrets as py_secrets
from typing import Any, Dict, List, Optional

from src.api.schemas.workflows import (
    ApplyGeneratedWorkflowRequest,
    ApplyGeneratedWorkflowResponse,
    GeneratedAgentConfig,
    GenerateSkeletonRequest,
    GenerateSkeletonResponse,
    GenerateWorkflowResponse,
    MCPSuggestion,
    SkeletonStep,
    SkeletonStepWithSuggestion,
    SuggestedAgent,
    TriggerType,
    WorkflowDefinitionSchema,
    WorkflowSkeleton,
    WorkflowStepSchema,
    WorkflowTrigger,
)
from src.config.logging import get_logger
from src.llm import LLMClient, LLMMessage
from src.mcp.models import MCPServerInstance
from src.models.agent_config import AgentConfig
from src.models.enums import AgentType
from src.models.llm_config import LLMConfig
from src.models.persona import AgentGoal, AgentInstructions, AgentRole
from src.models.safety_config import SafetyConfig
from src.storage import BaseAgentRepository
from src.storage.workflow_repository import WorkflowMetadata, WorkflowRepository

logger = get_logger(__name__)

# Skeleton generation prompt (Phase 1 of two-phase creation)
GENERATE_SKELETON_PROMPT = """You are an expert AI workflow architect specializing in designing intelligent automation workflows.

## EXISTING RESOURCES (REUSE WHEN POSSIBLE)

### Available Agents:
{existing_agents_json}

### Configured MCP Servers (Integrations):
{existing_mcps_json}

**Important**: If an existing agent can fulfill a step's requirement, reference it by ID instead of suggesting a new one. This saves time and ensures consistency.

## YOUR MISSION

Analyze the user's request and design an optimal workflow skeleton that:
1. Accomplishes the user's goal efficiently
2. Uses the right step types for each task (agent, conditional, parallel)
3. Handles edge cases and errors gracefully
4. Scales well for production use

## STEP TYPES AVAILABLE

### 1. AGENT STEP (type: "agent")
Execute a single AI agent to perform a specific task.
Use for: Processing, analysis, generation, API calls, data transformation.

### 2. CONDITIONAL STEP (type: "conditional")
Route the workflow based on classification or decision-making.
Use for: Intent classification, routing to different handlers, branching logic.
Structure: A classifier agent analyzes input and routes to different branches.

### 3. PARALLEL STEP (type: "parallel")
Execute multiple agents simultaneously.
Use for: Concurrent processing, gathering data from multiple sources, fan-out operations.
Results are aggregated (all, first, merge, or best).

## OUTPUT SCHEMA

Return a JSON object with these exact fields:

{{
  "workflow_name": "Descriptive Name",
  "workflow_description": "What this workflow accomplishes",
  "trigger_type": "manual" | "webhook",
  "trigger_reason": "Why this trigger type was chosen",

  "steps": [
    {{
      "id": "step-id-with-hyphens",
      "name": "Human Readable Name",
      "type": "agent" | "conditional" | "parallel",
      "role": "What this step accomplishes (1-2 sentences)",
      "order": 0,

      // For AGENT steps - use ONE of these:
      "agent_id": "existing-agent-id",  // Use if an existing agent fits
      // OR
      "suggested_agent": {{              // Use if no existing agent fits
        "name": "Agent Name",
        "description": "What the agent does",
        "goal": "Specific objective for this step",
        "required_mcps": ["template-name"],
        "suggested_tools": ["tool_name"]
      }},

      // For CONDITIONAL steps:
      "condition_source": "Expression to evaluate (e.g., ${{steps.classifier.output}})",
      "branches": {{
        "branch-value": "target-step-id"
      }},
      "default_branch": "fallback-step-id",
      "classifier_agent": {{
        "name": "Classifier Agent",
        "goal": "Classify input into categories: category1, category2, etc.",
        "classification_categories": ["category1", "category2", "default"]
      }},

      // For PARALLEL steps:
      "parallel_branches": [
        {{
          "id": "branch-id",
          "agent_name": "Branch Agent Name",
          "goal": "What this parallel branch does"
        }}
      ],
      "aggregation": "all" | "first" | "merge" | "best"
    }}
  ],

  "existing_agents_used": ["agent-id-1", "agent-id-2"],  // IDs of reused agents
  "existing_mcps_used": ["mcp-id-1"],                    // IDs of reused MCPs

  "mcp_dependencies": [
    {{"template": "service-name", "name": "Display Name", "reason": "Why needed"}}
  ],

  "explanation": "Brief explanation of the workflow architecture and design decisions",
  "warnings": ["Any potential issues or limitations"]
}}

## DESIGN PRINCIPLES

1. **Start Simple**: Use agent steps for straightforward tasks
2. **Branch Wisely**: Use conditional steps when different inputs need different handling
3. **Parallelize When Possible**: Use parallel steps for independent operations
4. **Fail Gracefully**: Include fallback/default branches in conditionals
5. **Be Specific**: Agent goals should be clear and measurable

## TRIGGER TYPE GUIDELINES

**Use "manual" for:**
- Chat-initiated workflows (user types a message)
- On-demand tasks (user clicks "run")
- Interactive assistants

**Use "webhook" for:**
- External event triggers (email received, form submitted)
- Scheduled automation
- API callbacks from other services

## EXAMPLE 1: Simple Linear Workflow

User request: "Summarize articles and post to Slack"

{{
  "workflow_name": "Article Summary Publisher",
  "workflow_description": "Fetches articles, generates summaries, and posts to Slack",
  "trigger_type": "manual",
  "trigger_reason": "User-initiated when they want to summarize specific content",
  "steps": [
    {{
      "id": "fetch-article",
      "name": "Fetch Article",
      "type": "agent",
      "role": "Retrieve article content from the provided URL",
      "order": 0,
      "suggested_agent": {{
        "name": "Article Fetcher",
        "description": "Fetches and parses web articles",
        "goal": "Extract the main content from the article URL",
        "required_mcps": [],
        "suggested_tools": ["web_fetch"]
      }}
    }},
    {{
      "id": "generate-summary",
      "name": "Generate Summary",
      "type": "agent",
      "role": "Create a concise summary of the article content",
      "order": 1,
      "suggested_agent": {{
        "name": "Content Summarizer",
        "description": "AI-powered text summarization",
        "goal": "Generate a 2-3 sentence summary capturing key points",
        "required_mcps": [],
        "suggested_tools": []
      }}
    }},
    {{
      "id": "post-to-slack",
      "name": "Post to Slack",
      "type": "agent",
      "role": "Send the summary to the designated Slack channel",
      "order": 2,
      "suggested_agent": {{
        "name": "Slack Publisher",
        "description": "Posts messages to Slack channels",
        "goal": "Format and send the summary to #articles channel",
        "required_mcps": ["slack"],
        "suggested_tools": ["slack_send_message"]
      }}
    }}
  ],
  "mcp_dependencies": [
    {{"template": "slack", "name": "Slack", "reason": "To post summaries to channels"}}
  ],
  "explanation": "Linear workflow: fetch → summarize → post. Each step depends on the previous.",
  "warnings": []
}}

## EXAMPLE 2: Conditional Routing Workflow

User request: "Handle customer inquiries - route to different handlers based on type"

{{
  "workflow_name": "Customer Inquiry Router",
  "workflow_description": "Classifies customer inquiries and routes to specialized handlers",
  "trigger_type": "manual",
  "trigger_reason": "Triggered when customer sends a message",
  "steps": [
    {{
      "id": "classify-inquiry",
      "name": "Classify Inquiry",
      "type": "conditional",
      "role": "Analyze the inquiry and route to the appropriate handler",
      "order": 0,
      "condition_source": "${{steps.classify-inquiry.output}}",
      "branches": {{
        "billing": "handle-billing",
        "technical": "handle-technical",
        "sales": "handle-sales"
      }},
      "default_branch": "handle-general",
      "classifier_agent": {{
        "name": "Intent Classifier",
        "goal": "Classify customer inquiry into: billing, technical, sales, or general",
        "classification_categories": ["billing", "technical", "sales", "general"]
      }}
    }},
    {{
      "id": "handle-billing",
      "name": "Handle Billing",
      "type": "agent",
      "role": "Address billing-related questions and issues",
      "order": 1,
      "suggested_agent": {{
        "name": "Billing Assistant",
        "description": "Handles billing inquiries with access to payment systems",
        "goal": "Resolve billing questions: invoices, payments, refunds",
        "required_mcps": ["stripe"],
        "suggested_tools": ["stripe_get_invoice", "stripe_list_charges"]
      }}
    }},
    {{
      "id": "handle-technical",
      "name": "Handle Technical",
      "type": "agent",
      "role": "Provide technical support and troubleshooting",
      "order": 1,
      "suggested_agent": {{
        "name": "Tech Support Agent",
        "description": "Technical troubleshooting specialist",
        "goal": "Diagnose and resolve technical issues",
        "required_mcps": [],
        "suggested_tools": []
      }}
    }},
    {{
      "id": "handle-sales",
      "name": "Handle Sales",
      "type": "agent",
      "role": "Answer sales questions and provide product information",
      "order": 1,
      "suggested_agent": {{
        "name": "Sales Assistant",
        "description": "Handles sales inquiries and product questions",
        "goal": "Provide product info, pricing, and guide purchase decisions",
        "required_mcps": [],
        "suggested_tools": []
      }}
    }},
    {{
      "id": "handle-general",
      "name": "Handle General",
      "type": "agent",
      "role": "Handle general inquiries that don't fit other categories",
      "order": 1,
      "suggested_agent": {{
        "name": "General Assistant",
        "description": "Handles miscellaneous customer questions",
        "goal": "Provide helpful responses to general questions",
        "required_mcps": [],
        "suggested_tools": []
      }}
    }}
  ],
  "mcp_dependencies": [
    {{"template": "stripe", "name": "Stripe", "reason": "For billing inquiries"}}
  ],
  "explanation": "Conditional workflow with intent classification. Routes to specialized handlers based on inquiry type with general fallback.",
  "warnings": ["Ensure all handlers have appropriate fallback responses"]
}}

## EXAMPLE 3: Parallel Processing Workflow

User request: "Research a topic by checking multiple sources simultaneously"

{{
  "workflow_name": "Multi-Source Researcher",
  "workflow_description": "Researches topics by querying multiple sources in parallel",
  "trigger_type": "manual",
  "trigger_reason": "User initiates research on a specific topic",
  "steps": [
    {{
      "id": "parallel-research",
      "name": "Research Sources",
      "type": "parallel",
      "role": "Query multiple sources simultaneously for comprehensive research",
      "order": 0,
      "parallel_branches": [
        {{
          "id": "web-search",
          "agent_name": "Web Researcher",
          "goal": "Search the web for recent articles and information"
        }},
        {{
          "id": "knowledge-base",
          "agent_name": "KB Searcher",
          "goal": "Search internal knowledge base for relevant documentation"
        }},
        {{
          "id": "news-search",
          "agent_name": "News Aggregator",
          "goal": "Find recent news articles on the topic"
        }}
      ],
      "aggregation": "merge"
    }},
    {{
      "id": "synthesize-findings",
      "name": "Synthesize Findings",
      "type": "agent",
      "role": "Combine and synthesize research from all sources",
      "order": 1,
      "suggested_agent": {{
        "name": "Research Synthesizer",
        "description": "Combines information from multiple sources",
        "goal": "Create a comprehensive summary from all research sources",
        "required_mcps": [],
        "suggested_tools": []
      }}
    }}
  ],
  "mcp_dependencies": [],
  "explanation": "Parallel step gathers information from 3 sources simultaneously, then synthesizes into coherent output.",
  "warnings": ["Performance depends on slowest parallel branch"]
}}

## USER REQUEST

{user_prompt}

{context_section}

## INSTRUCTIONS

1. Analyze the user's request carefully
2. Determine the optimal workflow architecture (linear, conditional, parallel, or hybrid)
3. Design steps that are specific, measurable, and achievable
4. Include all necessary MCP dependencies
5. Add warnings for any potential issues

Respond ONLY with valid JSON. No additional text before or after."""

# AI generation prompt template
GENERATE_WORKFLOW_PROMPT = """You are an expert AI workflow architect. Design a complete, production-ready workflow system.

## EXISTING RESOURCES (PREFER REUSING THESE)

### Available Agents:
{existing_agents_json}

### Configured MCP Servers:
{existing_mcps_json}

## DESIGN PRINCIPLES

1. **Reuse First**: Always check if existing agents/MCPs can fulfill the requirement
2. **Right Tool for the Job**: Use the appropriate step type for each task
3. **Fail Gracefully**: Include error handling and default branches
4. **Be Specific**: Agent goals should be clear and measurable
5. **Keep It Simple**: Don't over-engineer; prefer fewer, well-defined steps

## STEP TYPES REFERENCE

### 1. AGENT Step (type: "agent")
Execute a single AI agent.

```json
{{
  "id": "step-id",
  "type": "agent",
  "name": "Human Readable Name",
  "agent_id": "existing-agent-id",
  "input": "${{user_input}}",
  "timeout": 120,
  "retries": 1,
  "on_error": "fail"
}}
```

If no existing agent fits, use `suggested_agent` instead of `agent_id`:
```json
{{
  "id": "step-id",
  "type": "agent",
  "name": "Process Data",
  "suggested_agent": {{
    "name": "Data Processor",
    "description": "Processes and transforms data",
    "goal": "Extract key information from input",
    "model": "gpt-4o",
    "required_mcps": [],
    "suggested_tools": []
  }},
  "input": "${{user_input}}",
  "timeout": 120,
  "retries": 0,
  "on_error": "fail"
}}
```

### 2. CONDITIONAL Step (type: "conditional")
Route workflow based on classification or conditions.

```json
{{
  "id": "route-request",
  "type": "conditional",
  "name": "Route by Intent",
  "condition_source": "${{steps.classify.output}}",
  "conditional_branches": {{
    "billing": "handle-billing",
    "technical": "handle-technical",
    "sales": "handle-sales"
  }},
  "default": "handle-general"
}}
```

### 3. PARALLEL Step (type: "parallel")
Execute multiple agents concurrently.

```json
{{
  "id": "gather-data",
  "type": "parallel",
  "name": "Gather from Multiple Sources",
  "branches": [
    {{
      "id": "web-search",
      "agent_id": "web-searcher",
      "input": "${{user_input}}",
      "timeout": 60
    }},
    {{
      "id": "db-search",
      "agent_id": "database-querier",
      "input": "${{user_input}}",
      "timeout": 60
    }}
  ],
  "aggregation": "merge"
}}
```

Aggregation options: "all" (return array), "first" (fastest), "merge" (combine), "best" (LLM picks)

## TEMPLATE VARIABLES

- `${{user_input}}` - Original user input
- `${{steps.STEP_ID.output}}` - Output from previous step
- `${{context.KEY}}` - Runtime context variables

## OUTPUT SCHEMA

```json
{{
  "workflow": {{
    "id": "workflow-id",
    "name": "Workflow Name",
    "description": "What it does",
    "steps": [...],
    "entry_step": "first-step-id"
  }},
  "agents_to_create": [
    {{
      "id": "agent-id",
      "name": "Agent Name",
      "description": "What it does",
      "agent_type": "ChatAgent|RAGAgent|ToolAgent|FullAgent|RouterAgent",
      "role": "Agent's role",
      "goal": "What it should accomplish",
      "instructions": ["Step 1", "Step 2"]
    }}
  ],
  "existing_agents_used": ["agent-id-1", "agent-id-2"],
  "mcps_suggested": [
    {{
      "template": "slack",
      "reason": "To send notifications",
      "required_for_steps": ["notify-user"]
    }}
  ],
  "existing_mcps_used": ["mcp-id-1"],
  "explanation": "Brief design explanation",
  "warnings": ["Any potential issues"],
  "estimated_complexity": "simple|moderate|complex"
}}
```

## EXAMPLE 1: Simple Linear Workflow

User: "Summarize articles and post to Slack"

```json
{{
  "workflow": {{
    "id": "article-summarizer",
    "name": "Article Summary Publisher",
    "description": "Fetches articles, summarizes them, and posts to Slack",
    "steps": [
      {{
        "id": "fetch-content",
        "type": "agent",
        "name": "Fetch Article",
        "suggested_agent": {{
          "name": "Content Fetcher",
          "description": "Retrieves web content",
          "goal": "Extract article text from URL",
          "model": "gpt-4o",
          "required_mcps": [],
          "suggested_tools": ["web_fetch"]
        }},
        "input": "${{user_input}}",
        "timeout": 60,
        "retries": 1,
        "on_error": "fail"
      }},
      {{
        "id": "summarize",
        "type": "agent",
        "name": "Generate Summary",
        "suggested_agent": {{
          "name": "Content Summarizer",
          "description": "AI-powered summarization",
          "goal": "Create concise 2-3 sentence summary",
          "model": "gpt-4o",
          "required_mcps": [],
          "suggested_tools": []
        }},
        "input": "Summarize this article:\n\n${{steps.fetch-content.output}}",
        "timeout": 120,
        "retries": 0,
        "on_error": "fail"
      }},
      {{
        "id": "post-slack",
        "type": "agent",
        "name": "Post to Slack",
        "suggested_agent": {{
          "name": "Slack Publisher",
          "description": "Posts messages to Slack",
          "goal": "Send summary to #articles channel",
          "model": "gpt-4o",
          "required_mcps": ["slack"],
          "suggested_tools": ["slack_send_message"]
        }},
        "input": "Post this summary to #articles:\n\n${{steps.summarize.output}}",
        "timeout": 30,
        "retries": 2,
        "on_error": "fail"
      }}
    ],
    "entry_step": "fetch-content"
  }},
  "agents_to_create": [],
  "existing_agents_used": [],
  "mcps_suggested": [
    {{"template": "slack", "reason": "To post summaries", "required_for_steps": ["post-slack"]}}
  ],
  "existing_mcps_used": [],
  "explanation": "Linear workflow: fetch → summarize → post. Each step builds on the previous output.",
  "warnings": [],
  "estimated_complexity": "simple"
}}
```

## EXAMPLE 2: Conditional Routing Workflow

User: "Handle customer inquiries - route to different handlers based on type"

```json
{{
  "workflow": {{
    "id": "customer-router",
    "name": "Customer Inquiry Router",
    "description": "Classifies and routes customer inquiries to specialized handlers",
    "steps": [
      {{
        "id": "classify",
        "type": "agent",
        "name": "Classify Intent",
        "suggested_agent": {{
          "name": "Intent Classifier",
          "description": "Classifies customer inquiry type",
          "goal": "Output exactly one of: billing, technical, sales, general",
          "model": "gpt-4o",
          "required_mcps": [],
          "suggested_tools": []
        }},
        "input": "Classify this customer inquiry into exactly one category (billing, technical, sales, general):\n\n${{user_input}}",
        "timeout": 30,
        "retries": 1,
        "on_error": "fail"
      }},
      {{
        "id": "route",
        "type": "conditional",
        "name": "Route to Handler",
        "condition_source": "${{steps.classify.output}}",
        "conditional_branches": {{
          "billing": "handle-billing",
          "technical": "handle-technical",
          "sales": "handle-sales"
        }},
        "default": "handle-general"
      }},
      {{
        "id": "handle-billing",
        "type": "agent",
        "name": "Handle Billing",
        "suggested_agent": {{
          "name": "Billing Assistant",
          "description": "Handles billing inquiries",
          "goal": "Resolve billing questions about invoices, payments, refunds",
          "model": "gpt-4o",
          "required_mcps": ["stripe"],
          "suggested_tools": ["stripe_get_invoice"]
        }},
        "input": "${{user_input}}",
        "timeout": 120,
        "retries": 0,
        "on_error": "fail"
      }},
      {{
        "id": "handle-technical",
        "type": "agent",
        "name": "Handle Technical",
        "suggested_agent": {{
          "name": "Tech Support",
          "description": "Technical troubleshooting specialist",
          "goal": "Diagnose and resolve technical issues",
          "model": "gpt-4o",
          "required_mcps": [],
          "suggested_tools": []
        }},
        "input": "${{user_input}}",
        "timeout": 120,
        "retries": 0,
        "on_error": "fail"
      }},
      {{
        "id": "handle-sales",
        "type": "agent",
        "name": "Handle Sales",
        "suggested_agent": {{
          "name": "Sales Assistant",
          "description": "Handles sales inquiries",
          "goal": "Provide product info and guide purchase decisions",
          "model": "gpt-4o",
          "required_mcps": [],
          "suggested_tools": []
        }},
        "input": "${{user_input}}",
        "timeout": 120,
        "retries": 0,
        "on_error": "fail"
      }},
      {{
        "id": "handle-general",
        "type": "agent",
        "name": "Handle General",
        "suggested_agent": {{
          "name": "General Assistant",
          "description": "Handles misc inquiries",
          "goal": "Provide helpful responses to general questions",
          "model": "gpt-4o",
          "required_mcps": [],
          "suggested_tools": []
        }},
        "input": "${{user_input}}",
        "timeout": 120,
        "retries": 0,
        "on_error": "fail"
      }}
    ],
    "entry_step": "classify"
  }},
  "agents_to_create": [],
  "existing_agents_used": [],
  "mcps_suggested": [
    {{"template": "stripe", "reason": "For billing account access", "required_for_steps": ["handle-billing"]}}
  ],
  "existing_mcps_used": [],
  "explanation": "Intent classification followed by conditional routing to specialized handlers. Includes general fallback.",
  "warnings": ["Ensure classifier output matches branch keys exactly"],
  "estimated_complexity": "moderate"
}}
```

## EXAMPLE 3: Parallel Processing Workflow

User: "Research topics by searching multiple sources"

```json
{{
  "workflow": {{
    "id": "multi-source-research",
    "name": "Multi-Source Researcher",
    "description": "Researches topics by querying multiple sources in parallel",
    "steps": [
      {{
        "id": "parallel-search",
        "type": "parallel",
        "name": "Search All Sources",
        "branches": [
          {{
            "id": "web-search",
            "agent_id": "web-researcher",
            "input": "Search the web for: ${{user_input}}",
            "timeout": 60
          }},
          {{
            "id": "news-search",
            "agent_id": "news-aggregator",
            "input": "Find recent news about: ${{user_input}}",
            "timeout": 60
          }},
          {{
            "id": "kb-search",
            "agent_id": "kb-searcher",
            "input": "Search knowledge base for: ${{user_input}}",
            "timeout": 60
          }}
        ],
        "aggregation": "merge"
      }},
      {{
        "id": "synthesize",
        "type": "agent",
        "name": "Synthesize Findings",
        "suggested_agent": {{
          "name": "Research Synthesizer",
          "description": "Combines research from multiple sources",
          "goal": "Create comprehensive summary from all sources",
          "model": "gpt-4o",
          "required_mcps": [],
          "suggested_tools": []
        }},
        "input": "Synthesize these research findings into a coherent summary:\n\n${{steps.parallel-search.output}}",
        "timeout": 180,
        "retries": 0,
        "on_error": "fail"
      }}
    ],
    "entry_step": "parallel-search"
  }},
  "agents_to_create": [
    {{
      "id": "web-researcher",
      "name": "Web Researcher",
      "description": "Searches the web",
      "agent_type": "ToolAgent",
      "role": "Web search specialist",
      "goal": "Find relevant web content",
      "instructions": ["Search web for query", "Extract key information", "Return structured results"]
    }},
    {{
      "id": "news-aggregator",
      "name": "News Aggregator",
      "description": "Searches news sources",
      "agent_type": "ToolAgent",
      "role": "News aggregation",
      "goal": "Find recent news articles",
      "instructions": ["Search news APIs", "Filter by relevance", "Return summaries"]
    }},
    {{
      "id": "kb-searcher",
      "name": "Knowledge Base Searcher",
      "description": "Searches internal knowledge base",
      "agent_type": "RAGAgent",
      "role": "Knowledge retrieval",
      "goal": "Find relevant internal documentation",
      "instructions": ["Query vector store", "Rank by relevance", "Return excerpts"]
    }}
  ],
  "existing_agents_used": [],
  "mcps_suggested": [],
  "existing_mcps_used": [],
  "explanation": "Parallel step searches 3 sources simultaneously, then synthesizes findings. Merge aggregation combines all results.",
  "warnings": ["Total time depends on slowest parallel branch"],
  "estimated_complexity": "moderate"
}}
```

## USER REQUEST

{user_prompt}

{context_section}

Preferred complexity: {preferred_complexity}

## INSTRUCTIONS

1. Analyze the user's request carefully
2. Check if existing agents/MCPs can be reused
3. Choose the right step types for each task
4. Include proper error handling
5. Use suggested_agent when no existing agent fits

Respond ONLY with valid JSON. No additional text before or after."""


class WorkflowGenerator:
    """Generates workflows from natural language using AI."""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize the workflow generator.

        Args:
            llm_config: Optional LLM configuration. Defaults to GPT-4o.
        """
        self.llm_config = llm_config or LLMConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4096,
        )
        self._provider = LLMClient.get_provider(self.llm_config)

    async def generate(
        self,
        prompt: str,
        user_id: str,
        context: Optional[str] = None,
        preferred_complexity: str = "auto",
        include_agents: bool = True,
        include_mcps: bool = True,
        existing_agents: Optional[List[AgentConfig]] = None,
        existing_mcps: Optional[List[MCPServerInstance]] = None,
    ) -> GenerateWorkflowResponse:
        """Generate a workflow from natural language prompt.

        Args:
            prompt: User's description of desired workflow
            context: Additional context about the use case
            preferred_complexity: Desired complexity level
            include_agents: Whether to generate agent configs if needed
            include_mcps: Whether to suggest MCP servers if needed
            existing_agents: List of existing agents to potentially reuse
            existing_mcps: List of existing MCP servers to potentially reuse

        Returns:
            GenerateWorkflowResponse with workflow definition and resources
        """
        # Format existing resources for the prompt
        agents_json = json.dumps(
            [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "type": a.agent_type.value,
                }
                for a in (existing_agents or [])
            ],
            indent=2,
        )

        mcps_json = json.dumps(
            [
                {
                    "id": m.id,
                    "name": m.name,
                    "template": m.template,
                    "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                }
                for m in (existing_mcps or [])
            ],
            indent=2,
        )

        context_section = f"Additional context: {context}" if context else ""

        # Build the full prompt
        full_prompt = GENERATE_WORKFLOW_PROMPT.format(
            existing_agents_json=agents_json if agents_json != "[]" else "No existing agents available.",
            existing_mcps_json=mcps_json if mcps_json != "[]" else "No existing MCP servers configured.",
            user_prompt=prompt,
            context_section=context_section,
            preferred_complexity=preferred_complexity,
        )

        # Call the LLM
        logger.info("workflow_generation_started", prompt_length=len(prompt))

        messages = [LLMMessage(role="user", content=full_prompt)]
        response = await self._provider.complete(messages, user_id=user_id)

        # Parse the response
        try:
            # Extract JSON from the response (handle potential markdown code blocks)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Use strict=False to allow control characters in strings
            data = json.loads(content, strict=False)
        except json.JSONDecodeError as e:
            # Try to clean up the content and retry
            try:
                # Remove common problematic characters
                cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)
                data = json.loads(cleaned, strict=False)
                logger.warning("workflow_generation_json_cleaned", original_error=str(e))
            except json.JSONDecodeError as e2:
                logger.error("workflow_generation_json_error", error=str(e2), content=response.content[:500])
                raise ValueError(f"Failed to parse AI response as JSON: {e2}")

        # Validate and convert to response schema
        try:
            workflow = self._parse_workflow(data.get("workflow", {}))
            agents_to_create = (
                [self._parse_agent_config(a) for a in data.get("agents_to_create", [])]
                if include_agents
                else []
            )
            mcps_suggested = (
                [self._parse_mcp_suggestion(m) for m in data.get("mcps_suggested", [])]
                if include_mcps
                else []
            )

            logger.info(
                "workflow_generation_completed",
                workflow_id=workflow.id,
                steps_count=len(workflow.steps),
                new_agents=len(agents_to_create),
                suggested_mcps=len(mcps_suggested),
            )

            return GenerateWorkflowResponse(
                workflow=workflow,
                agents_to_create=agents_to_create,
                existing_agents_used=data.get("existing_agents_used", []),
                mcps_suggested=mcps_suggested,
                existing_mcps_used=data.get("existing_mcps_used", []),
                explanation=data.get("explanation", "Workflow generated from prompt."),
                warnings=data.get("warnings", []),
                estimated_complexity=data.get("estimated_complexity", "moderate"),
            )
        except Exception as e:
            logger.error("workflow_generation_parse_error", error=str(e), data=str(data)[:500])
            raise ValueError(f"Failed to parse workflow data: {e}")

    async def generate_skeleton(
        self,
        request: GenerateSkeletonRequest,
        user_id: str,
        existing_agents: Optional[List[AgentConfig]] = None,
        existing_mcps: Optional[List[MCPServerInstance]] = None,
    ) -> GenerateSkeletonResponse:
        """Generate a workflow skeleton from natural language prompt.

        This is Phase 1 of the two-phase creation flow. It returns just the
        structure (steps with roles) without creating agents.

        Args:
            request: The skeleton generation request
            user_id: The user ID making the request
            existing_agents: List of existing agents to potentially reuse
            existing_mcps: List of existing MCP servers to check connectivity

        Returns:
            GenerateSkeletonResponse with skeleton structure and suggestions
        """
        # Format existing resources for the prompt
        agents_json = json.dumps(
            [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description or "",
                    "type": a.agent_type.value,
                    "goal": a.goal.objective if a.goal else "",
                }
                for a in (existing_agents or [])
            ],
            indent=2,
        )

        mcps_json = json.dumps(
            [
                {
                    "id": m.id,
                    "name": m.name,
                    "template": m.template,
                    "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                }
                for m in (existing_mcps or [])
            ],
            indent=2,
        )

        context_section = f"Additional context: {request.context}" if request.context else ""

        full_prompt = GENERATE_SKELETON_PROMPT.format(
            existing_agents_json=agents_json if agents_json != "[]" else "No existing agents available.",
            existing_mcps_json=mcps_json if mcps_json != "[]" else "No MCP servers configured yet.",
            user_prompt=request.prompt,
            context_section=context_section,
        )

        logger.info("skeleton_generation_started", prompt_length=len(request.prompt))

        messages = [LLMMessage(role="user", content=full_prompt)]
        response = await self._provider.complete(messages, user_id=user_id)

        # Parse the response
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content, strict=False)
        except json.JSONDecodeError as e:
            try:
                cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)
                data = json.loads(cleaned, strict=False)
            except json.JSONDecodeError as e2:
                logger.error("skeleton_generation_json_error", error=str(e2))
                raise ValueError(f"Failed to parse AI response as JSON: {e2}")

        # Build skeleton steps
        skeleton_steps: List[SkeletonStep] = []
        step_suggestions: List[SkeletonStepWithSuggestion] = []

        for step_data in data.get("steps", []):
            step = SkeletonStep(
                id=step_data.get("id", f"step-{len(skeleton_steps)}"),
                name=step_data.get("name", "Unnamed Step"),
                role=step_data.get("role", "No role defined"),
                order=step_data.get("order", len(skeleton_steps)),
            )
            skeleton_steps.append(step)

            # Parse agent suggestion if present
            suggestion = None
            if "suggested_agent" in step_data:
                agent_data = step_data["suggested_agent"]
                suggestion = SuggestedAgent(
                    name=agent_data.get("name", step.name),
                    goal=agent_data.get("goal", step.role),
                    required_mcps=agent_data.get("required_mcps", []),
                    suggested_tools=agent_data.get("suggested_tools", []),
                )

            step_suggestions.append(SkeletonStepWithSuggestion(
                id=step.id,
                name=step.name,
                role=step.role,
                order=step.order,
                suggestion=suggestion,
            ))

        # Build trigger configuration
        trigger_type_str = data.get("trigger_type", "manual")
        trigger_type = TriggerType.WEBHOOK if trigger_type_str == "webhook" else TriggerType.MANUAL

        # Generate webhook token if webhook trigger
        webhook_config = None
        if trigger_type == TriggerType.WEBHOOK:
            from src.api.schemas.workflows import WebhookTriggerConfig
            webhook_config = WebhookTriggerConfig(
                token=py_secrets.token_urlsafe(16),
                rate_limit=60,
                max_payload_kb=100,
            )

        trigger = WorkflowTrigger(
            type=trigger_type,
            webhook_config=webhook_config,
        )

        # Build skeleton
        skeleton = WorkflowSkeleton(
            name=data.get("workflow_name", "Untitled Workflow"),
            description=data.get("workflow_description", ""),
            trigger=trigger,
            steps=skeleton_steps,
        )

        # Check MCP connectivity
        mcp_dependencies = []
        existing_mcp_templates = {m.template for m in (existing_mcps or [])}

        for dep in data.get("mcp_dependencies", []):
            template = dep.get("template", "")
            mcp_dependencies.append({
                "template": template,
                "name": dep.get("name", template),
                "reason": dep.get("reason", ""),
                "connected": template in existing_mcp_templates,
            })

        logger.info(
            "skeleton_generation_completed",
            workflow_name=skeleton.name,
            steps_count=len(skeleton_steps),
            trigger_type=trigger_type.value,
        )

        return GenerateSkeletonResponse(
            skeleton=skeleton,
            step_suggestions=step_suggestions,
            mcp_dependencies=mcp_dependencies,
            explanation=data.get("explanation", ""),
            warnings=data.get("warnings", []),
        )

    async def apply(
        self,
        request: ApplyGeneratedWorkflowRequest,
        agent_repo: BaseAgentRepository,
        workflow_repo: WorkflowRepository,
    ) -> ApplyGeneratedWorkflowResponse:
        """Save a generated workflow and check for missing agents.

        Per the plan: This does NOT auto-create agents. Users create them separately.

        Args:
            request: The apply request with workflow definition
            agent_repo: Repository for checking existing agents
            workflow_repo: Repository for saving workflows

        Returns:
            ApplyGeneratedWorkflowResponse with missing agent info
        """
        # Save the workflow
        workflow_id = request.workflow.id
        workflow_definition = request.workflow.model_dump()

        metadata = WorkflowMetadata(
            name=request.workflow_name,
            description=request.workflow_description,
            category=request.workflow_category,
            created_by=request.created_by,
        )

        await workflow_repo.save(workflow_id, workflow_definition, metadata)
        logger.info("workflow_saved_from_generation", workflow_id=workflow_id)

        # Check for missing agents - identify blocked steps
        blocked_steps: List[str] = []
        missing_agents: List[str] = []

        for step in request.workflow.steps:
            if step.type == "agent" and step.agent_id:
                # Check if agent exists
                agent = await agent_repo.get(step.agent_id)
                if not agent:
                    blocked_steps.append(step.id)
                    if step.agent_id not in missing_agents:
                        missing_agents.append(step.agent_id)

        # Determine if workflow can execute
        can_execute = len(missing_agents) == 0
        next_action = "ready_to_run" if can_execute else "create_agents"

        logger.info(
            "workflow_apply_result",
            workflow_id=workflow_id,
            can_execute=can_execute,
            missing_agents=missing_agents,
            blocked_steps=blocked_steps,
        )

        return ApplyGeneratedWorkflowResponse(
            workflow_id=workflow_id,
            blocked_steps=blocked_steps,
            missing_agents=missing_agents,
            can_execute=can_execute,
            next_action=next_action,
        )

    def _parse_workflow(self, data: Dict[str, Any]) -> WorkflowDefinitionSchema:
        """Parse workflow data into schema."""
        steps = []
        for step_data in data.get("steps", []):
            # Parse suggested_agent if present
            suggested_agent = None
            if "suggested_agent" in step_data and step_data["suggested_agent"]:
                agent_data = step_data["suggested_agent"]
                suggested_agent = SuggestedAgent(
                    name=agent_data.get("name", ""),
                    description=agent_data.get("description"),
                    goal=agent_data.get("goal", ""),
                    model=agent_data.get("model"),
                    required_mcps=agent_data.get("required_mcps", []),
                    suggested_tools=agent_data.get("suggested_tools", []),
                )

            steps.append(
                WorkflowStepSchema(
                    id=step_data.get("id", ""),
                    type=step_data.get("type", "agent"),
                    name=step_data.get("name"),
                    agent_id=step_data.get("agent_id"),
                    suggested_agent=suggested_agent,
                    input=step_data.get("input", "${user_input}"),
                    timeout=step_data.get("timeout", 120),
                    retries=step_data.get("retries", 0),
                    on_error=step_data.get("on_error", "fail"),
                    branches=step_data.get("branches"),
                    aggregation=step_data.get("aggregation"),
                    condition_source=step_data.get("condition_source"),
                    conditional_branches=step_data.get("conditional_branches"),
                    default=step_data.get("default"),
                    max_iterations=step_data.get("max_iterations"),
                    exit_condition=step_data.get("exit_condition"),
                    steps=step_data.get("steps"),
                )
            )

        return WorkflowDefinitionSchema(
            id=data.get("id", "generated-workflow"),
            name=data.get("name"),
            description=data.get("description"),
            steps=steps,
            entry_step=data.get("entry_step"),
            context=data.get("context"),
        )

    def _parse_agent_config(self, data: Dict[str, Any]) -> GeneratedAgentConfig:
        """Parse agent config from AI response.

        Handles both simplified (string) and full (dict) formats for role/goal/instructions.
        """
        # Handle role - can be string or dict
        role = data.get("role", {})
        if isinstance(role, str):
            role = {"title": role, "expertise": []}

        # Handle goal - can be string or dict
        goal = data.get("goal", {})
        if isinstance(goal, str):
            goal = {"objective": goal}

        # Handle instructions - can be string or dict
        instructions = data.get("instructions", {})
        if isinstance(instructions, str):
            instructions = {"steps": [instructions]}
        elif isinstance(instructions, list):
            instructions = {"steps": instructions}

        return GeneratedAgentConfig(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            agent_type=data.get("agent_type", "ChatAgent"),
            role=role,
            goal=goal,
            instructions=instructions,
        )

    def _parse_mcp_suggestion(self, data: Dict[str, Any]) -> MCPSuggestion:
        """Parse MCP suggestion from AI response."""
        return MCPSuggestion(
            template=data.get("template", ""),
            reason=data.get("reason", ""),
            required_for_steps=data.get("required_for_steps", []),
        )

    def _generated_to_agent_config(
        self,
        generated: GeneratedAgentConfig,
        created_by: Optional[str] = None,
    ) -> AgentConfig:
        """Convert generated agent config to full AgentConfig."""
        # Map agent type string to enum
        agent_type_map = {
            "ChatAgent": AgentType.LLM,
            "RAGAgent": AgentType.RAG,
            "ToolAgent": AgentType.TOOL,
            "FullAgent": AgentType.FULL,
            "RouterAgent": AgentType.ROUTER,
            "OrchestratorAgent": AgentType.ORCHESTRATOR,
        }
        agent_type = agent_type_map.get(generated.agent_type, AgentType.LLM)

        # Build role from generated data
        role_data = generated.role if isinstance(generated.role, dict) else {}
        role = AgentRole(
            title=role_data.get("title", generated.name),
            expertise=role_data.get("expertise", []),
            personality_traits=role_data.get("personality_traits", []),
            communication_style=role_data.get("communication_style"),
        )

        # Build goal from generated data
        goal_data = generated.goal if isinstance(generated.goal, dict) else {}
        goal = AgentGoal(
            primary_objective=goal_data.get("primary_objective", generated.description),
            success_criteria=goal_data.get("success_criteria", []),
            constraints=goal_data.get("constraints", []),
        )

        # Build instructions from generated data
        instr_data = generated.instructions if isinstance(generated.instructions, dict) else {}
        instructions = AgentInstructions(
            steps=instr_data.get("steps", []),
            guidelines=instr_data.get("guidelines", []),
            examples=instr_data.get("examples", []),
        )

        # Create the full config with default LLM config for LLM-based agents
        llm_config = None
        if agent_type in [AgentType.LLM, AgentType.RAG, AgentType.TOOL, AgentType.FULL]:
            llm_config = LLMConfig(provider="openai", model="gpt-4o", temperature=0.7)

        return AgentConfig(
            id=generated.id,
            name=generated.name,
            description=generated.description,
            agent_type=agent_type,
            role=role,
            goal=goal,
            instructions=instructions,
            llm_config=llm_config,
            safety=SafetyConfig(),
            created_by=created_by,
        )

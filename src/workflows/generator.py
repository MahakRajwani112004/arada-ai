"""AI-powered workflow generation from natural language prompts."""
import json
import re
from typing import Any, Dict, List, Optional

from src.api.schemas.workflows import (
    ApplyGeneratedWorkflowRequest,
    ApplyGeneratedWorkflowResponse,
    GeneratedAgentConfig,
    GenerateWorkflowResponse,
    MCPSuggestion,
    WorkflowDefinitionSchema,
    WorkflowStepSchema,
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

# AI generation prompt template
GENERATE_WORKFLOW_PROMPT = """You are an AI workflow architect. Given a user's description,
design a complete workflow system.

## EXISTING RESOURCES (PREFER REUSING THESE)

### Existing Agents:
{existing_agents_json}

### Existing MCP Servers (already configured):
{existing_mcps_json}

## YOUR TASK

1. PREFER using existing agents/MCPs when they fit the requirement
2. Only suggest NEW agents if existing ones don't cover the need
3. Only suggest NEW MCPs if they're not already configured

## OUTPUT FORMAT

You must output a valid JSON object with these exact fields:

1. "workflow": A workflow definition with:
   - id: unique workflow identifier (lowercase, alphanumeric with hyphens)
   - name: descriptive name
   - description: what the workflow does
   - steps: array of workflow steps (use existing agent IDs when possible!)
   - entry_step: first step ID

2. "agents_to_create": Array of NEW agent configurations (ONLY if needed):
   - Each agent should have: id, name, description, agent_type, role, goal, instructions
   - Set to empty array [] if existing agents are sufficient
   - agent_type must be one of: ChatAgent, RAGAgent, ToolAgent, FullAgent, RouterAgent, OrchestratorAgent

3. "existing_agents_used": List of existing agent IDs used in the workflow

4. "mcps_suggested": Array of NEW MCP server suggestions (ONLY if not already configured):
   - template: MCP template name (e.g., "gmail", "slack", "notion")
   - reason: why this MCP is needed
   - required_for_steps: list of step IDs that need this MCP
   - Set to empty array [] if existing MCPs are sufficient

5. "existing_mcps_used": List of existing MCP IDs used in the workflow

6. "explanation": Brief explanation of the workflow design, mentioning which
   existing resources are being reused

7. "warnings": Array of potential issues or suggestions (can be empty)

8. "estimated_complexity": One of "simple", "moderate", "complex"

## STEP TYPES

Step types available:
- "agent": Execute an agent (existing or new)
  Required fields: id, type, agent_id, input
- "parallel": Execute multiple branches concurrently
  Required fields: id, type, branches (array of step arrays), aggregation (all/first/merge)
- "conditional": Route based on conditions
  Required fields: id, type, condition_source, conditional_branches (map of condition to step_id), default
- "loop": Iterate until condition met
  Required fields: id, type, steps (array), max_iterations, exit_condition

## TEMPLATE VARIABLES

Use these placeholders in step inputs:
- ${{user_input}}: The original user input
- ${{steps.STEP_ID.output}}: Output from a previous step
- ${{context.KEY}}: Context variables passed at runtime

## EXAMPLE OUTPUT

{{
  "workflow": {{
    "id": "customer-support-flow",
    "name": "Customer Support Workflow",
    "description": "Handles customer inquiries with classification and routing",
    "steps": [
      {{
        "id": "classify",
        "type": "agent",
        "agent_id": "customer-classifier",
        "input": "${{user_input}}",
        "timeout": 120,
        "retries": 1,
        "on_error": "fail"
      }},
      {{
        "id": "respond",
        "type": "agent",
        "agent_id": "response-generator",
        "input": "Classification: ${{steps.classify.output}}\nOriginal query: ${{user_input}}",
        "timeout": 120,
        "retries": 0,
        "on_error": "fail"
      }}
    ],
    "entry_step": "classify"
  }},
  "agents_to_create": [],
  "existing_agents_used": ["customer-classifier", "response-generator"],
  "mcps_suggested": [],
  "existing_mcps_used": [],
  "explanation": "This workflow uses existing agents to classify and respond to customer inquiries.",
  "warnings": [],
  "estimated_complexity": "simple"
}}

## USER REQUEST

{user_prompt}

{context_section}

Preferred complexity: {preferred_complexity}

Respond ONLY with valid JSON. No additional text before or after the JSON."""


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
        response = await self._provider.complete(messages)

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
            steps.append(
                WorkflowStepSchema(
                    id=step_data.get("id", ""),
                    type=step_data.get("type", "agent"),
                    agent_id=step_data.get("agent_id"),
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

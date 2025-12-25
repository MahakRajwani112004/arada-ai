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
GENERATE_SKELETON_PROMPT = """You are an AI workflow architect. Given a user's description,
design a workflow SKELETON - just the structure and step roles, without creating agents.

## YOUR TASK

Design the workflow structure:
1. Identify the steps needed to accomplish the user's goal
2. Give each step a clear name and role description
3. Suggest the best trigger type (manual or webhook)
4. Identify what tools/MCPs each step might need

## OUTPUT FORMAT

Return a JSON object with these exact fields:

1. "workflow_name": A descriptive name for the workflow
2. "workflow_description": What the workflow accomplishes
3. "trigger_type": "manual" or "webhook" based on the use case
4. "trigger_reason": Why this trigger type was chosen

5. "steps": Array of workflow steps, each with:
   - "id": Lowercase identifier with hyphens (e.g., "classify-email")
   - "name": Human-readable name (e.g., "Classify Email")
   - "role": What this step should do (1-2 sentences)
   - "order": Step sequence number (0, 1, 2, ...)
   - "suggested_agent": {{
       "name": Suggested agent name,
       "goal": What the agent should accomplish,
       "required_mcps": Array of MCP templates needed (e.g., ["gmail", "slack"]),
       "suggested_tools": Array of tool names (e.g., ["gmail_send_message"])
     }}

6. "mcp_dependencies": Array of {{
     "template": MCP template name,
     "name": Display name,
     "reason": Why needed
   }}

7. "explanation": Brief explanation of the workflow design
8. "warnings": Array of potential issues (can be empty)

## TRIGGER TYPE GUIDELINES

- Use "manual" for:
  - Chat-initiated workflows
  - User-driven actions
  - One-off tasks

- Use "webhook" for:
  - External event triggers (email received, form submitted)
  - Scheduled automation
  - Integration callbacks

## EXAMPLE OUTPUT

{{
  "workflow_name": "Email Urgency Handler",
  "workflow_description": "Monitors emails, classifies urgency, and notifies for urgent ones",
  "trigger_type": "webhook",
  "trigger_reason": "Triggered by incoming email notifications",
  "steps": [
    {{
      "id": "fetch-email",
      "name": "Fetch Email",
      "role": "Retrieve the full email content from the incoming webhook data",
      "order": 0,
      "suggested_agent": {{
        "name": "Email Fetcher",
        "goal": "Extract and parse email content from webhook payload",
        "required_mcps": ["gmail"],
        "suggested_tools": ["gmail_get_message"]
      }}
    }},
    {{
      "id": "classify-urgency",
      "name": "Classify Urgency",
      "role": "Analyze the email content and determine its urgency level",
      "order": 1,
      "suggested_agent": {{
        "name": "Urgency Classifier",
        "goal": "Classify email urgency as high, medium, or low",
        "required_mcps": [],
        "suggested_tools": []
      }}
    }},
    {{
      "id": "send-notification",
      "name": "Send Notification",
      "role": "Notify the user about urgent emails via Slack",
      "order": 2,
      "suggested_agent": {{
        "name": "Slack Notifier",
        "goal": "Send formatted notifications to Slack for urgent emails",
        "required_mcps": ["slack"],
        "suggested_tools": ["slack_send_message"]
      }}
    }}
  ],
  "mcp_dependencies": [
    {{"template": "gmail", "name": "Gmail", "reason": "To fetch email content"}},
    {{"template": "slack", "name": "Slack", "reason": "To send notifications"}}
  ],
  "explanation": "This workflow uses a webhook trigger to receive email notifications, then processes each email through classification and notification steps.",
  "warnings": []
}}

## USER REQUEST

{user_prompt}

{context_section}

Respond ONLY with valid JSON. No additional text."""

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
        existing_mcps: Optional[List[MCPServerInstance]] = None,
    ) -> GenerateSkeletonResponse:
        """Generate a workflow skeleton from natural language prompt.

        This is Phase 1 of the two-phase creation flow. It returns just the
        structure (steps with roles) without creating agents.

        Args:
            request: The skeleton generation request
            existing_mcps: List of existing MCP servers to check connectivity

        Returns:
            GenerateSkeletonResponse with skeleton structure and suggestions
        """
        context_section = f"Additional context: {request.context}" if request.context else ""

        full_prompt = GENERATE_SKELETON_PROMPT.format(
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

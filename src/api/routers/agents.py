"""Agent API routes."""
import json
import re

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.schemas.agent import (
    AgentExampleSchema,
    AgentGoalSchema,
    AgentInstructionsSchema,
    AgentListResponse,
    AgentResponse,
    AgentRoleSchema,
    CreateAgentRequest,
    GenerateAgentRequest,
    GenerateAgentResponse,
)
from src.models.agent_config import AgentConfig
from src.models.enums import AgentType
from src.models.knowledge_config import KnowledgeBaseConfig
from src.models.llm_config import LLMConfig
from src.models.orchestrator_config import AgentReference, OrchestratorConfig, OrchestratorMode, AggregationStrategy
from src.models.persona import AgentExample, AgentGoal, AgentInstructions, AgentRole
from src.models.safety_config import GovernanceConfig, SafetyConfig
from src.models.tool_config import ToolConfig
from src.api.dependencies import get_repository
from src.storage import BaseAgentRepository
from src.llm.client import LLMClient, LLMMessage

router = APIRouter(prefix="/agents", tags=["agents"])

# Prompt for AI agent generation
GENERATE_AGENT_PROMPT = """You are an AI assistant that helps create agent configurations.
Given an agent name and optional context, generate a complete agent configuration.

Respond with a JSON object containing:
{
  "description": "A clear description of what this agent does",
  "role": {
    "title": "The agent's role title",
    "expertise": ["area1", "area2", "area3"],
    "personality": ["trait1", "trait2", "trait3"],
    "communication_style": "How the agent communicates"
  },
  "goal": {
    "objective": "The main objective of this agent",
    "success_criteria": ["criterion1", "criterion2"],
    "constraints": []
  },
  "instructions": {
    "steps": ["step1", "step2", "step3", "step4"],
    "rules": ["rule1", "rule2"],
    "prohibited": [],
    "output_format": "How the agent should format its responses"
  },
  "examples": [
    {"input": "Example user input", "output": "Example agent response"}
  ],
  "suggested_agent_type": "ToolAgent"
}

For suggested_agent_type, choose ONLY from these exact values:
- LLMAgent: For simple conversational agents (chat, Q&A)
- ToolAgent: For agents that use external tools/APIs (most common)
- RAGAgent: For agents that need to search knowledge bases
- FullAgent: For complex agents needing both tools and knowledge bases
- OrchestratorAgent: For agents that coordinate multiple sub-agents

Respond ONLY with the JSON object, no additional text."""

# Mapping for invalid/legacy agent type names to valid ones
AGENT_TYPE_ALIASES = {
    "ChatAgent": "LLMAgent",
    "WorkflowAgent": "FullAgent",
    "SimpleAgent": "LLMAgent",
}


def _parse_agent_type(value: str) -> AgentType:
    """Parse agent type string with fallback for invalid values."""
    # Check if it's an alias
    if value in AGENT_TYPE_ALIASES:
        value = AGENT_TYPE_ALIASES[value]

    # Try to parse as AgentType
    try:
        return AgentType(value)
    except ValueError:
        # Default to ToolAgent if invalid
        return AgentType.TOOL


@router.post("/generate", response_model=GenerateAgentResponse)
async def generate_agent_config(request: GenerateAgentRequest) -> GenerateAgentResponse:
    """Generate agent configuration using AI."""
    try:
        # Use OpenAI for generation (faster, cheaper for this use case)
        llm_config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1024,
        )
        provider = LLMClient.get_provider(llm_config)

        # Build user message
        user_content = f"Create an agent configuration for: {request.name}"
        if request.context:
            user_content += f"\n\nAdditional context: {request.context}"

        messages = [
            LLMMessage(role="system", content=GENERATE_AGENT_PROMPT),
            LLMMessage(role="user", content=user_content),
        ]

        response = await provider.complete(messages)

        # Parse JSON from response
        content = response.content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)

        data = json.loads(content)

        return GenerateAgentResponse(
            description=data.get("description", f"An AI agent for {request.name}"),
            role=AgentRoleSchema(
                title=data.get("role", {}).get("title", "AI Assistant"),
                expertise=data.get("role", {}).get("expertise", []),
                personality=data.get("role", {}).get("personality", ["helpful", "professional"]),
                communication_style=data.get("role", {}).get("communication_style", "clear and concise"),
            ),
            goal=AgentGoalSchema(
                objective=data.get("goal", {}).get("objective", f"Help users with {request.name}"),
                success_criteria=data.get("goal", {}).get("success_criteria", []),
                constraints=data.get("goal", {}).get("constraints", []),
            ),
            instructions=AgentInstructionsSchema(
                steps=data.get("instructions", {}).get("steps", []),
                rules=data.get("instructions", {}).get("rules", []),
                prohibited=data.get("instructions", {}).get("prohibited", []),
                output_format=data.get("instructions", {}).get("output_format"),
            ),
            examples=[
                AgentExampleSchema(input=ex.get("input", ""), output=ex.get("output", ""))
                for ex in data.get("examples", [])
            ],
            suggested_agent_type=_parse_agent_type(data.get("suggested_agent_type", "ToolAgent")),
        )

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse AI response: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate agent config: {str(e)}",
        )


def _to_agent_config(request: CreateAgentRequest) -> AgentConfig:
    """Convert API request to AgentConfig."""
    llm_config = None
    if request.llm_config:
        llm_config = LLMConfig(
            provider=request.llm_config.provider,
            model=request.llm_config.model,
            temperature=request.llm_config.temperature,
            max_tokens=request.llm_config.max_tokens,
        )

    kb_config = None
    if request.knowledge_base:
        kb_config = KnowledgeBaseConfig(
            collection_name=request.knowledge_base.collection_name,
            embedding_model=request.knowledge_base.embedding_model,
            top_k=request.knowledge_base.top_k,
            similarity_threshold=request.knowledge_base.similarity_threshold,
        )

    orchestrator_config = None
    if request.orchestrator_config:
        orchestrator_config = OrchestratorConfig(
            mode=OrchestratorMode(request.orchestrator_config.mode),
            available_agents=[
                AgentReference(
                    agent_id=a.agent_id,
                    alias=a.alias,
                    description=a.description,
                )
                for a in request.orchestrator_config.available_agents
            ],
            workflow_definition=request.orchestrator_config.workflow_definition,
            default_aggregation=AggregationStrategy(request.orchestrator_config.default_aggregation),
            max_parallel=request.orchestrator_config.max_parallel,
            max_depth=request.orchestrator_config.max_depth,
            allow_self_reference=request.orchestrator_config.allow_self_reference,
        )

    return AgentConfig(
        id=request.id,
        name=request.name,
        description=request.description,
        agent_type=request.agent_type,
        role=AgentRole(
            title=request.role.title,
            expertise=request.role.expertise,
            personality=request.role.personality,
            communication_style=request.role.communication_style,
        ),
        goal=AgentGoal(
            objective=request.goal.objective,
            success_criteria=request.goal.success_criteria,
            constraints=request.goal.constraints,
        ),
        instructions=AgentInstructions(
            steps=request.instructions.steps,
            rules=request.instructions.rules,
            prohibited=request.instructions.prohibited,
            output_format=request.instructions.output_format,
        ),
        examples=[
            AgentExample(input=e.input, output=e.output)
            for e in request.examples
        ],
        llm_config=llm_config,
        knowledge_base=kb_config,
        tools=[
            ToolConfig(
                tool_id=t.tool_id,
                enabled=t.enabled,
                requires_confirmation=t.requires_confirmation,
            )
            for t in request.tools
        ],
        routing_table=request.routing_table,
        orchestrator_config=orchestrator_config,
        safety=SafetyConfig(
            level=request.safety.level,
            blocked_topics=request.safety.blocked_topics,
            blocked_patterns=request.safety.blocked_patterns,
        ),
        governance=GovernanceConfig(),
    )


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: CreateAgentRequest,
    repository: BaseAgentRepository = Depends(get_repository),
) -> AgentResponse:
    """Create a new agent."""
    if await repository.exists(request.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with ID '{request.id}' already exists",
        )

    config = _to_agent_config(request)
    await repository.save(config)

    return AgentResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        agent_type=config.agent_type,
    )


@router.get("", response_model=AgentListResponse)
async def list_agents(
    repository: BaseAgentRepository = Depends(get_repository),
) -> AgentListResponse:
    """List all agents."""
    agents = await repository.list()
    return AgentListResponse(
        agents=[
            AgentResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                agent_type=a.agent_type,
            )
            for a in agents
        ],
        total=len(agents),
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    repository: BaseAgentRepository = Depends(get_repository),
) -> AgentResponse:
    """Get agent by ID."""
    config = await repository.get(agent_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    return AgentResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        agent_type=config.agent_type,
    )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    repository: BaseAgentRepository = Depends(get_repository),
) -> None:
    """Delete agent by ID."""
    if not await repository.delete(agent_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

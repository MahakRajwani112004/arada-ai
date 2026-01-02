"""Agent Factory - creates agents from configuration with component validation."""
from typing import Dict, List, Optional, Type

from src.agents.base import BaseAgent
from src.agents.component_loader import ComponentValidator
from src.agents.types.full_agent import FullAgent
from src.agents.types.llm_agent import LLMAgent
from src.agents.types.orchestrator_agent import OrchestratorAgent
from src.agents.types.rag_agent import RAGAgent
from src.agents.types.router_agent import RouterAgent
from src.agents.types.simple_agent import SimpleAgent
from src.agents.types.tool_agent import ToolAgent
from src.config.logging import get_logger
from src.models.agent_config import AgentConfig
from src.models.enums import AgentType
from src.skills.models import Skill

logger = get_logger(__name__)


class AgentFactory:
    """
    Factory for creating agent instances from configuration.

    This factory:
    1. Validates agent configuration matches type requirements
    2. Logs warnings for suboptimal configurations
    3. Creates agent with skills injection

    Usage:
        # Basic creation
        config = AgentConfig(...)
        agent = AgentFactory.create(config)

        # With skills (RECOMMENDED)
        skills = await ComponentLoader.load_skills(config, session)
        agent = AgentFactory.create(config, skills=skills)

        # Validate before creation
        result = AgentFactory.validate(config)
        if not result.is_valid:
            raise ValueError(result.errors)
    """

    _agent_classes: Dict[AgentType, Type[BaseAgent]] = {
        AgentType.SIMPLE: SimpleAgent,
        AgentType.LLM: LLMAgent,
        AgentType.RAG: RAGAgent,
        AgentType.TOOL: ToolAgent,
        AgentType.FULL: FullAgent,
        AgentType.ROUTER: RouterAgent,
        AgentType.ORCHESTRATOR: OrchestratorAgent,
    }

    @classmethod
    def create(
        cls,
        config: AgentConfig,
        skills: Optional[List[Skill]] = None,
        validate: bool = True,
    ) -> BaseAgent:
        """
        Create an agent instance from configuration.

        Args:
            config: Agent configuration
            skills: Optional list of skills to inject into the agent
            validate: Whether to validate config (default True)

        Returns:
            Agent instance of the appropriate type

        Raises:
            ValueError: If agent type is not supported or validation fails
        """
        # Validate config
        if validate:
            result = ComponentValidator.validate(config)
            if not result.is_valid:
                raise ValueError(
                    f"Agent configuration invalid: {'; '.join(result.errors)}"
                )
            # Warnings are logged but don't block creation

        # Validate config for the agent type (existing validation)
        config.validate_for_type()

        agent_type = config.agent_type
        agent_class = cls._agent_classes.get(agent_type)

        if not agent_class:
            supported = [t.value for t in cls._agent_classes.keys()]
            raise ValueError(
                f"Unsupported agent type: {agent_type}. "
                f"Supported types: {supported}"
            )

        # Log component status
        logger.info(
            "agent_factory_create",
            agent_id=config.id,
            agent_type=agent_type.value if hasattr(agent_type, "value") else str(agent_type),
            skills_count=len(skills) if skills else 0,
            tools_count=len([t for t in config.tools if t.enabled]) if config.tools else 0,
            has_kb=config.knowledge_base is not None,
        )

        # Create agent with skills
        try:
            return agent_class(config, skills=skills)
        except TypeError:
            # Fallback for agents that don't accept skills (e.g., SimpleAgent)
            logger.debug(
                "agent_skills_fallback",
                agent_id=config.id,
                message="Agent class doesn't accept skills in constructor",
            )
            agent = agent_class(config)
            if skills:
                agent.set_skills(skills)
            return agent

    @classmethod
    def validate(cls, config: AgentConfig):
        """
        Validate agent configuration.

        Args:
            config: Agent configuration to validate

        Returns:
            ComponentValidationResult with errors and warnings
        """
        return ComponentValidator.validate(config)

    @classmethod
    def register_type(
        cls,
        agent_type: AgentType,
        agent_class: Type[BaseAgent],
    ) -> None:
        """
        Register a custom agent type.

        Args:
            agent_type: The AgentType enum value
            agent_class: Agent class implementing BaseAgent
        """
        cls._agent_classes[agent_type] = agent_class
        logger.info(
            "agent_type_registered",
            agent_type=agent_type.value if hasattr(agent_type, "value") else str(agent_type),
            class_name=agent_class.__name__,
        )

    @classmethod
    def supported_types(cls) -> list[AgentType]:
        """Get list of supported agent types."""
        return list(cls._agent_classes.keys())

    @classmethod
    def get_agent_class(cls, agent_type: AgentType) -> Optional[Type[BaseAgent]]:
        """
        Get the agent class for a type.

        Args:
            agent_type: The agent type

        Returns:
            Agent class or None if not found
        """
        return cls._agent_classes.get(agent_type)

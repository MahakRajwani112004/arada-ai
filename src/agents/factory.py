"""Agent Factory - creates agents from configuration."""
from typing import Dict, Type

from src.agents.base import BaseAgent
from src.agents.types.full_agent import FullAgent
from src.agents.types.llm_agent import LLMAgent
from src.agents.types.rag_agent import RAGAgent
from src.agents.types.router_agent import RouterAgent
from src.agents.types.simple_agent import SimpleAgent
from src.agents.types.tool_agent import ToolAgent
from src.models.agent_config import AgentConfig
from src.models.enums import AgentType


class AgentFactory:
    """
    Factory for creating agent instances from configuration.

    Usage:
        config = AgentConfig(...)
        agent = AgentFactory.create(config)
        response = await agent.execute(context)
    """

    _agent_classes: Dict[AgentType, Type[BaseAgent]] = {
        AgentType.SIMPLE: SimpleAgent,
        AgentType.LLM: LLMAgent,
        AgentType.RAG: RAGAgent,
        AgentType.TOOL: ToolAgent,
        AgentType.FULL: FullAgent,
        AgentType.ROUTER: RouterAgent,
    }

    @classmethod
    def create(cls, config: AgentConfig) -> BaseAgent:
        """
        Create an agent instance from configuration.

        Args:
            config: Agent configuration

        Returns:
            Agent instance of the appropriate type

        Raises:
            ValueError: If agent type is not supported
        """
        # Validate config for the agent type
        config.validate_for_type()

        agent_type = config.agent_type
        agent_class = cls._agent_classes.get(agent_type)

        if not agent_class:
            supported = [t.value for t in cls._agent_classes.keys()]
            raise ValueError(
                f"Unsupported agent type: {agent_type}. "
                f"Supported types: {supported}"
            )

        return agent_class(config)

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

    @classmethod
    def supported_types(cls) -> list[AgentType]:
        """Get list of supported agent types."""
        return list(cls._agent_classes.keys())

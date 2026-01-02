"""Centralized component loading for agents.

This module provides deterministic loading of all agent components:
- Skills (domain expertise)
- Tools (MCP and custom functions)
- Knowledge Base (RAG retrieval)
- Child Agents (for orchestrators)

All component loading should go through this module to ensure consistency
across direct execution, Temporal workflows, and nested agent calls.
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.config.logging import get_logger
from src.models.agent_config import AgentConfig
from src.skills.models import Skill

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.knowledge.knowledge_base import KnowledgeBase
    from src.llm.providers.base import ToolDefinition

logger = get_logger(__name__)


class ComponentLoader:
    """
    Deterministic component loading for agents.

    Usage:
        # Load all components before creating agent
        components = await ComponentLoader.load_all(config, session)
        agent = AgentFactory.create(config, **components)

    This ensures:
    - Skills are always loaded from database
    - Tools are resolved from MCP registry
    - KB is initialized if configured
    - Child agents have their components loaded
    """

    @staticmethod
    async def load_all(
        config: AgentConfig,
        session: Optional["AsyncSession"] = None,
        load_kb: bool = True,
    ) -> Dict[str, Any]:
        """
        Load all components for an agent.

        Args:
            config: Agent configuration
            session: Database session for skill loading
            load_kb: Whether to initialize knowledge base

        Returns:
            Dictionary with loaded components:
            - skills: List[Skill]
            - tool_definitions: List[ToolDefinition]
            - knowledge_base: Optional[KnowledgeBase]
        """
        components: Dict[str, Any] = {
            "skills": [],
            "tool_definitions": [],
            "knowledge_base": None,
        }

        # Load skills if session provided
        if session:
            components["skills"] = await ComponentLoader.load_skills(config, session)

        # Load tool definitions
        components["tool_definitions"] = await ComponentLoader.load_tools(config)

        # Initialize knowledge base if configured and requested
        if load_kb and config.knowledge_base:
            components["knowledge_base"] = await ComponentLoader.load_knowledge_base(config)

        logger.info(
            "components_loaded",
            agent_id=config.id,
            skills_count=len(components["skills"]),
            tools_count=len(components["tool_definitions"]),
            has_kb=components["knowledge_base"] is not None,
        )

        return components

    @staticmethod
    async def load_skills(
        config: AgentConfig,
        session: "AsyncSession",
    ) -> List[Skill]:
        """
        Load skills from database for an agent.

        Args:
            config: Agent configuration with skills list
            session: Database session

        Returns:
            List of loaded Skill objects
        """
        if not config.skills:
            return []

        from src.skills.repository import SkillRepository

        skills: List[Skill] = []
        # Use a system user for skill loading (skills are tenant-scoped in repo)
        skill_repo = SkillRepository(session, user_id="system")

        for skill_config in config.skills:
            if not skill_config.enabled:
                continue

            try:
                skill = await skill_repo.get(skill_config.skill_id)
                if skill:
                    skills.append(skill)
                    logger.debug(
                        "skill_loaded",
                        agent_id=config.id,
                        skill_id=skill_config.skill_id,
                    )
                else:
                    logger.warning(
                        "skill_not_found",
                        agent_id=config.id,
                        skill_id=skill_config.skill_id,
                    )
            except Exception as e:
                logger.error(
                    "skill_load_failed",
                    agent_id=config.id,
                    skill_id=skill_config.skill_id,
                    error=str(e),
                )

        return skills

    @staticmethod
    async def load_tools(config: AgentConfig) -> List["ToolDefinition"]:
        """
        Load tool definitions from registry.

        Args:
            config: Agent configuration with tools list

        Returns:
            List of ToolDefinition objects for LLM function calling
        """
        if not config.tools:
            return []

        from src.tools.registry import get_registry

        registry = get_registry()
        enabled_tools = [t.tool_id for t in config.tools if t.enabled]

        if not enabled_tools:
            return []

        # Get OpenAI-format tool definitions
        tool_definitions = registry.get_openai_tools(enabled_tools)

        logger.debug(
            "tools_loaded",
            agent_id=config.id,
            tool_count=len(tool_definitions),
            tool_names=enabled_tools,
        )

        return tool_definitions

    @staticmethod
    async def load_knowledge_base(
        config: AgentConfig,
    ) -> Optional["KnowledgeBase"]:
        """
        Initialize knowledge base for an agent.

        Args:
            config: Agent configuration with knowledge_base config

        Returns:
            Initialized KnowledgeBase or None
        """
        if not config.knowledge_base:
            return None

        from src.knowledge.knowledge_base import KnowledgeBase

        try:
            kb = KnowledgeBase(config.knowledge_base)
            await kb.initialize()

            logger.debug(
                "knowledge_base_initialized",
                agent_id=config.id,
                collection=config.knowledge_base.collection_name,
            )

            return kb

        except Exception as e:
            logger.error(
                "knowledge_base_init_failed",
                agent_id=config.id,
                error=str(e),
            )
            return None

    @staticmethod
    async def load_child_agent_skills(
        child_config: AgentConfig,
        session: "AsyncSession",
    ) -> List[Skill]:
        """
        Load skills for a child agent (used by orchestrators).

        This ensures child agents get their domain expertise
        when called by an orchestrator.

        Args:
            child_config: Child agent configuration
            session: Database session

        Returns:
            List of loaded Skill objects for the child
        """
        return await ComponentLoader.load_skills(child_config, session)

    @staticmethod
    def get_enabled_tool_names(config: AgentConfig) -> List[str]:
        """
        Get list of enabled tool names from config.

        Args:
            config: Agent configuration

        Returns:
            List of tool IDs that are enabled
        """
        return [t.tool_id for t in config.tools if t.enabled]

    @staticmethod
    def get_enabled_skill_ids(config: AgentConfig) -> List[str]:
        """
        Get list of enabled skill IDs from config.

        Args:
            config: Agent configuration

        Returns:
            List of skill IDs that are enabled
        """
        return [s.skill_id for s in config.skills if s.enabled]


class ComponentValidationResult:
    """Result of agent component validation."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def is_valid(self) -> bool:
        """Returns True if no errors (warnings are ok)."""
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        """Add a validation error."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append(message)


class ComponentValidator:
    """
    Validates agent configuration for component requirements.

    Ensures agent type matches its component configuration.
    """

    @staticmethod
    def validate(config: AgentConfig) -> ComponentValidationResult:
        """
        Validate agent configuration.

        Args:
            config: Agent configuration to validate

        Returns:
            ComponentValidationResult with errors/warnings
        """
        result = ComponentValidationResult()
        agent_type = config.agent_type.value if hasattr(config.agent_type, "value") else str(config.agent_type)

        # ToolAgent requires tools
        if agent_type == "ToolAgent":
            if not config.tools or not any(t.enabled for t in config.tools):
                result.add_warning(
                    f"ToolAgent '{config.id}' has no enabled tools - "
                    "consider using LLMAgent instead"
                )

        # RAGAgent requires knowledge base
        elif agent_type == "RAGAgent":
            if not config.knowledge_base:
                result.add_error(
                    f"RAGAgent '{config.id}' requires knowledge_base configuration"
                )

        # FullAgent requires knowledge base and benefits from tools
        elif agent_type == "FullAgent":
            if not config.knowledge_base:
                result.add_error(
                    f"FullAgent '{config.id}' requires knowledge_base configuration"
                )
            if not config.tools or not any(t.enabled for t in config.tools):
                result.add_warning(
                    f"FullAgent '{config.id}' has no enabled tools - "
                    "consider using RAGAgent instead"
                )

        # RouterAgent requires routing table
        elif agent_type == "RouterAgent":
            if not config.routing_table:
                result.add_error(
                    f"RouterAgent '{config.id}' requires routing_table configuration"
                )

        # OrchestratorAgent requires available agents
        elif agent_type == "OrchestratorAgent":
            if not config.orchestrator_config:
                result.add_error(
                    f"OrchestratorAgent '{config.id}' requires orchestrator_config"
                )
            elif not config.orchestrator_config.available_agents and not config.orchestrator_config.auto_discover:
                result.add_warning(
                    f"OrchestratorAgent '{config.id}' has no available_agents and auto_discover is False - "
                    "it cannot orchestrate anything"
                )

        # All LLM-based agents should have llm_config
        if agent_type in ["LLMAgent", "RAGAgent", "ToolAgent", "FullAgent", "RouterAgent", "OrchestratorAgent"]:
            if not config.llm_config:
                result.add_error(
                    f"{agent_type} '{config.id}' requires llm_config"
                )

        # Log validation results
        if result.errors:
            logger.error(
                "agent_validation_failed",
                agent_id=config.id,
                agent_type=agent_type,
                errors=result.errors,
            )
        elif result.warnings:
            logger.warning(
                "agent_validation_warnings",
                agent_id=config.id,
                agent_type=agent_type,
                warnings=result.warnings,
            )

        return result

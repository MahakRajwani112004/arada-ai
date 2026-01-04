"""Base agent class - all agent types inherit from this with instrumentation."""
import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.config.logging import get_logger
from src.config.settings import get_settings
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse
from src.skills.models import Skill

if TYPE_CHECKING:
    from src.skills.selector import SkillSelector

logger = get_logger(__name__)
settings = get_settings()


class BaseAgent(ABC):
    """
    Abstract base agent class with automatic instrumentation.

    All agent types inherit from this and implement _execute_impl().
    The execute() method wraps _execute_impl() with monitoring.
    The config determines behavior, not the class.
    """

    def __init__(self, config: AgentConfig, skills: Optional[List[Skill]] = None):
        """Initialize agent with configuration and optional skills.

        Args:
            config: Agent configuration
            skills: List of loaded Skill objects to inject into prompts
        """
        self.config = config
        self.id = config.id
        self.name = config.name
        self._skills: List[Skill] = skills or []

        # Map skill_id -> parameters from config
        self._skill_parameters: Dict[str, Dict[str, Any]] = {}
        for skill_config in config.skills:
            if skill_config.enabled:
                self._skill_parameters[skill_config.skill_id] = skill_config.parameters

        # Initialize skill selector if we have multiple skills and LLM config
        self._skill_selector: Optional["SkillSelector"] = None
        if len(self._skills) > 2 and config.llm_config:
            from src.skills.selector import SkillSelector
            self._skill_selector = SkillSelector(config.llm_config)

    async def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execute the agent's logic with instrumentation.

        This is an instrumented wrapper that:
        1. Records timing
        2. Logs the execution
        3. Sends metrics to Prometheus
        4. Saves analytics to PostgreSQL

        Args:
            context: Runtime context with user input and session info

        Returns:
            AgentResponse with content and metadata
        """
        start_time = time.perf_counter()
        success = True
        error_type = None
        error_message = None
        response: Optional[AgentResponse] = None

        try:
            # Call the actual implementation
            response = await self._execute_impl(context)
            return response

        except Exception as e:
            success = False
            error_type = type(e).__name__
            error_message = str(e)
            raise

        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Get agent type from config
            agent_type = self.config.agent_type.value if hasattr(self.config.agent_type, "value") else str(self.config.agent_type)

            # Extract correlation IDs from context
            user_id = context.user_id
            request_id = context.request_id
            workflow_id = context.workflow_id

            # Extract input/output previews for analytics
            input_preview = context.user_input[:200] if context.user_input else None
            output_preview = response.content[:500] if response and response.content else None

            # Extract token/cost from response metadata if available
            total_tokens = 0
            total_cost_cents = 0
            if response and response.metadata:
                total_tokens = response.metadata.get("total_tokens", 0)
                total_cost_cents = response.metadata.get("total_cost_cents", 0)

            # Record Prometheus metrics
            if settings.monitoring_enabled:
                self._record_prometheus_metrics(
                    agent_type=agent_type,
                    success=success,
                    latency_ms=latency_ms,
                )

            # Record to PostgreSQL (async, non-blocking)
            if settings.analytics_enabled:
                asyncio.create_task(
                    self._record_analytics(
                        user_id=user_id,
                        agent_type=agent_type,
                        latency_ms=latency_ms,
                        success=success,
                        request_id=request_id,
                        workflow_id=workflow_id,
                        error_type=error_type,
                        error_message=error_message,
                        input_preview=input_preview,
                        output_preview=output_preview,
                        total_tokens=total_tokens,
                        total_cost_cents=total_cost_cents,
                    )
                )

            # Log the execution
            log_method = logger.info if success else logger.warning
            log_method(
                "agent_execution_completed",
                agent_id=self.id,
                agent_type=agent_type,
                latency_ms=latency_ms,
                success=success,
                error_type=error_type,
            )

    def _record_prometheus_metrics(
        self,
        agent_type: str,
        success: bool,
        latency_ms: int,
    ) -> None:
        """Record metrics to Prometheus."""
        try:
            from src.monitoring.metrics import (
                AGENT_EXECUTION_DURATION,
                AGENT_EXECUTIONS_TOTAL,
            )

            status = "success" if success else "failure"

            # Execution count
            AGENT_EXECUTIONS_TOTAL.labels(
                agent_id=self.id,
                agent_type=agent_type,
                status=status,
            ).inc()

            # Execution duration
            AGENT_EXECUTION_DURATION.labels(
                agent_id=self.id,
                agent_type=agent_type,
            ).observe(latency_ms / 1000)  # Convert to seconds

        except Exception as e:
            # Metrics should never break the main flow
            logger.debug("prometheus_metrics_failed", error=str(e))

    async def _record_analytics(
        self,
        user_id: str,
        agent_type: str,
        latency_ms: int,
        success: bool,
        request_id: Optional[str],
        workflow_id: Optional[str],
        error_type: Optional[str],
        error_message: Optional[str],
        # Overview tab fields (MVP)
        input_preview: Optional[str] = None,
        output_preview: Optional[str] = None,
        total_tokens: int = 0,
        total_cost_cents: int = 0,
        parent_execution_id: Optional[str] = None,
    ) -> None:
        """Record analytics to PostgreSQL."""
        try:
            from src.monitoring.analytics import get_analytics_service

            service = get_analytics_service()
            await service.record_agent_execution(
                user_id=user_id,
                agent_id=self.id,
                agent_type=agent_type,
                latency_ms=latency_ms,
                success=success,
                request_id=request_id,
                workflow_id=workflow_id,
                error_type=error_type,
                error_message=error_message,
                # Overview tab fields (MVP)
                input_preview=input_preview,
                output_preview=output_preview,
                total_tokens=total_tokens,
                total_cost_cents=total_cost_cents,
                parent_execution_id=parent_execution_id,
            )
        except Exception as e:
            # Analytics should never break the main flow
            logger.debug("analytics_record_failed", error=str(e))

    @abstractmethod
    async def _execute_impl(self, context: AgentContext) -> AgentResponse:
        """
        Actual implementation of agent execution.

        Subclasses implement this method instead of execute().
        The execute() method wraps this with instrumentation.

        This is implemented differently by each agent type:
        - SimpleAgent: Template/rule matching
        - LLMAgent: Single LLM call
        - RAGAgent: Retrieve + LLM
        - ToolAgent: LLM + Tool loop
        - FullAgent: Retrieve + LLM + Tool loop
        - RouterAgent: Classify + Route

        Args:
            context: Runtime context with user input and session info

        Returns:
            AgentResponse with content and metadata
        """
        pass

    async def _select_skills_for_query(
        self,
        user_input: str,
        user_id: Optional[str] = None,
    ) -> List[Skill]:
        """
        Select relevant skills for the given query.

        Uses LLM-based selection when there are more than 2 skills,
        otherwise returns all skills.

        Args:
            user_input: The user's query
            user_id: Optional user ID for tracking

        Returns:
            List of selected skills
        """
        if not self._skills:
            return []

        # If no selector or few skills, return all
        if not self._skill_selector or len(self._skills) <= 2:
            return self._skills

        return await self._skill_selector.select(
            query=user_input,
            available_skills=self._skills,
            max_skills=2,
            user_id=user_id,
        )

    def build_system_prompt(
        self,
        selected_skills: Optional[List[Skill]] = None,
    ) -> str:
        """
        Build system prompt from config.

        Args:
            selected_skills: Optional list of skills to inject. If None,
                           injects all skills (legacy behavior).

        Returns:
            Complete system prompt string
        """
        parts = []

        # Current date/time context with timezone
        import time
        now = datetime.now()
        # Get system timezone
        tz_name = time.tzname[time.daylight] if time.daylight else time.tzname[0]
        # Calculate UTC offset
        utc_offset_seconds = -time.timezone if not time.daylight else -time.altzone
        utc_offset_hours = utc_offset_seconds // 3600
        utc_offset_minutes = abs(utc_offset_seconds % 3600) // 60
        utc_offset_str = f"UTC{'+' if utc_offset_hours >= 0 else ''}{utc_offset_hours:+d}:{utc_offset_minutes:02d}"

        parts.append(
            f"## CURRENT DATE/TIME\n"
            f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')} {tz_name} ({utc_offset_str})\n"
            f"Today is {now.strftime('%A, %B %d, %Y')}\n"
            f"Timezone: {tz_name} ({utc_offset_str})"
        )

        # Role section
        role = self.config.role
        parts.append(f"## ROLE\nYou are {role.title}.")
        if role.expertise:
            parts.append(f"Your expertise: {', '.join(role.expertise)}.")
        if role.personality:
            parts.append(f"Your personality: {', '.join(role.personality)}.")
        parts.append(f"Communication style: {role.communication_style}.")

        # Goal section
        goal = self.config.goal
        parts.append(f"\n## GOAL\n{goal.objective}")
        if goal.constraints:
            parts.append("\nConstraints:")
            for constraint in goal.constraints:
                parts.append(f"- {constraint}")

        # Instructions section
        instructions = self.config.instructions
        if instructions.steps:
            parts.append("\n## INSTRUCTIONS")
            for i, step in enumerate(instructions.steps, 1):
                parts.append(f"{i}. {step}")

        if instructions.rules:
            parts.append("\n## RULES")
            for rule in instructions.rules:
                parts.append(f"- {rule}")

        if instructions.prohibited:
            parts.append("\n## PROHIBITED")
            for prohibited in instructions.prohibited:
                parts.append(f"- DO NOT: {prohibited}")

        # Anti-hallucination rules - always included for reliability
        parts.append("\n## CRITICAL RULES")
        parts.append("- ONLY state facts you can verify from provided context or tool results")
        parts.append("- If you don't have information, say \"I don't have that information\"")
        parts.append("- NEVER make up data, names, dates, numbers, or specific details")
        parts.append("- If asked about something not in your context, acknowledge the limitation")
        parts.append("- Do NOT repeat questions that have already been answered in the conversation")

        if instructions.output_format:
            parts.append(f"\n## OUTPUT FORMAT\n{instructions.output_format}")

        # Examples section
        if self.config.examples:
            parts.append("\n## EXAMPLES")
            for example in self.config.examples[:3]:  # Max 3 examples
                parts.append(f"\nInput: {example.input}")
                parts.append(f"Output: {example.output}")

        # Note: Tools are provided via native function calling, not in system prompt
        # The LLM receives tool definitions through the API's tool/function calling feature

        # Skills section - inject domain expertise
        # Use selected_skills if provided, otherwise fall back to all skills
        skills_to_inject = selected_skills if selected_skills is not None else self._skills
        if skills_to_inject:
            parts.append("\n## DOMAIN EXPERTISE")
            for skill in skills_to_inject:
                params = self._skill_parameters.get(skill.id, {})
                skill_context = skill.build_context_injection(params)
                parts.append(skill_context)
                parts.append("")  # Separator between skills

        return "\n".join(parts)

    def set_skills(self, skills: List[Skill]) -> None:
        """Set skills for this agent (for async loading after init).

        Args:
            skills: List of loaded Skill objects
        """
        self._skills = skills

    def get_enabled_skills(self) -> List[str]:
        """Get list of enabled skill IDs from config."""
        return [
            skill.skill_id for skill in self.config.skills if skill.enabled
        ]

    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tool IDs."""
        return [
            tool.tool_id for tool in self.config.tools if tool.enabled
        ]

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"

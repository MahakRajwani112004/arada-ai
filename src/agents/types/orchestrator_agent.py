"""OrchestratorAgent - coordinates multiple agents via tool calling."""
import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from src.agents.base import BaseAgent
from src.agents.confidence import ConfidenceCalculator, ConfidenceSignals
from src.llm import LLMClient
from src.llm.providers.base import LLMMessage, ToolCall, ToolDefinition
from src.models.agent_config import AgentConfig
from src.models.orchestrator_config import (
    AggregationStrategy,
    OrchestratorMode,
)
from src.models.responses import AgentContext, AgentResponse
from src.tools.agent_tool import AgentTool
from src.tools.registry import get_registry


class CircuitBreaker:
    """Simple circuit breaker for agent failures."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures: Dict[str, int] = {}
        self._open_time: Dict[str, float] = {}

    def record_failure(self, agent_id: str) -> None:
        """Record a failure for an agent."""
        self._failures[agent_id] = self._failures.get(agent_id, 0) + 1
        if self._failures[agent_id] >= self.failure_threshold:
            self._open_time[agent_id] = time.time()

    def record_success(self, agent_id: str) -> None:
        """Record a success - reset failure count."""
        self._failures[agent_id] = 0
        self._open_time.pop(agent_id, None)

    def is_open(self, agent_id: str) -> bool:
        """Check if circuit is open (agent should be skipped)."""
        if agent_id not in self._open_time:
            return False

        # Check if recovery timeout has passed
        if time.time() - self._open_time[agent_id] > self.recovery_timeout:
            # Half-open: allow one attempt
            self._open_time.pop(agent_id)
            self._failures[agent_id] = self.failure_threshold - 1
            return False

        return True

    def get_status(self, agent_id: str) -> str:
        """Get circuit status for an agent."""
        if agent_id in self._open_time:
            return "open"
        elif self._failures.get(agent_id, 0) > 0:
            return "half-open"
        return "closed"


class OrchestratorAgent(BaseAgent):
    """
    Agent that orchestrates other agents via native tool calling.

    The LLM can call agents as tools, enabling:
    - Dynamic agent selection at runtime
    - Parallel execution of multiple agents
    - Sequential chains passing context
    - Aggregation of results from multiple agents

    IMPORTANT: For production use with durability guarantees, use this agent
    through the Temporal workflow (AgentWorkflow._handle_orchestrator).
    The execute() method provides in-process execution for testing/simple use.

    Use cases:
    - Complex multi-step workflows
    - Ensemble decision making
    - Agent routing and coordination
    - Recursive agent hierarchies
    """

    DEFAULT_MAX_ITERATIONS = 15  # Default, can be overridden via orchestrator_config

    def __init__(
        self,
        config: AgentConfig,
        skills: Optional[List["Skill"]] = None,
    ):
        """
        Initialize OrchestratorAgent.

        Args:
            config: Agent configuration
            skills: List of Skill objects for domain expertise
        """
        from src.skills.models import Skill
        super().__init__(config, skills=skills)

        if not config.llm_config:
            raise ValueError("OrchestratorAgent requires llm_config")

        if not config.orchestrator_config:
            raise ValueError("OrchestratorAgent requires orchestrator_config")

        self._provider = LLMClient.get_provider(config.llm_config)
        self._orchestrator_config = config.orchestrator_config
        self._registry = get_registry()

        # Will be populated during execution
        self._agent_tools: Dict[str, AgentTool] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._agent_tool_definitions: List[ToolDefinition] = []

        # Circuit breaker for child agent failures
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60.0,
        )

    async def _load_agent_tools(self) -> None:
        """Load agent tool definitions for available agents."""
        from src.storage import PostgresAgentRepository
        from src.storage.database import get_session

        self._agent_tools = {}
        self._agent_configs = {}
        self._agent_tool_definitions = []

        # Get repository via session context manager
        async for session in get_session():
            repository = PostgresAgentRepository(session)
            for agent_ref in self._orchestrator_config.available_agents:
                config = await repository.get(agent_ref.agent_id)
                if config:
                    agent_tool = AgentTool(config)
                    tool_name = f"agent:{agent_ref.agent_id}"

                    self._agent_tools[tool_name] = agent_tool
                    self._agent_configs[agent_ref.agent_id] = config

                    # Build tool definition for LLM
                    defn = agent_tool.definition
                    description = agent_ref.description or defn.description

                    self._agent_tool_definitions.append(
                        ToolDefinition(
                            name=tool_name,
                            description=description,
                            parameters={
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The input/query to send to the agent",
                                    },
                                    "context": {
                                        "type": "string",
                                        "description": "Optional additional context",
                                    },
                                },
                                "required": ["query"],
                            },
                        )
                    )
            break  # Only need one iteration

    def _get_all_tool_definitions(self) -> List[ToolDefinition]:
        """Get all tool definitions (agents + regular tools)."""
        definitions = list(self._agent_tool_definitions)

        # Add regular tools if enabled
        enabled_tools = self.get_enabled_tools()
        if enabled_tools:
            regular_tools = [t for t in enabled_tools if not t.startswith("agent:")]
            if regular_tools:
                registry_definitions = self._registry.get_definitions(regular_tools)
                for defn in registry_definitions:
                    definitions.append(
                        ToolDefinition(
                            name=defn.name,
                            description=defn.description,
                            parameters=defn.to_openai_format()["function"]["parameters"],
                        )
                    )

        return definitions

    async def _execute_impl(self, context: AgentContext) -> AgentResponse:
        """
        Execute OrchestratorAgent in-process.

        NOTE: This executes agents directly without Temporal's durability.
        For production use with fault-tolerance, use via AgentWorkflow.

        For durable execution, the workflow's _handle_orchestrator method
        runs agent tools as Temporal activities with retry and recovery.
        """
        await self._load_agent_tools()

        mode = self._orchestrator_config.mode

        if mode == OrchestratorMode.LLM_DRIVEN:
            return await self._execute_llm_driven(context)
        elif mode == OrchestratorMode.WORKFLOW:
            return AgentResponse(
                content="Workflow mode requires Temporal execution.",
                confidence=0.0,
                error="Use AgentWorkflow for workflow mode",
            )
        elif mode == OrchestratorMode.HYBRID:
            return await self._execute_llm_driven(context)
        else:
            return AgentResponse(
                content=f"Unknown orchestrator mode: {mode}",
                confidence=0.0,
                error=f"Invalid mode: {mode}",
            )

    async def _execute_llm_driven(self, context: AgentContext) -> AgentResponse:
        """
        LLM-driven orchestration (in-process execution).

        The LLM decides which agents to call based on the input.
        Uses native tool calling for agent invocation.
        """
        import structlog
        logger = structlog.get_logger(__name__)

        # Store context for use in tool execution
        self._current_context = context

        messages = self._build_messages(context)
        tool_definitions = self._get_all_tool_definitions()

        all_tool_calls: List[Dict[str, Any]] = []
        all_agent_results: List[Dict[str, Any]] = []
        child_confidences: List[float] = []
        child_failures: int = 0
        iterations = 0

        # Use configurable max_iterations, fallback to default
        max_iterations = getattr(
            self._orchestrator_config, "max_iterations", self.DEFAULT_MAX_ITERATIONS
        )

        while iterations < max_iterations:
            iterations += 1

            response = await self._provider.complete(
                messages=messages,
                tools=tool_definitions if tool_definitions else None,
                user_id=context.user_id,
                agent_id=self.id,
                request_id=context.request_id,
                workflow_id=context.workflow_id,
            )

            if not response.tool_calls:
                # Calculate real confidence from signals
                signals = ConfidenceSignals(
                    finish_reason=response.finish_reason,
                    response_length=len(response.content or ""),
                    has_uncertainty_language=ConfidenceCalculator.detect_uncertainty(response.content or ""),
                    is_refusal=ConfidenceCalculator.detect_refusal(response.content or ""),
                    tool_calls_total=len(all_tool_calls),
                    tool_calls_succeeded=sum(1 for tc in all_tool_calls if tc.get("success", False)),
                    tool_calls_failed=sum(1 for tc in all_tool_calls if not tc.get("success", False)),
                    iterations_used=iterations,
                    max_iterations_reached=False,
                    child_confidences=child_confidences,
                    child_failures=child_failures,
                )
                confidence = ConfidenceCalculator.calculate(signals)

                return AgentResponse(
                    content=response.content,
                    confidence=confidence,
                    metadata={
                        "model": response.model,
                        "usage": response.usage,
                        "iterations": iterations,
                        "tool_calls": all_tool_calls,
                        "agent_results": all_agent_results,
                        "mode": "llm_driven",
                        "execution_mode": "in_process",
                        "child_confidences": child_confidences,
                    },
                )

            messages.append(
                LLMMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            results = await self._execute_tool_calls(response.tool_calls)

            for tool_call, result in zip(response.tool_calls, results):
                success = result.get("success", False)
                call_record = {
                    "tool": tool_call.name,
                    "arguments": tool_call.arguments,
                    "success": success,
                }
                all_tool_calls.append(call_record)

                if tool_call.name.startswith("agent:"):
                    all_agent_results.append({
                        "agent": tool_call.name,
                        "result": result,
                    })

                    # Track child confidence for aggregation
                    if success:
                        child_conf = result.get("metadata", {}).get("confidence", 0.85)
                        child_confidences.append(child_conf)
                    else:
                        child_failures += 1

                messages.append(
                    LLMMessage(
                        role="tool",
                        content=json.dumps(result),
                        tool_call_id=tool_call.id,
                    )
                )

        # Max iterations - calculate confidence with penalty
        signals = ConfidenceSignals(
            tool_calls_total=len(all_tool_calls),
            tool_calls_succeeded=sum(1 for tc in all_tool_calls if tc.get("success", False)),
            tool_calls_failed=sum(1 for tc in all_tool_calls if not tc.get("success", False)),
            iterations_used=iterations,
            max_iterations_reached=True,
            child_confidences=child_confidences,
            child_failures=child_failures,
        )
        confidence = ConfidenceCalculator.calculate(signals)

        return AgentResponse(
            content="Maximum orchestration iterations reached.",
            confidence=confidence,
            metadata={
                "iterations": iterations,
                "tool_calls": all_tool_calls,
                "agent_results": all_agent_results,
                "mode": "llm_driven",
                "child_confidences": child_confidences,
            },
        )

    async def _execute_tool_calls(
        self, tool_calls: List[ToolCall]
    ) -> List[Dict[str, Any]]:
        """Execute tool calls with parallel support for agents."""
        agent_calls = [tc for tc in tool_calls if tc.name.startswith("agent:")]
        other_calls = [tc for tc in tool_calls if not tc.name.startswith("agent:")]

        results: Dict[str, Dict[str, Any]] = {}

        # Execute agent calls in parallel
        if agent_calls:
            max_parallel = self._orchestrator_config.max_parallel
            agent_results = await self._execute_agent_calls_parallel(
                agent_calls, max_parallel
            )
            for tc, result in zip(agent_calls, agent_results):
                results[tc.id] = result

        # Execute other tool calls sequentially
        for tc in other_calls:
            result = await self._execute_single_tool(tc)
            results[tc.id] = result

        return [results[tc.id] for tc in tool_calls]

    async def _execute_agent_calls_parallel(
        self, tool_calls: List[ToolCall], max_parallel: int
    ) -> List[Dict[str, Any]]:
        """Execute agent tool calls in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(max_parallel)

        async def execute_with_limit(tc: ToolCall) -> Dict[str, Any]:
            async with semaphore:
                return await self._execute_single_tool(tc)

        tasks = [execute_with_limit(tc) for tc in tool_calls]
        return await asyncio.gather(*tasks)

    async def _execute_single_tool(self, tool_call: ToolCall) -> Dict[str, Any]:
        """Execute a single tool call with error handling and circuit breaker."""
        import structlog
        logger = structlog.get_logger(__name__)

        tool_name = tool_call.name
        arguments = tool_call.arguments

        # Validate arguments
        if not isinstance(arguments, dict):
            logger.warning(
                "tool_invalid_arguments",
                tool=tool_name,
                arguments_type=type(arguments).__name__,
            )
            return {
                "success": False,
                "output": None,
                "error": f"Invalid arguments type: expected dict, got {type(arguments).__name__}",
            }

        if tool_name.startswith("agent:"):
            agent_id = tool_name.split(":", 1)[1]

            # Check circuit breaker
            if self._circuit_breaker.is_open(agent_id):
                logger.warning(
                    "agent_circuit_open",
                    agent_id=agent_id,
                    status=self._circuit_breaker.get_status(agent_id),
                )
                return {
                    "success": False,
                    "content": "",
                    "agent_id": agent_id,
                    "error": f"Agent {agent_id} is temporarily unavailable (circuit open after failures)",
                }

            result = await self._execute_agent_in_process(tool_name, arguments)

            # Update circuit breaker based on result
            if result.get("success", False):
                self._circuit_breaker.record_success(agent_id)
            else:
                self._circuit_breaker.record_failure(agent_id)
                logger.warning(
                    "agent_execution_failed",
                    agent_id=agent_id,
                    error=result.get("error"),
                    circuit_status=self._circuit_breaker.get_status(agent_id),
                )

            return result
        else:
            # Regular tool execution with error handling
            try:
                result = await self._registry.execute(tool_name, **arguments)
                return {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                }
            except TypeError as e:
                logger.warning(
                    "tool_argument_error",
                    tool=tool_name,
                    error=str(e),
                )
                return {
                    "success": False,
                    "output": None,
                    "error": f"Tool argument error: {e}",
                }
            except Exception as e:
                logger.error(
                    "tool_execution_error",
                    tool=tool_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                return {
                    "success": False,
                    "output": None,
                    "error": f"Tool execution failed: {type(e).__name__}: {e}",
                }

    async def _execute_agent_in_process(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an agent in-process (without Temporal).

        This is useful for testing and simple use cases.
        For production with durability, use the workflow's _handle_orchestrator.

        IMPORTANT: This now loads skills for child agents to ensure they
        have their domain expertise during execution.
        """
        import structlog
        from src.agents.factory import AgentFactory
        from src.agents.component_loader import ComponentLoader
        from src.storage.database import get_session

        logger = structlog.get_logger(__name__)
        agent_id = tool_name.split(":", 1)[1]
        config = self._agent_configs.get(agent_id)

        if not config:
            return {
                "success": False,
                "content": "",
                "agent_id": agent_id,
                "error": f"Agent config not found: {agent_id}",
                "metadata": {"confidence": 0.0},
            }

        try:
            # Load skills for child agent
            child_skills = []
            if config.skills:
                async for session in get_session():
                    child_skills = await ComponentLoader.load_skills(config, session)
                    break

            # Create agent with its skills
            agent = AgentFactory.create(config, skills=child_skills)

            # Build context for the child agent
            query = arguments.get("query", "")
            additional_context = arguments.get("context", "")

            if additional_context:
                query = f"{query}\n\nContext: {additional_context}"

            # Pass parent's conversation history to child agent so it has context
            child_context = AgentContext(
                user_input=query,
                session_id=self._current_context.session_id,
                user_id=self._current_context.user_id,
                conversation_history=self._current_context.conversation_history,
                metadata={"parent_orchestrator": self.id},
                request_id=self._current_context.request_id,
                workflow_id=self._current_context.workflow_id,
            )

            response = await agent.execute(child_context)

            logger.info(
                "child_agent_executed",
                agent_id=agent_id,
                success=True,
                confidence=response.confidence,
            )

            return {
                "success": True,
                "content": response.content,
                "agent_id": agent_id,
                "error": response.error,
                "metadata": {
                    **(response.metadata or {}),
                    "confidence": response.confidence,
                },
            }

        except Exception as e:
            logger.error(
                "child_agent_execution_error",
                agent_id=agent_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "success": False,
                "content": "",
                "agent_id": agent_id,
                "error": str(e),
                "metadata": {"confidence": 0.0},
            }

    def _build_messages(self, context: AgentContext) -> List[LLMMessage]:
        """Build messages for LLM conversation."""
        messages = []

        system_prompt = self._build_orchestration_prompt()
        messages.append(LLMMessage(role="system", content=system_prompt))

        for msg in context.conversation_history:
            messages.append(LLMMessage(role=msg.role, content=msg.content))

        messages.append(LLMMessage(role="user", content=context.user_input))

        return messages

    def _build_orchestration_prompt(self) -> str:
        """Build system prompt for orchestration."""
        base_prompt = self.build_system_prompt()

        agent_list = []
        for agent_ref in self._orchestrator_config.available_agents:
            agent_info = f"- agent:{agent_ref.agent_id}"
            if agent_ref.alias:
                agent_info += f" (alias: {agent_ref.alias})"
            if agent_ref.description:
                agent_info += f": {agent_ref.description}"
            agent_list.append(agent_info)

        orchestration_section = f"""

## ORCHESTRATION

You are an orchestrator agent that coordinates other specialized agents.

Available agents:
{chr(10).join(agent_list) if agent_list else "No agents configured."}

You can call these agents as tools using their agent: prefix names.
Each agent will process your query and return results.

Guidelines:
- Call agents when their expertise matches the task
- You can call multiple agents in parallel if needed
- Synthesize results from multiple agents into a coherent response
- If an agent fails, consider alternatives or explain the limitation
"""

        return base_prompt + orchestration_section

    async def aggregate_results(
        self,
        results: List[Dict[str, Any]],
        strategy: Optional[AggregationStrategy] = None,
    ) -> str:
        """
        Aggregate results from multiple agent calls.

        Uses the orchestration.aggregators module for implementation.
        """
        from src.orchestration.aggregators import AgentResult, create_aggregator

        strategy = strategy or self._orchestrator_config.default_aggregation

        # Convert to AgentResult objects
        agent_results = [
            AgentResult(
                agent_id=r.get("agent_id", "unknown"),
                success=r.get("success", False),
                content=r.get("content", ""),
                error=r.get("error"),
                metadata=r.get("metadata", {}),
            )
            for r in results
        ]

        # Create and use aggregator (pass user_id through llm_config for LLM-based aggregators)
        llm_config = self.config.llm_config.model_dump() if self.config.llm_config else {}
        llm_config["user_id"] = self._current_context.user_id if hasattr(self, "_current_context") else "system"
        aggregator = create_aggregator(
            strategy,
            config={"llm_config": llm_config},
        )

        return await aggregator.aggregate(agent_results)

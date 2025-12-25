"""OrchestratorAgent - coordinates multiple agents via tool calling."""
import asyncio
import json
from typing import Any, Dict, List, Optional

from src.agents.base import BaseAgent
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

    MAX_ITERATIONS = 15

    def __init__(self, config: AgentConfig):
        """Initialize OrchestratorAgent."""
        super().__init__(config)

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
        messages = self._build_messages(context)
        tool_definitions = self._get_all_tool_definitions()

        all_tool_calls: List[Dict[str, Any]] = []
        all_agent_results: List[Dict[str, Any]] = []
        iterations = 0

        while iterations < self.MAX_ITERATIONS:
            iterations += 1

            response = await self._provider.complete(
                messages=messages,
                tools=tool_definitions if tool_definitions else None,
            )

            if not response.tool_calls:
                return AgentResponse(
                    content=response.content,
                    confidence=0.9,
                    metadata={
                        "model": response.model,
                        "usage": response.usage,
                        "iterations": iterations,
                        "tool_calls": all_tool_calls,
                        "agent_results": all_agent_results,
                        "mode": "llm_driven",
                        "execution_mode": "in_process",
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
                call_record = {
                    "tool": tool_call.name,
                    "arguments": tool_call.arguments,
                    "success": result.get("success", False),
                }
                all_tool_calls.append(call_record)

                if tool_call.name.startswith("agent:"):
                    all_agent_results.append({
                        "agent": tool_call.name,
                        "result": result,
                    })

                messages.append(
                    LLMMessage(
                        role="tool",
                        content=json.dumps(result),
                        tool_call_id=tool_call.id,
                    )
                )

        return AgentResponse(
            content="Maximum orchestration iterations reached.",
            confidence=0.5,
            metadata={
                "iterations": iterations,
                "tool_calls": all_tool_calls,
                "agent_results": all_agent_results,
                "mode": "llm_driven",
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
        """Execute a single tool call."""
        tool_name = tool_call.name
        arguments = tool_call.arguments

        if tool_name.startswith("agent:"):
            return await self._execute_agent_in_process(tool_name, arguments)
        else:
            result = await self._registry.execute(tool_name, **arguments)
            return {
                "success": result.success,
                "output": result.output,
                "error": result.error,
            }

    async def _execute_agent_in_process(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an agent in-process (without Temporal).

        This is useful for testing and simple use cases.
        For production with durability, use the workflow's _handle_orchestrator.
        """
        from src.agents.factory import AgentFactory

        agent_id = tool_name.split(":", 1)[1]
        config = self._agent_configs.get(agent_id)

        if not config:
            return {
                "success": False,
                "content": "",
                "agent_id": agent_id,
                "error": f"Agent config not found: {agent_id}",
            }

        try:
            # Create and execute the agent directly
            agent = AgentFactory.create(config)

            # Build context for the child agent
            query = arguments.get("query", "")
            additional_context = arguments.get("context", "")

            if additional_context:
                query = f"{query}\n\nContext: {additional_context}"

            child_context = AgentContext(
                user_input=query,
                conversation_history=[],
                session_id=None,
                metadata={"parent_orchestrator": self.id},
            )

            response = await agent.execute(child_context)

            return {
                "success": True,
                "content": response.content,
                "agent_id": agent_id,
                "error": response.error,
                "metadata": response.metadata,
            }

        except Exception as e:
            return {
                "success": False,
                "content": "",
                "agent_id": agent_id,
                "error": str(e),
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

        # Create and use aggregator
        aggregator = create_aggregator(
            strategy,
            config={"llm_config": self.config.llm_config.model_dump() if self.config.llm_config else {}},
        )

        return await aggregator.aggregate(agent_results)

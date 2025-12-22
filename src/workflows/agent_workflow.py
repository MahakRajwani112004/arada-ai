"""Agent Workflow - Main Temporal workflow for all agent types."""
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, List, Optional

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from src.activities.agent_tool_activity import (
        AgentToolExecutionInput,
        AgentToolExecutionOutput,
        GetAgentToolDefinitionsInput,
        GetAgentToolDefinitionsOutput,
        execute_agent_as_tool,
        get_agent_tool_definitions,
    )
    from src.activities.knowledge_activity import (
        RetrieveInput,
        RetrieveOutput,
        retrieve_knowledge,
    )
    from src.activities.llm_activity import (
        LLMCompletionInput,
        LLMCompletionOutput,
        ToolDefinitionInput,
        llm_completion,
    )
    from src.activities.safety_activity import (
        SafetyCheckInput,
        SafetyCheckOutput,
        check_input_safety,
        check_output_safety,
    )
    from src.activities.tool_activity import (
        GetToolDefinitionsInput,
        GetToolDefinitionsOutput,
        ToolExecutionInput,
        ToolExecutionOutput,
        execute_tool,
        get_tool_definitions,
    )
    from src.models.enums import AgentType
    from src.models.orchestrator_config import AggregationStrategy, OrchestratorMode


@dataclass
class AgentWorkflowInput:
    """Input for agent workflow."""

    agent_id: str
    agent_type: str
    user_input: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    session_id: Optional[str] = None

    # Agent configuration (flattened for workflow)
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024

    # System prompt (pre-built from config)
    system_prompt: str = ""

    # Safety settings
    safety_level: str = "standard"
    blocked_topics: List[str] = field(default_factory=list)

    # RAG settings (for RAGAgent/FullAgent)
    knowledge_collection: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    top_k: int = 5
    similarity_threshold: Optional[float] = None

    # Tool settings (for ToolAgent/FullAgent)
    enabled_tools: List[str] = field(default_factory=list)

    # Router settings (for RouterAgent)
    routing_table: Dict[str, str] = field(default_factory=dict)

    # Orchestrator settings (for OrchestratorAgent)
    orchestrator_mode: str = "llm_driven"
    orchestrator_available_agents: List[Dict[str, Any]] = field(default_factory=list)
    orchestrator_max_parallel: int = 5
    orchestrator_max_depth: int = 3
    orchestrator_aggregation: str = "all"


@dataclass
class AgentWorkflowOutput:
    """Output from agent workflow."""

    content: str
    agent_id: str
    agent_type: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Helper Functions (shared across handlers)
# =============================================================================


def sanitize_tool_name(name: str) -> str:
    """
    Convert tool name to OpenAI-compatible format.

    OpenAI requires tool names to match ^[a-zA-Z0-9_-]+$ (no colons).
    We convert colons to double underscores.
    """
    return name.replace(":", "__")


def build_param_schema(param: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build parameter schema with proper array handling.

    Ensures array types have items schema as required by OpenAI.
    """
    schema: Dict[str, Any] = {
        "type": param["type"],
        "description": param["description"],
    }
    # For array types, add items schema
    if param["type"] == "array":
        schema["items"] = param.get("items") or {"type": "string"}
    return schema


def build_tool_definitions(
    definitions: List[Any],
    tool_name_map: Dict[str, str],
) -> List["ToolDefinitionInput"]:
    """
    Convert tool definitions to LLM activity format.

    Args:
        definitions: List of tool definition objects
        tool_name_map: Dict to populate with sanitized -> original name mapping

    Returns:
        List of ToolDefinitionInput for LLM activity
    """
    tools = []
    for d in definitions:
        sanitized_name = sanitize_tool_name(d.name)
        tool_name_map[sanitized_name] = d.name
        tools.append(
            ToolDefinitionInput(
                name=sanitized_name,
                description=d.description,
                parameters={
                    "type": "object",
                    "properties": {
                        p["name"]: build_param_schema(p) for p in d.parameters
                    },
                    "required": [
                        p["name"] for p in d.parameters if p.get("required", True)
                    ],
                },
            )
        )
    return tools


@workflow.defn
class AgentWorkflow:
    """
    Unified workflow for all agent types.

    Routes to appropriate execution path based on agent_type:
    - SimpleAgent: No LLM, returns based on patterns
    - LLMAgent: Single LLM call
    - RAGAgent: Retrieve + LLM
    - ToolAgent: LLM + Tool loop
    - FullAgent: Retrieve + LLM + Tool loop
    - RouterAgent: Classify + Route
    """

    @workflow.run
    async def run(self, input: AgentWorkflowInput) -> AgentWorkflowOutput:
        """Execute the agent workflow."""
        workflow.logger.info(
            f"Starting agent workflow: id={input.agent_id}, type={input.agent_type}"
        )

        try:
            # Input safety check
            safety_result = await self._check_safety(
                input.user_input,
                input.safety_level,
                input.blocked_topics,
                is_input=True,
            )

            if not safety_result.is_safe:
                return AgentWorkflowOutput(
                    content="I cannot process this request due to safety policies.",
                    agent_id=input.agent_id,
                    agent_type=input.agent_type,
                    success=False,
                    error=f"Safety violation: {', '.join(safety_result.violations)}",
                    metadata={"safety_violations": safety_result.violations},
                )

            # Route to appropriate handler
            agent_type = AgentType(input.agent_type)

            if agent_type == AgentType.SIMPLE:
                result = await self._handle_simple(input)
            elif agent_type == AgentType.LLM:
                result = await self._handle_llm(input)
            elif agent_type == AgentType.RAG:
                result = await self._handle_rag(input)
            elif agent_type == AgentType.TOOL:
                result = await self._handle_tool(input)
            elif agent_type == AgentType.FULL:
                result = await self._handle_full(input)
            elif agent_type == AgentType.ROUTER:
                result = await self._handle_router(input)
            elif agent_type == AgentType.ORCHESTRATOR:
                result = await self._handle_orchestrator(input)
            else:
                raise ValueError(f"Unknown agent type: {input.agent_type}")

            # Output safety check
            output_safety = await self._check_safety(
                result.content,
                input.safety_level,
                input.blocked_topics,
                is_input=False,
            )

            if not output_safety.is_safe:
                return AgentWorkflowOutput(
                    content="I generated a response but it was filtered for safety.",
                    agent_id=input.agent_id,
                    agent_type=input.agent_type,
                    success=False,
                    error="Output safety violation",
                    metadata={"filtered": True},
                )

            return result

        except Exception as e:
            workflow.logger.error(f"Workflow error: {e}")
            return AgentWorkflowOutput(
                content="An error occurred while processing your request.",
                agent_id=input.agent_id,
                agent_type=input.agent_type,
                success=False,
                error=str(e),
            )

    async def _check_safety(
        self,
        content: str,
        safety_level: str,
        blocked_topics: List[str],
        is_input: bool,
    ) -> SafetyCheckOutput:
        """Run safety check activity."""
        check_fn = check_input_safety if is_input else check_output_safety
        return await workflow.execute_activity(
            check_fn,
            SafetyCheckInput(
                content=content,
                safety_level=safety_level,
                blocked_topics=blocked_topics,
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )

    async def _handle_simple(
        self, input: AgentWorkflowInput
    ) -> AgentWorkflowOutput:
        """Handle SimpleAgent - pattern matching only."""
        # SimpleAgent doesn't use LLM, returns default
        return AgentWorkflowOutput(
            content=f"SimpleAgent response for: {input.user_input[:50]}...",
            agent_id=input.agent_id,
            agent_type=input.agent_type,
            success=True,
            metadata={"match_type": "workflow_default"},
        )

    async def _handle_llm(
        self, input: AgentWorkflowInput
    ) -> AgentWorkflowOutput:
        """Handle LLMAgent - single LLM call."""
        if not input.llm_provider or not input.llm_model:
            raise ValueError("LLMAgent requires llm_provider and llm_model")

        # Build messages
        messages = [{"role": "system", "content": input.system_prompt}]
        messages.extend(input.conversation_history)
        messages.append({"role": "user", "content": input.user_input})

        # Call LLM activity
        result: LLMCompletionOutput = await workflow.execute_activity(
            llm_completion,
            LLMCompletionInput(
                provider=input.llm_provider,
                model=input.llm_model,
                messages=messages,
                temperature=input.llm_temperature,
                max_tokens=input.llm_max_tokens,
            ),
            start_to_close_timeout=timedelta(seconds=120),
        )

        return AgentWorkflowOutput(
            content=result.content,
            agent_id=input.agent_id,
            agent_type=input.agent_type,
            success=True,
            metadata={
                "model": result.model,
                "usage": result.usage,
                "finish_reason": result.finish_reason,
            },
        )

    async def _handle_rag(
        self, input: AgentWorkflowInput
    ) -> AgentWorkflowOutput:
        """Handle RAGAgent - retrieve + LLM."""
        if not input.llm_provider or not input.llm_model:
            raise ValueError("RAGAgent requires llm_provider and llm_model")
        if not input.knowledge_collection:
            raise ValueError("RAGAgent requires knowledge_collection")

        # Step 1: Retrieve relevant documents
        retrieval_result: RetrieveOutput = await workflow.execute_activity(
            retrieve_knowledge,
            RetrieveInput(
                query=input.user_input,
                collection_name=input.knowledge_collection,
                embedding_model=input.embedding_model,
                top_k=input.top_k,
                similarity_threshold=input.similarity_threshold,
            ),
            start_to_close_timeout=timedelta(seconds=60),
        )

        # Step 2: Build context from retrieved documents
        context_docs = "\n\n".join([
            f"[Document {i+1}]\n{doc.content}"
            for i, doc in enumerate(retrieval_result.documents)
        ])

        # Augment system prompt with context
        augmented_prompt = input.system_prompt
        if context_docs:
            augmented_prompt += f"\n\n## RETRIEVED CONTEXT\n{context_docs}"

        # Step 3: Generate response with LLM
        messages = [{"role": "system", "content": augmented_prompt}]
        messages.extend(input.conversation_history)
        messages.append({"role": "user", "content": input.user_input})

        llm_result: LLMCompletionOutput = await workflow.execute_activity(
            llm_completion,
            LLMCompletionInput(
                provider=input.llm_provider,
                model=input.llm_model,
                messages=messages,
                temperature=input.llm_temperature,
                max_tokens=input.llm_max_tokens,
            ),
            start_to_close_timeout=timedelta(seconds=120),
        )

        return AgentWorkflowOutput(
            content=llm_result.content,
            agent_id=input.agent_id,
            agent_type=input.agent_type,
            success=True,
            metadata={
                "model": llm_result.model,
                "usage": llm_result.usage,
                "finish_reason": llm_result.finish_reason,
                "retrieved_count": retrieval_result.total_found,
                "retrieval_scores": [
                    doc.score for doc in retrieval_result.documents
                ],
            },
        )

    async def _handle_tool(
        self, input: AgentWorkflowInput
    ) -> AgentWorkflowOutput:
        """Handle ToolAgent - LLM + native tool calling loop."""
        import json

        if not input.llm_provider or not input.llm_model:
            raise ValueError("ToolAgent requires llm_provider and llm_model")

        MAX_TOOL_ITERATIONS = 10
        tool_calls_made = []
        iterations = 0

        # Get tool definitions for enabled tools
        tool_defs_result: GetToolDefinitionsOutput = await workflow.execute_activity(
            get_tool_definitions,
            GetToolDefinitionsInput(tool_names=input.enabled_tools),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Convert to LLM format with name sanitization
        tool_name_map: Dict[str, str] = {}
        tools = build_tool_definitions(tool_defs_result.definitions, tool_name_map)

        # Build set of resolved enabled tools (values in tool_name_map are resolved names)
        resolved_enabled_tools = set(tool_name_map.values())

        workflow.logger.info(f"Tool definitions loaded: {[t.name for t in tools]}")
        workflow.logger.info(f"Resolved enabled tools: {resolved_enabled_tools}")

        messages: List[Dict[str, Any]] = [{"role": "system", "content": input.system_prompt}]
        messages.extend(input.conversation_history)
        messages.append({"role": "user", "content": input.user_input})

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1

            # Call LLM with tools
            llm_result: LLMCompletionOutput = await workflow.execute_activity(
                llm_completion,
                LLMCompletionInput(
                    provider=input.llm_provider,
                    model=input.llm_model,
                    messages=messages,
                    temperature=input.llm_temperature,
                    max_tokens=input.llm_max_tokens,
                    tools=tools if tools else None,
                ),
                start_to_close_timeout=timedelta(seconds=120),
            )

            # Check for native tool calls
            if not llm_result.tool_calls:
                # No tool calls, return response
                return AgentWorkflowOutput(
                    content=llm_result.content,
                    agent_id=input.agent_id,
                    agent_type=input.agent_type,
                    success=True,
                    metadata={
                        "model": llm_result.model,
                        "usage": llm_result.usage,
                        "tool_calls": tool_calls_made,
                        "iterations": iterations,
                    },
                )

            # Add assistant message with tool calls to conversation
            messages.append({
                "role": "assistant",
                "content": llm_result.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                    for tc in llm_result.tool_calls
                ],
            })

            # Execute each tool and add results
            for tc in llm_result.tool_calls:
                # Map sanitized name back to original
                original_name = tool_name_map.get(tc.name, tc.name)
                workflow.logger.info(f"Executing tool: {original_name} (sanitized: {tc.name}) with args: {tc.arguments}")

                # Check if tool is enabled (use resolved name)
                if original_name not in resolved_enabled_tools:
                    tool_result = {"error": f"Tool {original_name} not enabled"}
                else:
                    result: ToolExecutionOutput = await workflow.execute_activity(
                        execute_tool,
                        ToolExecutionInput(
                            tool_name=original_name,  # Use original name for execution
                            arguments=tc.arguments,
                        ),
                        start_to_close_timeout=timedelta(seconds=60),
                    )
                    tool_result = {
                        "success": result.success,
                        "output": result.output,
                        "error": result.error,
                    }

                tool_calls_made.append({
                    "tool": original_name,
                    "args": tc.arguments,
                    "result": tool_result,
                })

                # Add tool result message
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result),
                    "tool_call_id": tc.id,
                })

        # Max iterations reached
        return AgentWorkflowOutput(
            content="Maximum tool iterations reached.",
            agent_id=input.agent_id,
            agent_type=input.agent_type,
            success=False,
            error="Max iterations",
            metadata={"tool_calls": tool_calls_made, "iterations": iterations},
        )

    async def _handle_full(
        self, input: AgentWorkflowInput
    ) -> AgentWorkflowOutput:
        """Handle FullAgent - retrieve + LLM + native tool calling loop."""
        import json

        if not input.llm_provider or not input.llm_model:
            raise ValueError("FullAgent requires llm_provider and llm_model")
        if not input.knowledge_collection:
            raise ValueError("FullAgent requires knowledge_collection")

        # Step 1: Retrieve relevant documents
        retrieval_result: RetrieveOutput = await workflow.execute_activity(
            retrieve_knowledge,
            RetrieveInput(
                query=input.user_input,
                collection_name=input.knowledge_collection,
                embedding_model=input.embedding_model,
                top_k=input.top_k,
                similarity_threshold=input.similarity_threshold,
            ),
            start_to_close_timeout=timedelta(seconds=60),
        )

        # Build context with retrieved docs
        context_docs = "\n\n".join([
            f"[Document {i+1}]\n{doc.content}"
            for i, doc in enumerate(retrieval_result.documents)
        ])

        augmented_prompt = input.system_prompt
        if context_docs:
            augmented_prompt += f"\n\n## RETRIEVED CONTEXT\n{context_docs}"

        # Get tool definitions for enabled tools
        tool_defs_result: GetToolDefinitionsOutput = await workflow.execute_activity(
            get_tool_definitions,
            GetToolDefinitionsInput(tool_names=input.enabled_tools),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Convert to LLM format with name sanitization
        tool_name_map: Dict[str, str] = {}
        tools = build_tool_definitions(tool_defs_result.definitions, tool_name_map)

        # Build set of resolved enabled tools
        resolved_enabled_tools = set(tool_name_map.values())

        # Step 2: Tool loop with RAG context
        MAX_TOOL_ITERATIONS = 10
        tool_calls_made = []
        iterations = 0

        messages: List[Dict[str, Any]] = [{"role": "system", "content": augmented_prompt}]
        messages.extend(input.conversation_history)
        messages.append({"role": "user", "content": input.user_input})

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1

            llm_result: LLMCompletionOutput = await workflow.execute_activity(
                llm_completion,
                LLMCompletionInput(
                    provider=input.llm_provider,
                    model=input.llm_model,
                    messages=messages,
                    temperature=input.llm_temperature,
                    max_tokens=input.llm_max_tokens,
                    tools=tools if tools else None,
                ),
                start_to_close_timeout=timedelta(seconds=120),
            )

            # Check for native tool calls
            if not llm_result.tool_calls:
                return AgentWorkflowOutput(
                    content=llm_result.content,
                    agent_id=input.agent_id,
                    agent_type=input.agent_type,
                    success=True,
                    metadata={
                        "model": llm_result.model,
                        "usage": llm_result.usage,
                        "retrieved_count": retrieval_result.total_found,
                        "tool_calls": tool_calls_made,
                        "iterations": iterations,
                    },
                )

            # Add assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": llm_result.content or "",
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in llm_result.tool_calls
                ],
            })

            # Execute each tool
            for tc in llm_result.tool_calls:
                # Map sanitized name back to original (resolved) name
                original_name = tool_name_map.get(tc.name, tc.name)

                if original_name not in resolved_enabled_tools:
                    tool_result = {"error": f"Tool {original_name} not enabled"}
                else:
                    result: ToolExecutionOutput = await workflow.execute_activity(
                        execute_tool,
                        ToolExecutionInput(tool_name=original_name, arguments=tc.arguments),
                        start_to_close_timeout=timedelta(seconds=60),
                    )
                    tool_result = {"success": result.success, "output": result.output, "error": result.error}

                tool_calls_made.append({"tool": original_name, "args": tc.arguments, "result": tool_result})
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result),
                    "tool_call_id": tc.id,
                })

        return AgentWorkflowOutput(
            content="Maximum iterations reached.",
            agent_id=input.agent_id,
            agent_type=input.agent_type,
            success=False,
            metadata={"tool_calls": tool_calls_made},
        )

    async def _handle_router(
        self, input: AgentWorkflowInput
    ) -> AgentWorkflowOutput:
        """Handle RouterAgent - classify + route."""
        if not input.llm_provider or not input.llm_model:
            raise ValueError("RouterAgent requires llm_provider and llm_model")
        if not input.routing_table:
            raise ValueError("RouterAgent requires routing_table")

        # Build classification prompt
        categories = [k for k in input.routing_table.keys() if k != "default"]
        categories_str = ", ".join(categories)

        system_prompt = f"""You are a routing classifier. Classify the user's input into exactly one category.

Available categories: {categories_str}

Respond with ONLY the category name, nothing else."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input.user_input},
        ]

        llm_result: LLMCompletionOutput = await workflow.execute_activity(
            llm_completion,
            LLMCompletionInput(
                provider=input.llm_provider,
                model=input.llm_model,
                messages=messages,
                temperature=0.1,
                max_tokens=50,
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )

        classification = llm_result.content.strip().lower()
        target_agent = None

        for category in input.routing_table.keys():
            if category.lower() in classification:
                target_agent = input.routing_table[category]
                classification = category
                break

        if not target_agent:
            target_agent = input.routing_table.get("default")
            classification = "default"

        return AgentWorkflowOutput(
            content=f"Routing to: {target_agent}" if target_agent else "No route found",
            agent_id=input.agent_id,
            agent_type=input.agent_type,
            success=target_agent is not None,
            metadata={
                "classification": classification,
                "target_agent": target_agent,
                "routing_table": input.routing_table,
            },
        )

    async def _handle_orchestrator(
        self, input: AgentWorkflowInput
    ) -> AgentWorkflowOutput:
        """Handle OrchestratorAgent - coordinate multiple agents via tool calling."""
        import json

        if not input.llm_provider or not input.llm_model:
            raise ValueError("OrchestratorAgent requires llm_provider and llm_model")
        if not input.orchestrator_available_agents:
            raise ValueError("OrchestratorAgent requires orchestrator_available_agents")

        MAX_ORCHESTRATOR_ITERATIONS = 15
        tool_calls_made = []
        agent_results = []
        iterations = 0

        # Get agent tool definitions for available agents
        agent_ids = [a.get("agent_id") for a in input.orchestrator_available_agents if a.get("agent_id")]

        agent_tool_defs: GetAgentToolDefinitionsOutput = await workflow.execute_activity(
            get_agent_tool_definitions,
            GetAgentToolDefinitionsInput(agent_ids=agent_ids),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Build tool definitions from agent definitions
        tool_name_map: Dict[str, str] = {}
        tools = []

        # Agent tools have a fixed parameter schema
        for agent_def in agent_tool_defs.definitions:
            sanitized_name = sanitize_tool_name(agent_def.name)
            tool_name_map[sanitized_name] = agent_def.name

            # Find the matching agent reference for description override
            agent_ref = next(
                (a for a in input.orchestrator_available_agents if a.get("agent_id") == agent_def.agent_id),
                None,
            )
            description = agent_ref.get("description", agent_def.description) if agent_ref else agent_def.description

            tools.append(
                ToolDefinitionInput(
                    name=sanitized_name,
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

        # Also add regular tools if enabled
        if input.enabled_tools:
            regular_tools = [t for t in input.enabled_tools if not t.startswith("agent:")]
            if regular_tools:
                tool_defs_result: GetToolDefinitionsOutput = await workflow.execute_activity(
                    get_tool_definitions,
                    GetToolDefinitionsInput(tool_names=regular_tools),
                    start_to_close_timeout=timedelta(seconds=30),
                )
                # Use helper to build regular tool definitions
                tools.extend(build_tool_definitions(tool_defs_result.definitions, tool_name_map))

        workflow.logger.info(f"Orchestrator tools loaded: {[t.name for t in tools]}")

        # Build orchestration system prompt
        agent_list_items = []
        for a in input.orchestrator_available_agents:
            agent_id = a.get("agent_id", "unknown")
            tool_name = sanitize_tool_name(f"agent:{agent_id}")
            desc = a.get("description", "Specialized agent")
            agent_list_items.append(f"- {tool_name}: {desc}")
        agent_list = "\n".join(agent_list_items)

        orchestration_prompt = f"""{input.system_prompt}

## ORCHESTRATION

You are an orchestrator agent that coordinates specialized agents.

Available agents:
{agent_list}

Call agents as tools to delegate tasks. Synthesize their results into a coherent response.
"""

        messages: List[Dict[str, Any]] = [{"role": "system", "content": orchestration_prompt}]
        messages.extend(input.conversation_history)
        messages.append({"role": "user", "content": input.user_input})

        while iterations < MAX_ORCHESTRATOR_ITERATIONS:
            iterations += 1

            # Call LLM with agent tools
            llm_result: LLMCompletionOutput = await workflow.execute_activity(
                llm_completion,
                LLMCompletionInput(
                    provider=input.llm_provider,
                    model=input.llm_model,
                    messages=messages,
                    temperature=input.llm_temperature,
                    max_tokens=input.llm_max_tokens,
                    tools=tools if tools else None,
                ),
                start_to_close_timeout=timedelta(seconds=120),
            )

            # Check for tool calls
            if not llm_result.tool_calls:
                # No tool calls, return final response
                return AgentWorkflowOutput(
                    content=llm_result.content,
                    agent_id=input.agent_id,
                    agent_type=input.agent_type,
                    success=True,
                    metadata={
                        "model": llm_result.model,
                        "usage": llm_result.usage,
                        "iterations": iterations,
                        "tool_calls": tool_calls_made,
                        "agent_results": agent_results,
                        "mode": input.orchestrator_mode,
                    },
                )

            # Add assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": llm_result.content or "",
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in llm_result.tool_calls
                ],
            })

            # Execute tool calls
            for tc in llm_result.tool_calls:
                original_name = tool_name_map.get(tc.name, tc.name)
                workflow.logger.info(
                    f"Orchestrator executing: {original_name} (sanitized: {tc.name})"
                )

                if original_name.startswith("agent:"):
                    # Execute agent tool
                    agent_id = original_name.split(":", 1)[1]
                    agent_result: AgentToolExecutionOutput = await workflow.execute_activity(
                        execute_agent_as_tool,
                        AgentToolExecutionInput(
                            agent_id=agent_id,
                            query=tc.arguments.get("query", ""),
                            context={
                                "additional_context": tc.arguments.get("context", ""),
                            },
                            current_depth=0,
                            max_depth=input.orchestrator_max_depth,
                        ),
                        start_to_close_timeout=timedelta(seconds=300),
                    )
                    tool_result = {
                        "success": agent_result.success,
                        "content": agent_result.content,
                        "agent_id": agent_result.agent_id,
                        "error": agent_result.error,
                    }
                    agent_results.append({
                        "agent": original_name,
                        "result": tool_result,
                    })
                else:
                    # Execute regular tool
                    result: ToolExecutionOutput = await workflow.execute_activity(
                        execute_tool,
                        ToolExecutionInput(
                            tool_name=original_name,
                            arguments=tc.arguments,
                        ),
                        start_to_close_timeout=timedelta(seconds=60),
                    )
                    tool_result = {
                        "success": result.success,
                        "output": result.output,
                        "error": result.error,
                    }

                tool_calls_made.append({
                    "tool": original_name,
                    "args": tc.arguments,
                    "result": tool_result,
                })

                # Add tool result message
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result),
                    "tool_call_id": tc.id,
                })

        # Max iterations reached
        return AgentWorkflowOutput(
            content="Maximum orchestration iterations reached.",
            agent_id=input.agent_id,
            agent_type=input.agent_type,
            success=False,
            error="Max iterations",
            metadata={
                "tool_calls": tool_calls_made,
                "agent_results": agent_results,
                "iterations": iterations,
            },
        )

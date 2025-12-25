"""Agent Workflow - Main Temporal workflow for all agent types."""
import json
import re
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, List, Optional, Set

from temporalio import workflow
from temporalio.common import RetryPolicy

# =============================================================================
# Constants for workflow safety limits
# =============================================================================
MAX_WORKFLOW_STEPS = 100  # Maximum steps to execute (prevents infinite loops)
MAX_TEMPLATE_DEPTH = 5  # Maximum depth for template path resolution
MAX_RESULT_SIZE = 50000  # Maximum characters per step result
VALID_PATH_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")  # Valid path components

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
    from src.models.workflow_definition import (
        StepType,
        WorkflowDefinition,
        validate_workflow_definition,
    )


@dataclass
class AgentWorkflowInput:
    """Input for agent workflow."""

    agent_id: str
    agent_type: str
    user_input: str
    user_id: str  # Required for user-level analytics
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

    # Workflow definition (for WORKFLOW mode)
    # JSON structure: {"id": "...", "steps": [...], "entry_step": "..."}
    workflow_definition: Optional[Dict[str, Any]] = None


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
                user_id=input.user_id,
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
                user_id=input.user_id,
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
                    user_id=input.user_id,
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
                            user_id=input.user_id,
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
                    user_id=input.user_id,
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
                        ToolExecutionInput(tool_name=original_name, user_id=input.user_id, arguments=tc.arguments),
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
                user_id=input.user_id,
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
        """Handle OrchestratorAgent - supports multiple orchestration modes."""
        mode = input.orchestrator_mode or "llm_driven"

        if mode == "workflow":
            # Execute predefined workflow definition
            return await self._execute_workflow_definition(input)
        elif mode == "hybrid":
            # TODO: Implement hybrid mode (workflow + LLM can deviate)
            return await self._execute_llm_driven_orchestration(input)
        else:
            # Default: LLM-driven orchestration
            return await self._execute_llm_driven_orchestration(input)

    async def _execute_llm_driven_orchestration(
        self, input: AgentWorkflowInput
    ) -> AgentWorkflowOutput:
        """Execute LLM-driven orchestration where LLM decides which agents to call."""
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
                    user_id=input.user_id,
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
                            user_id=input.user_id,
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
                            user_id=input.user_id,
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

    # =========================================================================
    # WORKFLOW MODE - Execute predefined workflow definition
    # =========================================================================

    async def _execute_workflow_definition(
        self, input: AgentWorkflowInput
    ) -> AgentWorkflowOutput:
        """
        Execute a predefined workflow definition.

        Each step is executed as a Temporal activity for durability.
        Supports: agent, parallel, conditional, loop step types.

        Security features:
        - Validates workflow definition with Pydantic models
        - Limits max steps to prevent infinite loops
        - Tracks visited steps to detect cycles at runtime
        - Sanitizes template paths
        - Truncates large results
        """
        if not input.workflow_definition:
            raise ValueError("WORKFLOW mode requires workflow_definition")

        # Validate workflow definition with Pydantic model
        try:
            validated_def = validate_workflow_definition(input.workflow_definition)
        except ValueError as e:
            return AgentWorkflowOutput(
                content=f"Invalid workflow definition: {str(e)}",
                agent_id=input.agent_id,
                agent_type=input.agent_type,
                success=False,
                error=f"Validation error: {str(e)}",
                metadata={"mode": "workflow", "validation_error": str(e)},
            )

        # Use raw dict for execution (validated structure is guaranteed)
        definition = input.workflow_definition
        steps = definition.get("steps", [])

        # Build step index for quick lookup with order tracking
        steps_by_id: Dict[str, Dict[str, Any]] = {s["id"]: s for s in steps}
        step_order: Dict[str, int] = {s["id"]: i for i, s in enumerate(steps)}

        # Execution state
        step_results: Dict[str, Any] = {}
        steps_executed: List[str] = []
        visited_steps: Set[str] = set()  # Track visited to detect runtime cycles
        total_steps_executed = 0  # Safety counter

        # Context for template resolution
        context = {
            "user_input": input.user_input,
            "workflow": definition,
            **(definition.get("context", {})),
        }

        # Start from entry step or first step
        current_step_id = validated_def.entry_step or steps[0]["id"]

        workflow.logger.info(
            f"Starting workflow: {definition.get('id', 'unknown')}, "
            f"entry_step: {current_step_id}, total_steps: {len(steps)}"
        )

        while current_step_id:
            # Safety check: prevent infinite loops
            total_steps_executed += 1
            if total_steps_executed > MAX_WORKFLOW_STEPS:
                return AgentWorkflowOutput(
                    content=f"Workflow exceeded maximum steps ({MAX_WORKFLOW_STEPS})",
                    agent_id=input.agent_id,
                    agent_type=input.agent_type,
                    success=False,
                    error="Max workflow steps exceeded",
                    metadata={
                        "mode": "workflow",
                        "workflow_id": definition.get("id"),
                        "steps_executed": steps_executed,
                        "total_steps_executed": total_steps_executed,
                    },
                )
            step = steps_by_id.get(current_step_id)
            if not step:
                workflow.logger.error(f"Step not found: {current_step_id}")
                break

            step_type = step.get("type", "agent")
            workflow.logger.info(f"Executing step: {step['id']} (type: {step_type})")

            try:
                # ============================================================
                # AGENT STEP - Execute single agent
                # ============================================================
                if step_type == "agent":
                    resolved_input = self._resolve_template(
                        step.get("input", "${user_input}"),
                        step_results,
                        context
                    )

                    result: AgentToolExecutionOutput = await workflow.execute_activity(
                        execute_agent_as_tool,
                        AgentToolExecutionInput(
                            agent_id=step["agent_id"],
                            query=resolved_input,
                            user_id=input.user_id,
                            context={},
                            current_depth=0,
                            max_depth=input.orchestrator_max_depth,
                        ),
                        start_to_close_timeout=timedelta(seconds=step.get("timeout", 120)),
                        retry_policy=RetryPolicy(
                            maximum_attempts=step.get("retries", 0) + 1,
                            initial_interval=timedelta(seconds=1),
                            backoff_coefficient=2.0,
                            maximum_interval=timedelta(seconds=30),
                        ),
                    )

                    step_results[step["id"]] = {
                        "success": result.success,
                        "output": result.content,
                        "error": result.error,
                        "agent_id": result.agent_id,
                    }
                    steps_executed.append(step["id"])

                    # Handle errors
                    if not result.success:
                        on_error = step.get("on_error", "fail")
                        if on_error == "fail":
                            return AgentWorkflowOutput(
                                content=f"Workflow failed at step '{step['id']}': {result.error}",
                                agent_id=input.agent_id,
                                agent_type=input.agent_type,
                                success=False,
                                error=result.error,
                                metadata={
                                    "mode": "workflow",
                                    "workflow_id": definition.get("id"),
                                    "steps_executed": steps_executed,
                                    "step_results": step_results,
                                    "failed_step": step["id"],
                                },
                            )
                        elif on_error == "skip":
                            workflow.logger.warning(f"Skipping failed step: {step['id']}")
                        elif on_error in steps_by_id:
                            current_step_id = on_error
                            continue

                    current_step_id = self._get_next_step_id(step["id"], step_order)

                # ============================================================
                # PARALLEL STEP - Execute multiple agents concurrently
                # ============================================================
                elif step_type == "parallel":
                    branches = step.get("branches", [])
                    if not branches:
                        workflow.logger.warning(f"Parallel step {step['id']} has no branches")
                        current_step_id = self._get_next_step_id(step["id"], step_order)
                        continue

                    # Enforce max_parallel limit
                    max_parallel = input.orchestrator_max_parallel or 5
                    if len(branches) > max_parallel:
                        workflow.logger.warning(
                            f"Parallel step {step['id']} has {len(branches)} branches, "
                            f"limiting to {max_parallel}"
                        )
                        branches = branches[:max_parallel]

                    # Start all branch activities (Temporal handles true parallelism)
                    branch_tasks = []
                    for branch in branches:
                        resolved_input = self._resolve_template(
                            branch.get("input", "${user_input}"),
                            step_results,
                            context
                        )

                        task = workflow.execute_activity(
                            execute_agent_as_tool,
                            AgentToolExecutionInput(
                                agent_id=branch["agent_id"],
                                query=resolved_input,
                                user_id=input.user_id,
                                context={},
                                current_depth=0,
                                max_depth=input.orchestrator_max_depth,
                            ),
                            start_to_close_timeout=timedelta(seconds=branch.get("timeout", 120)),
                        )
                        branch_tasks.append((branch.get("id", branch["agent_id"]), task))

                    # Await all branches concurrently
                    branch_results = {}
                    for branch_id, task in branch_tasks:
                        result = await task
                        branch_results[branch_id] = {
                            "success": result.success,
                            "output": self._truncate_result(result.content),
                            "error": result.error,
                            "agent_id": result.agent_id,
                        }

                    # Aggregate results
                    aggregation = step.get("aggregation", "all")
                    aggregated = self._aggregate_parallel_results(branch_results, aggregation)

                    step_results[step["id"]] = {
                        "branches": branch_results,
                        "output": aggregated,
                    }
                    steps_executed.append(step["id"])

                    current_step_id = self._get_next_step_id(step["id"], step_order)

                # ============================================================
                # CONDITIONAL STEP - Route based on condition
                # ============================================================
                elif step_type == "conditional":
                    condition_source = step.get("condition_source", "")
                    value = self._resolve_template(condition_source, step_results, context)

                    # Clean up value for matching (normalize whitespace and case)
                    value = value.strip().lower()

                    # Support both 'branches' and 'conditional_branches' field names
                    branches = step.get("conditional_branches") or step.get("branches", {})
                    next_step = None

                    # Try to match branch (case-insensitive, with partial matching)
                    for branch_key, branch_target in branches.items():
                        branch_key_lower = branch_key.lower()
                        # Exact match or value contains branch key
                        if branch_key_lower == value or branch_key_lower in value:
                            next_step = branch_target
                            break

                    # Use default if no match
                    if not next_step:
                        next_step = step.get("default")

                    step_results[step["id"]] = {
                        "condition_value": value,
                        "selected_branch": next_step,
                    }
                    steps_executed.append(step["id"])

                    if next_step:
                        current_step_id = next_step
                    else:
                        workflow.logger.warning(
                            f"Conditional step {step['id']} has no matching branch for '{value}'"
                        )
                        current_step_id = self._get_next_step_id(step["id"], step_order)

                # ============================================================
                # LOOP STEP - Iterate until condition met
                # ============================================================
                elif step_type == "loop":
                    max_iterations = min(step.get("max_iterations", 5), 20)  # Cap at 20
                    exit_condition = step.get("exit_condition", "false")
                    inner_steps = step.get("steps", [])

                    if not inner_steps:
                        workflow.logger.warning(f"Loop step {step['id']} has no inner steps")
                        current_step_id = self._get_next_step_id(step["id"], step_order)
                        continue

                    loop_results = []
                    last_inner_output = ""

                    for iteration in range(max_iterations):
                        workflow.logger.info(
                            f"Loop '{step['id']}' iteration {iteration + 1}/{max_iterations}"
                        )

                        iteration_results = {}

                        # Execute inner steps
                        for inner_step in inner_steps:
                            resolved_input = self._resolve_template(
                                inner_step.get("input", "${user_input}"),
                                step_results,
                                {**context, "loop_iteration": iteration}
                            )

                            result = await workflow.execute_activity(
                                execute_agent_as_tool,
                                AgentToolExecutionInput(
                                    agent_id=inner_step["agent_id"],
                                    query=resolved_input,
                                    user_id=input.user_id,
                                    context={},
                                    current_depth=0,
                                    max_depth=input.orchestrator_max_depth,
                                ),
                                start_to_close_timeout=timedelta(
                                    seconds=inner_step.get("timeout", 120)
                                ),
                            )

                            inner_step_result = {
                                "success": result.success,
                                "output": self._truncate_result(result.content),
                                "iteration": iteration,
                            }
                            # Use unique key per iteration to avoid collision
                            unique_key = f"{inner_step['id']}_iter_{iteration}"
                            step_results[unique_key] = inner_step_result
                            # Also store latest under original ID for template access
                            step_results[inner_step["id"]] = inner_step_result
                            iteration_results[inner_step["id"]] = inner_step_result
                            last_inner_output = result.content

                        loop_results.append({
                            "iteration": iteration,
                            "results": iteration_results,
                        })

                        # Check exit condition before next iteration
                        resolved_condition = self._resolve_template(
                            exit_condition, step_results, context
                        )

                        if self._evaluate_condition(resolved_condition):
                            workflow.logger.info(
                                f"Loop exit condition met at iteration {iteration + 1}"
                            )
                            break

                    step_results[step["id"]] = {
                        "iterations_completed": len(loop_results),
                        "results": loop_results,
                        "output": last_inner_output,  # Use last actual output
                    }
                    steps_executed.append(step["id"])

                    current_step_id = self._get_next_step_id(step["id"], step_order)

                else:
                    workflow.logger.warning(f"Unknown step type: {step_type}")
                    current_step_id = self._get_next_step_id(step["id"], step_order)

            except Exception as e:
                workflow.logger.error(f"Error executing step {step['id']}: {e}")
                return AgentWorkflowOutput(
                    content=f"Workflow error at step '{step['id']}': {str(e)}",
                    agent_id=input.agent_id,
                    agent_type=input.agent_type,
                    success=False,
                    error=str(e),
                    metadata={
                        "mode": "workflow",
                        "workflow_id": definition.get("id"),
                        "steps_executed": steps_executed,
                        "step_results": step_results,
                        "failed_step": step["id"],
                    },
                )

        # ================================================================
        # WORKFLOW COMPLETE
        # ================================================================

        # Handle empty workflow (no steps executed)
        if not steps_executed:
            workflow.logger.warning(
                f"Workflow completed with no steps executed: {definition.get('id', 'unknown')}"
            )
            return AgentWorkflowOutput(
                content="Workflow completed but no steps were executed.",
                agent_id=input.agent_id,
                agent_type=input.agent_type,
                success=False,
                error="No steps executed",
                metadata={
                    "mode": "workflow",
                    "workflow_id": definition.get("id"),
                    "steps_executed": [],
                },
            )

        final_step_id = steps_executed[-1]
        final_result = step_results.get(final_step_id, {})
        final_output = final_result.get("output", "")

        # Convert to string if needed (use compact JSON for internal storage)
        if not isinstance(final_output, str):
            final_output = json.dumps(final_output)

        workflow.logger.info(
            f"Workflow completed: {definition.get('id', 'unknown')}, "
            f"steps_executed: {len(steps_executed)}"
        )

        return AgentWorkflowOutput(
            content=final_output,
            agent_id=input.agent_id,
            agent_type=input.agent_type,
            success=True,
            metadata={
                "mode": "workflow",
                "workflow_id": definition.get("id"),
                "workflow_name": definition.get("name"),
                "steps_executed": steps_executed,
                "step_results": step_results,
            },
        )

    # =========================================================================
    # WORKFLOW HELPER METHODS
    # =========================================================================

    def _resolve_template(
        self,
        template: str,
        step_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Resolve ${...} placeholders in template string.

        Supports:
        - ${user_input} - original user input
        - ${steps.step_id.output} - output from a previous step
        - ${steps.step_id.field} - specific field from step result
        - ${context.key} - context variable
        - ${loop_iteration} - current loop iteration

        Security: Limits path depth and validates path components.
        """
        def replace_match(match: re.Match) -> str:
            path = match.group(1)
            # Limit path length to prevent abuse
            if len(path) > 200:
                return ""
            return self._get_path_value(path, step_results, context)

        return re.sub(r'\$\{([^}]+)\}', replace_match, template)

    def _get_path_value(
        self,
        path: str,
        step_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Get value from dot-notation path like 'steps.fetch.output'.

        Security: Limits depth, validates path components, no attribute access.
        """
        parts = path.split('.')

        # Limit path depth
        if len(parts) > MAX_TEMPLATE_DEPTH:
            return ""

        # Validate all path components (only allow safe characters)
        for part in parts:
            # Allow alphanumeric, underscore, hyphen (for step IDs like "step-1")
            if not re.match(r'^[a-zA-Z0-9_-]+$', part):
                return ""

        if parts[0] == "steps" and len(parts) >= 2:
            step_id = parts[1]
            result = step_results.get(step_id, {})
            # Navigate remaining path (dict access only, no getattr)
            for part in parts[2:]:
                if isinstance(result, dict):
                    result = result.get(part, "")
                else:
                    result = ""
                    break
            return str(result) if result else ""

        elif parts[0] == "context" and len(parts) >= 2:
            key = parts[1]
            value = context.get(key, "")
            return str(value) if value else ""

        elif parts[0] == "user_input":
            return context.get("user_input", "")

        elif parts[0] == "loop_iteration":
            return str(context.get("loop_iteration", 0))

        return ""

    def _get_next_step_id(
        self,
        current_id: str,
        step_order: Dict[str, int]
    ) -> Optional[str]:
        """
        Get the next sequential step ID, or None if at end.

        Uses pre-built step_order dict for O(1) lookup instead of O(n) list search.
        """
        current_idx = step_order.get(current_id)
        if current_idx is None:
            return None

        # Find step with next index
        next_idx = current_idx + 1
        for step_id, idx in step_order.items():
            if idx == next_idx:
                return step_id
        return None

    def _aggregate_parallel_results(
        self,
        results: Dict[str, Any],
        strategy: str
    ) -> Any:
        """Aggregate results from parallel branches."""
        if strategy == "all":
            # Combine all successful outputs
            outputs = []
            for branch_id, r in results.items():
                if r.get("success") and r.get("output"):
                    outputs.append(f"[{branch_id}]\n{r['output']}")
            return "\n\n---\n\n".join(outputs)

        elif strategy == "first":
            # Return first successful result
            for r in results.values():
                if r.get("success"):
                    return r.get("output", "")
            return ""

        elif strategy == "merge":
            # Merge into single dict (for structured outputs)
            merged = {}
            for branch_id, r in results.items():
                output = r.get("output")
                if isinstance(output, dict):
                    merged.update(output)
                elif isinstance(output, str):
                    try:
                        parsed = json.loads(output)
                        if isinstance(parsed, dict):
                            merged.update(parsed)
                    except (json.JSONDecodeError, TypeError):
                        merged[branch_id] = output
                else:
                    merged[branch_id] = output
            return merged

        elif strategy == "best":
            # For now, return first successful (LLM selection would be async)
            for r in results.values():
                if r.get("success"):
                    return r.get("output", "")
            return ""

        # Default: return all results as dict
        return {k: v.get("output") for k, v in results.items()}

    def _truncate_result(self, content: Optional[str]) -> str:
        """Truncate result to prevent Temporal history exhaustion."""
        if not content:
            return ""
        if len(content) > MAX_RESULT_SIZE:
            return content[:MAX_RESULT_SIZE] + "\n... [truncated]"
        return content

    def _evaluate_condition(self, condition: str) -> bool:
        """
        Safely evaluate a simple condition expression.

        Supports:
        - Boolean literals: "true", "false"
        - Simple comparisons: "5 > 3", "'done' == 'done'"
        - Operators: ==, !=, >=, <=, >, <

        Security:
        - No eval() or exec()
        - Limited input length
        - Explicit operator matching only
        - Type-safe comparisons
        """
        if not condition or not isinstance(condition, str):
            return False

        # Limit input length to prevent abuse
        if len(condition) > 500:
            return False

        condition = condition.strip()

        # Handle simple boolean values
        condition_lower = condition.lower()
        if condition_lower == "true":
            return True
        if condition_lower == "false":
            return False

        # Handle simple comparisons with explicit pattern
        # Pattern is intentionally restrictive for security
        comparison_pattern = r'^(["\']?[^"\'<>=!]+["\']?)\s*(==|!=|>=|<=|>|<)\s*(["\']?[^"\'<>=!]+["\']?)$'

        try:
            match = re.match(comparison_pattern, condition, re.DOTALL)
        except re.error:
            # Invalid regex input
            return False

        if not match:
            return False

        left_raw, op, right_raw = match.groups()
        left_raw = left_raw.strip()
        right_raw = right_raw.strip()

        # Parse values with explicit type handling
        def parse_value(val: str):
            """Parse a value string into a typed value."""
            val = val.strip()
            # Remove quotes if present
            if (val.startswith('"') and val.endswith('"')) or \
               (val.startswith("'") and val.endswith("'")):
                return val[1:-1]
            # Try numeric conversion
            try:
                if '.' in val:
                    return float(val)
                return int(val)
            except ValueError:
                return val

        left_val = parse_value(left_raw)
        right_val = parse_value(right_raw)

        # Type-safe comparisons
        try:
            if op == "==":
                return left_val == right_val
            elif op == "!=":
                return left_val != right_val
            elif op in (">=", "<=", ">", "<"):
                # Numeric comparisons require compatible types
                if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
                    if op == ">=":
                        return left_val >= right_val
                    elif op == "<=":
                        return left_val <= right_val
                    elif op == ">":
                        return left_val > right_val
                    elif op == "<":
                        return left_val < right_val
                # String comparisons (lexicographic)
                elif isinstance(left_val, str) and isinstance(right_val, str):
                    if op == ">=":
                        return left_val >= right_val
                    elif op == "<=":
                        return left_val <= right_val
                    elif op == ">":
                        return left_val > right_val
                    elif op == "<":
                        return left_val < right_val
                # Mixed types - not comparable
                return False
        except (TypeError, ValueError):
            return False

        return False

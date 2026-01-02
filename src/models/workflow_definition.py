"""Workflow definition models with validation."""
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class SuggestedAgent(BaseModel):
    """AI's suggestion for an agent to fulfill a step (for draft workflows)."""
    name: str = Field(..., description="Suggested agent name")
    description: Optional[str] = Field(None, description="Description of what the agent does")
    goal: str = Field(..., description="What this agent should accomplish")
    model: Optional[str] = Field(None, description="LLM model to use (e.g., gpt-4o)")
    required_mcps: List[str] = Field(default_factory=list, description="MCP servers needed")
    suggested_tools: List[str] = Field(default_factory=list, description="Tools the agent should use")


class StepType(str, Enum):
    """Types of workflow steps."""

    AGENT = "agent"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    APPROVAL = "approval"  # Human-in-the-loop approval gate


class ErrorHandling(str, Enum):
    """How to handle step errors."""

    FAIL = "fail"  # Stop workflow on error
    SKIP = "skip"  # Skip step and continue


class AggregationType(str, Enum):
    """How to aggregate parallel results."""

    ALL = "all"
    FIRST = "first"
    MERGE = "merge"
    BEST = "best"


# Regex pattern for valid IDs (alphanumeric, hyphens, underscores)
ID_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_-]{0,99}$"


class ParallelBranch(BaseModel):
    """A branch in a parallel step."""

    id: Optional[str] = Field(None, pattern=ID_PATTERN)
    agent_id: str = Field(..., pattern=ID_PATTERN)
    input: str = Field(default="${user_input}", max_length=10000)
    timeout: int = Field(default=120, ge=1, le=600)


class LoopInnerStep(BaseModel):
    """A step inside a loop."""

    id: str = Field(..., pattern=ID_PATTERN)
    agent_id: str = Field(..., pattern=ID_PATTERN)
    input: str = Field(default="${user_input}", max_length=10000)
    timeout: int = Field(default=120, ge=1, le=600)


class LoopMode(str, Enum):
    """Mode for loop iteration."""

    COUNT = "count"  # Iterate a fixed number of times
    FOREACH = "foreach"  # Iterate over a collection
    UNTIL = "until"  # Iterate until condition is met


class WorkflowStep(BaseModel):
    """A single step in a workflow definition."""

    id: str = Field(..., pattern=ID_PATTERN, description="Unique step identifier")
    type: StepType = Field(default=StepType.AGENT, description="Step type")
    name: Optional[str] = Field(None, max_length=200, description="Human-readable step name")

    # Agent step fields
    agent_id: Optional[str] = Field(None, pattern=ID_PATTERN)
    suggested_agent: Optional[SuggestedAgent] = Field(
        None,
        description="AI suggestion for agent (for draft workflows without agent_id)"
    )
    input: Optional[str] = Field(None, max_length=10000)
    timeout: int = Field(default=120, ge=1, le=600)
    retries: int = Field(default=0, ge=0, le=5)
    on_error: Optional[str] = Field(
        default="fail",
        description="Error handling: 'fail', 'skip', or step_id to jump to",
    )

    # Parallel step fields
    branches: Optional[List[ParallelBranch]] = Field(None, max_length=10)
    aggregation: AggregationType = Field(default=AggregationType.ALL)

    # Conditional step fields
    condition_source: Optional[str] = Field(None, max_length=1000)
    # branches dict is reused - keys are condition values, values are step IDs
    conditional_branches: Optional[Dict[str, str]] = Field(None)
    default: Optional[str] = Field(None, pattern=ID_PATTERN)

    # Loop step fields
    loop_mode: Optional[LoopMode] = Field(default=LoopMode.COUNT, description="Loop mode")
    max_iterations: int = Field(default=5, ge=1, le=100)
    over: Optional[str] = Field(
        None, max_length=10000,
        description="Expression to iterate over. Can be JSON array, ${steps.X.output}, or template variable"
    )
    item_variable: Optional[str] = Field(
        default="item",
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        description="Variable name for current item in foreach mode (accessible as ${loop.item})"
    )
    exit_condition: Optional[str] = Field(
        None, max_length=1000,
        description="Expression that when 'true'/'done'/'complete' exits the loop"
    )
    break_condition: Optional[str] = Field(
        None, max_length=1000,
        description="Expression to break loop early (evaluated after each iteration)"
    )
    continue_condition: Optional[str] = Field(
        None, max_length=1000,
        description="Expression to skip to next iteration (evaluated before each step)"
    )
    collect_results: bool = Field(
        default=True,
        description="Whether to collect all iteration results into an array"
    )
    steps: Optional[List[LoopInnerStep]] = Field(None, max_length=10)

    # Approval step fields (human-in-the-loop)
    approval_message: Optional[str] = Field(
        None, max_length=5000,
        description="Message to display to approvers explaining what needs approval"
    )
    approvers: Optional[List[str]] = Field(
        None, max_length=50,
        description="List of user IDs, emails, or role patterns (e.g., 'role:admin') who can approve"
    )
    required_approvals: int = Field(
        default=1, ge=1, le=10,
        description="Number of approvals required (1 for single approver)"
    )
    approval_timeout_seconds: Optional[int] = Field(
        None, ge=60, le=604800,  # 1 min to 7 days
        description="Timeout in seconds for approval (None = no timeout)"
    )
    on_reject: Optional[str] = Field(
        default="fail",
        description="Action on rejection: 'fail', 'skip', or step_id to jump to"
    )

    @field_validator("on_error")
    @classmethod
    def validate_on_error(cls, v: Optional[str]) -> str:
        if v is None:
            return "fail"
        if v in ("fail", "skip"):
            return v
        # Otherwise it should be a step ID - will be validated at workflow level
        return v

    @model_validator(mode="after")
    def validate_step_type_fields(self) -> "WorkflowStep":
        """Validate that required fields are present for each step type."""
        if self.type == StepType.AGENT:
            # Allow either agent_id (ready) or suggested_agent (draft)
            if not self.agent_id and not self.suggested_agent:
                raise ValueError(f"Step '{self.id}': agent step requires agent_id or suggested_agent")

        elif self.type == StepType.PARALLEL:
            if not self.branches or len(self.branches) == 0:
                raise ValueError(f"Step '{self.id}': parallel step requires branches")
            if len(self.branches) > 10:
                raise ValueError(f"Step '{self.id}': max 10 parallel branches allowed")

        elif self.type == StepType.CONDITIONAL:
            if not self.condition_source:
                raise ValueError(
                    f"Step '{self.id}': conditional step requires condition_source"
                )
            if not self.conditional_branches:
                raise ValueError(
                    f"Step '{self.id}': conditional step requires conditional_branches"
                )

        elif self.type == StepType.LOOP:
            if not self.steps or len(self.steps) == 0:
                raise ValueError(f"Step '{self.id}': loop step requires inner steps")
            # Validate foreach mode requires 'over' expression
            if self.loop_mode == LoopMode.FOREACH and not self.over:
                raise ValueError(
                    f"Step '{self.id}': foreach loop mode requires 'over' expression"
                )
            # Validate until mode requires exit_condition
            if self.loop_mode == LoopMode.UNTIL and not self.exit_condition:
                raise ValueError(
                    f"Step '{self.id}': until loop mode requires 'exit_condition'"
                )

        elif self.type == StepType.APPROVAL:
            if not self.approval_message:
                raise ValueError(
                    f"Step '{self.id}': approval step requires approval_message"
                )
            # Approvers are optional - if not set, workflow creator can approve

        return self


class WorkflowDefinition(BaseModel):
    """Complete workflow definition with validation."""

    id: str = Field(..., pattern=ID_PATTERN, description="Workflow identifier")
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    steps: List[WorkflowStep] = Field(..., min_length=1, max_length=50)
    entry_step: Optional[str] = Field(None, pattern=ID_PATTERN)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_workflow(self) -> "WorkflowDefinition":
        """Validate workflow structure and references."""
        step_ids = {step.id for step in self.steps}

        # Validate entry_step exists
        if self.entry_step and self.entry_step not in step_ids:
            raise ValueError(f"entry_step '{self.entry_step}' not found in steps")

        # Validate all step references
        for step in self.steps:
            # Validate on_error references
            if step.on_error and step.on_error not in ("fail", "skip"):
                if step.on_error not in step_ids:
                    raise ValueError(
                        f"Step '{step.id}': on_error references unknown step '{step.on_error}'"
                    )

            # Validate conditional branch targets
            if step.type == StepType.CONDITIONAL and step.conditional_branches:
                for target in step.conditional_branches.values():
                    if target not in step_ids:
                        raise ValueError(
                            f"Step '{step.id}': branch targets unknown step '{target}'"
                        )
                if step.default and step.default not in step_ids:
                    raise ValueError(
                        f"Step '{step.id}': default targets unknown step '{step.default}'"
                    )

        # Check for duplicate step IDs
        if len(step_ids) != len(self.steps):
            raise ValueError("Duplicate step IDs found")

        # Detect cycles (simple check - more sophisticated would use graph algorithms)
        self._detect_cycles()

        return self

    def _detect_cycles(self) -> None:
        """Detect cycles in step references (basic check)."""
        # Build adjacency list
        graph: Dict[str, List[str]] = {step.id: [] for step in self.steps}

        for i, step in enumerate(self.steps):
            # Add edge to next sequential step
            if i + 1 < len(self.steps):
                graph[step.id].append(self.steps[i + 1].id)

            # Add edge from on_error
            if step.on_error and step.on_error not in ("fail", "skip"):
                graph[step.id].append(step.on_error)

            # Add edges from conditional branches
            if step.type == StepType.CONDITIONAL and step.conditional_branches:
                for target in step.conditional_branches.values():
                    graph[step.id].append(target)
                if step.default:
                    graph[step.id].append(step.default)

        # DFS to detect cycles
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in graph}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in graph[node]:
                if color[neighbor] == GRAY:
                    return True  # Back edge = cycle
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        for node in graph:
            if color[node] == WHITE:
                if dfs(node):
                    raise ValueError(
                        f"Cycle detected in workflow starting from step '{node}'"
                    )

    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by its ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def is_ready_to_run(self) -> bool:
        """Check if all agent steps have agent_id (not just suggested_agent)."""
        for step in self.steps:
            if step.type == StepType.AGENT:
                if not step.agent_id:
                    return False
            elif step.type == StepType.PARALLEL and step.branches:
                for branch in step.branches:
                    if not branch.agent_id:
                        return False
        return True

    def get_draft_steps(self) -> List[WorkflowStep]:
        """Get all steps that have suggested_agent but no agent_id."""
        return [
            step for step in self.steps
            if step.type == StepType.AGENT and not step.agent_id and step.suggested_agent
        ]

    def get_missing_agent_ids(self) -> List[str]:
        """Get step IDs that need agents created."""
        return [step.id for step in self.get_draft_steps()]


def validate_workflow_definition(data: Dict[str, Any]) -> WorkflowDefinition:
    """
    Validate and parse a workflow definition dict.

    Args:
        data: Raw workflow definition dict

    Returns:
        Validated WorkflowDefinition

    Raises:
        ValueError: If validation fails
    """
    # Handle conditional branches field name mapping
    if "steps" in data:
        for step in data["steps"]:
            # Map 'branches' to 'conditional_branches' for conditional steps
            if step.get("type") == "conditional" and "branches" in step:
                step["conditional_branches"] = step.pop("branches")

    return WorkflowDefinition.model_validate(data)

"""Workflow constants for safety limits and validation."""
import re

# =============================================================================
# Constants for workflow safety limits
# =============================================================================

# Maximum steps to execute (prevents infinite loops)
MAX_WORKFLOW_STEPS = 100

# Maximum depth for template path resolution
MAX_TEMPLATE_DEPTH = 5

# Maximum characters per step result
MAX_RESULT_SIZE = 50000

# Valid path components for template resolution
VALID_PATH_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Maximum iterations for tool execution loops
MAX_TOOL_ITERATIONS = 10

# Maximum iterations for orchestrator loops
MAX_ORCHESTRATOR_ITERATIONS = 15

# Keywords that indicate an action tool (vs. query tool)
ACTION_TOOL_KEYWORDS = ["send", "create", "update", "delete", "write", "post"]

"""Calculator tool for basic math operations."""
import ast
import operator
from typing import Any

from src.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


class CalculatorTool(BaseTool):
    """Safe calculator tool for math expressions."""

    # Allowed operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    @property
    def definition(self) -> ToolDefinition:
        """Return calculator tool definition."""
        return ToolDefinition(
            name="calculator",
            description="Evaluate mathematical expressions. Supports +, -, *, /, ** operators.",
            parameters=[
                ToolParameter(
                    name="expression",
                    type="string",
                    description="The math expression to evaluate, e.g., '2 + 2' or '(5 * 3) / 2'",
                    required=True,
                ),
            ],
        )

    def _eval_node(self, node: ast.AST) -> float:
        """Safely evaluate an AST node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant: {node.value}")

        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(left, right)

        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(operand)

        raise ValueError(f"Unsupported node type: {type(node).__name__}")

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the calculator."""
        expression = kwargs.get("expression", "")

        if not expression:
            return ToolResult(
                success=False,
                output=None,
                error="Expression is required",
            )

        try:
            # Parse expression
            tree = ast.parse(expression, mode="eval")
            result = self._eval_node(tree.body)

            return ToolResult(
                success=True,
                output=result,
            )
        except (ValueError, SyntaxError) as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid expression: {str(e)}",
            )
        except ZeroDivisionError:
            return ToolResult(
                success=False,
                output=None,
                error="Division by zero",
            )

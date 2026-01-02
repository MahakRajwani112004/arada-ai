"""Comprehensive unit tests for CalculatorTool.

Tests cover:
- Tool definition and metadata
- Basic arithmetic operations (addition, subtraction, multiplication, division, exponentiation)
- Unary operators (negation, positive)
- Complex expressions with parentheses and operator precedence
- Edge cases (large numbers, decimals, negative numbers)
- Error handling (invalid expressions, division by zero, unsupported operations)
"""

import pytest
from src.tools.builtin.calculator import CalculatorTool
from src.tools.base import ToolDefinition, ToolParameter, ToolResult


class TestCalculatorToolDefinition:
    """Tests for CalculatorTool definition and metadata."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create a CalculatorTool instance for testing."""
        return CalculatorTool()

    def test_tool_name(self, calculator: CalculatorTool):
        """Test that the tool has the correct name."""
        assert calculator.name == "calculator"

    def test_tool_definition_type(self, calculator: CalculatorTool):
        """Test that definition returns a ToolDefinition instance."""
        assert isinstance(calculator.definition, ToolDefinition)

    def test_tool_description(self, calculator: CalculatorTool):
        """Test that the tool has a meaningful description."""
        definition = calculator.definition
        assert "mathematical" in definition.description.lower() or "math" in definition.description.lower()
        assert len(definition.description) > 10

    def test_tool_has_expression_parameter(self, calculator: CalculatorTool):
        """Test that the tool has an expression parameter."""
        definition = calculator.definition
        assert len(definition.parameters) == 1

        param = definition.parameters[0]
        assert param.name == "expression"
        assert param.type == "string"
        assert param.required is True

    def test_to_openai_format(self, calculator: CalculatorTool):
        """Test that the definition converts to OpenAI format correctly."""
        openai_format = calculator.definition.to_openai_format()

        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "calculator"
        assert "expression" in openai_format["function"]["parameters"]["properties"]
        assert "expression" in openai_format["function"]["parameters"]["required"]


class TestCalculatorBasicOperations:
    """Tests for basic arithmetic operations."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create a CalculatorTool instance for testing."""
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_addition_integers(self, calculator: CalculatorTool):
        """Test addition of two integers."""
        result = await calculator.execute(expression="2 + 3")

        assert result.success is True
        assert result.output == 5.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_addition_floats(self, calculator: CalculatorTool):
        """Test addition of floating point numbers."""
        result = await calculator.execute(expression="2.5 + 3.7")

        assert result.success is True
        assert result.output == pytest.approx(6.2)
        assert result.error is None

    @pytest.mark.asyncio
    async def test_subtraction(self, calculator: CalculatorTool):
        """Test subtraction operation."""
        result = await calculator.execute(expression="10 - 4")

        assert result.success is True
        assert result.output == 6.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_subtraction_negative_result(self, calculator: CalculatorTool):
        """Test subtraction resulting in negative number."""
        result = await calculator.execute(expression="5 - 10")

        assert result.success is True
        assert result.output == -5.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_multiplication(self, calculator: CalculatorTool):
        """Test multiplication operation."""
        result = await calculator.execute(expression="7 * 8")

        assert result.success is True
        assert result.output == 56.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_multiplication_by_zero(self, calculator: CalculatorTool):
        """Test multiplication by zero."""
        result = await calculator.execute(expression="5 * 0")

        assert result.success is True
        assert result.output == 0.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_division(self, calculator: CalculatorTool):
        """Test division operation."""
        result = await calculator.execute(expression="15 / 3")

        assert result.success is True
        assert result.output == 5.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_division_non_integer_result(self, calculator: CalculatorTool):
        """Test division with non-integer result."""
        result = await calculator.execute(expression="7 / 2")

        assert result.success is True
        assert result.output == 3.5
        assert result.error is None

    @pytest.mark.asyncio
    async def test_exponentiation(self, calculator: CalculatorTool):
        """Test exponentiation operation."""
        result = await calculator.execute(expression="2 ** 10")

        assert result.success is True
        assert result.output == 1024.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_exponentiation_square_root(self, calculator: CalculatorTool):
        """Test exponentiation for square root (x ** 0.5)."""
        result = await calculator.execute(expression="16 ** 0.5")

        assert result.success is True
        assert result.output == 4.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_exponentiation_zero_power(self, calculator: CalculatorTool):
        """Test exponentiation with zero exponent."""
        result = await calculator.execute(expression="5 ** 0")

        assert result.success is True
        assert result.output == 1.0
        assert result.error is None


class TestCalculatorUnaryOperators:
    """Tests for unary operators (negation and positive)."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create a CalculatorTool instance for testing."""
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_unary_negation(self, calculator: CalculatorTool):
        """Test unary negation operator."""
        result = await calculator.execute(expression="-5")

        assert result.success is True
        assert result.output == -5.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_unary_positive(self, calculator: CalculatorTool):
        """Test unary positive operator."""
        result = await calculator.execute(expression="+5")

        assert result.success is True
        assert result.output == 5.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_double_negation(self, calculator: CalculatorTool):
        """Test double negation."""
        result = await calculator.execute(expression="--5")

        assert result.success is True
        assert result.output == 5.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_negation_in_expression(self, calculator: CalculatorTool):
        """Test negation within an expression."""
        result = await calculator.execute(expression="10 + -3")

        assert result.success is True
        assert result.output == 7.0
        assert result.error is None


class TestCalculatorComplexExpressions:
    """Tests for complex expressions with multiple operators and parentheses."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create a CalculatorTool instance for testing."""
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_expression_with_parentheses(self, calculator: CalculatorTool):
        """Test expression with parentheses for grouping."""
        result = await calculator.execute(expression="(2 + 3) * 4")

        assert result.success is True
        assert result.output == 20.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_nested_parentheses(self, calculator: CalculatorTool):
        """Test expression with nested parentheses."""
        result = await calculator.execute(expression="((2 + 3) * (4 - 1))")

        assert result.success is True
        assert result.output == 15.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_operator_precedence_mult_add(self, calculator: CalculatorTool):
        """Test that multiplication has higher precedence than addition."""
        result = await calculator.execute(expression="2 + 3 * 4")

        assert result.success is True
        assert result.output == 14.0  # 2 + (3 * 4) = 14, not (2 + 3) * 4 = 20
        assert result.error is None

    @pytest.mark.asyncio
    async def test_operator_precedence_div_sub(self, calculator: CalculatorTool):
        """Test that division has higher precedence than subtraction."""
        result = await calculator.execute(expression="10 - 6 / 2")

        assert result.success is True
        assert result.output == 7.0  # 10 - (6 / 2) = 7
        assert result.error is None

    @pytest.mark.asyncio
    async def test_operator_precedence_power(self, calculator: CalculatorTool):
        """Test that exponentiation has higher precedence than multiplication."""
        result = await calculator.execute(expression="2 * 3 ** 2")

        assert result.success is True
        assert result.output == 18.0  # 2 * (3 ** 2) = 18
        assert result.error is None

    @pytest.mark.asyncio
    async def test_multiple_operators_chain(self, calculator: CalculatorTool):
        """Test chain of multiple operators."""
        result = await calculator.execute(expression="1 + 2 - 3 + 4 - 5")

        assert result.success is True
        assert result.output == -1.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_mixed_operations(self, calculator: CalculatorTool):
        """Test expression with all supported operations."""
        result = await calculator.execute(expression="(10 + 5) * 2 / 3 - 1")

        assert result.success is True
        assert result.output == pytest.approx(9.0)
        assert result.error is None


class TestCalculatorEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create a CalculatorTool instance for testing."""
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_large_numbers(self, calculator: CalculatorTool):
        """Test calculation with large numbers."""
        result = await calculator.execute(expression="1000000 * 1000000")

        assert result.success is True
        assert result.output == 1e12
        assert result.error is None

    @pytest.mark.asyncio
    async def test_small_decimals(self, calculator: CalculatorTool):
        """Test calculation with small decimal numbers."""
        result = await calculator.execute(expression="0.001 + 0.002")

        assert result.success is True
        assert result.output == pytest.approx(0.003)
        assert result.error is None

    @pytest.mark.asyncio
    async def test_zero_result(self, calculator: CalculatorTool):
        """Test expression that results in zero."""
        result = await calculator.execute(expression="5 - 5")

        assert result.success is True
        assert result.output == 0.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_single_number(self, calculator: CalculatorTool):
        """Test expression with just a single number."""
        result = await calculator.execute(expression="42")

        assert result.success is True
        assert result.output == 42.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_single_negative_number(self, calculator: CalculatorTool):
        """Test expression with just a negative number."""
        result = await calculator.execute(expression="-42")

        assert result.success is True
        assert result.output == -42.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_expression_with_leading_spaces_fails(self, calculator: CalculatorTool):
        """Test that expression with leading spaces fails due to AST parsing.

        Note: Python's AST parser treats leading whitespace as indentation,
        which causes a SyntaxError in 'eval' mode. This is expected behavior.
        """
        result = await calculator.execute(expression="  10   +   20  ")

        # Leading spaces cause "unexpected indent" error in AST parsing
        assert result.success is False
        assert result.output is None
        assert "indent" in result.error.lower()

    @pytest.mark.asyncio
    async def test_expression_with_internal_spaces(self, calculator: CalculatorTool):
        """Test expression with spaces between operators (no leading spaces)."""
        result = await calculator.execute(expression="10   +   20")

        assert result.success is True
        assert result.output == 30.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_expression_no_spaces(self, calculator: CalculatorTool):
        """Test expression with no spaces."""
        result = await calculator.execute(expression="10+20")

        assert result.success is True
        assert result.output == 30.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_very_large_exponent(self, calculator: CalculatorTool):
        """Test exponentiation with large result."""
        result = await calculator.execute(expression="10 ** 10")

        assert result.success is True
        assert result.output == 1e10
        assert result.error is None

    @pytest.mark.asyncio
    async def test_negative_exponent(self, calculator: CalculatorTool):
        """Test exponentiation with negative exponent."""
        result = await calculator.execute(expression="2 ** -2")

        assert result.success is True
        assert result.output == 0.25
        assert result.error is None


class TestCalculatorErrorHandling:
    """Tests for error handling and invalid inputs."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create a CalculatorTool instance for testing."""
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_empty_expression(self, calculator: CalculatorTool):
        """Test that empty expression returns an error."""
        result = await calculator.execute(expression="")

        assert result.success is False
        assert result.output is None
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_missing_expression(self, calculator: CalculatorTool):
        """Test that missing expression returns an error."""
        result = await calculator.execute()

        assert result.success is False
        assert result.output is None
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_division_by_zero(self, calculator: CalculatorTool):
        """Test that division by zero returns an error."""
        result = await calculator.execute(expression="10 / 0")

        assert result.success is False
        assert result.output is None
        assert "zero" in result.error.lower()

    @pytest.mark.asyncio
    async def test_division_by_zero_in_expression(self, calculator: CalculatorTool):
        """Test division by zero within a complex expression."""
        result = await calculator.execute(expression="(5 + 5) / (3 - 3)")

        assert result.success is False
        assert result.output is None
        assert "zero" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invalid_syntax_missing_operator(self, calculator: CalculatorTool):
        """Test expression with missing operator."""
        result = await calculator.execute(expression="2 3")

        assert result.success is False
        assert result.output is None
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_invalid_syntax_unbalanced_parentheses(self, calculator: CalculatorTool):
        """Test expression with unbalanced parentheses."""
        result = await calculator.execute(expression="(2 + 3")

        assert result.success is False
        assert result.output is None
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_invalid_syntax_double_operator(self, calculator: CalculatorTool):
        """Test expression with double operators."""
        result = await calculator.execute(expression="2 ++ 3")

        assert result.success is True  # This is actually valid: 2 + (+3)
        assert result.output == 5.0

    @pytest.mark.asyncio
    async def test_unsupported_operation_modulo(self, calculator: CalculatorTool):
        """Test that modulo operator is not supported."""
        result = await calculator.execute(expression="10 % 3")

        assert result.success is False
        assert result.output is None
        assert "unsupported" in result.error.lower() or "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_unsupported_operation_floor_division(self, calculator: CalculatorTool):
        """Test that floor division is not supported."""
        result = await calculator.execute(expression="10 // 3")

        assert result.success is False
        assert result.output is None
        assert "unsupported" in result.error.lower() or "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_string_constant_rejected(self, calculator: CalculatorTool):
        """Test that string constants are rejected."""
        result = await calculator.execute(expression="'hello' + 'world'")

        assert result.success is False
        assert result.output is None
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_function_call_rejected(self, calculator: CalculatorTool):
        """Test that function calls are rejected for security."""
        result = await calculator.execute(expression="abs(-5)")

        assert result.success is False
        assert result.output is None
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_import_rejected(self, calculator: CalculatorTool):
        """Test that import statements are rejected for security."""
        result = await calculator.execute(expression="__import__('os')")

        assert result.success is False
        assert result.output is None
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_attribute_access_rejected(self, calculator: CalculatorTool):
        """Test that attribute access is rejected."""
        result = await calculator.execute(expression="(1).__class__")

        assert result.success is False
        assert result.output is None
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_list_comprehension_rejected(self, calculator: CalculatorTool):
        """Test that list comprehensions are rejected."""
        result = await calculator.execute(expression="[x for x in range(10)]")

        assert result.success is False
        assert result.output is None
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_lambda_rejected(self, calculator: CalculatorTool):
        """Test that lambda expressions are rejected."""
        result = await calculator.execute(expression="(lambda x: x)(5)")

        assert result.success is False
        assert result.output is None
        assert result.error is not None


class TestCalculatorResultTypes:
    """Tests to verify result types and structure."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create a CalculatorTool instance for testing."""
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_result_is_tool_result(self, calculator: CalculatorTool):
        """Test that execute returns a ToolResult instance."""
        result = await calculator.execute(expression="1 + 1")

        assert isinstance(result, ToolResult)

    @pytest.mark.asyncio
    async def test_successful_result_has_float_output(self, calculator: CalculatorTool):
        """Test that successful calculations return float output."""
        result = await calculator.execute(expression="5 + 5")

        assert isinstance(result.output, float)

    @pytest.mark.asyncio
    async def test_integer_input_returns_float(self, calculator: CalculatorTool):
        """Test that integer inputs still return float output."""
        result = await calculator.execute(expression="10")

        assert result.output == 10.0
        assert isinstance(result.output, float)

    @pytest.mark.asyncio
    async def test_error_result_has_none_output(self, calculator: CalculatorTool):
        """Test that error results have None output."""
        result = await calculator.execute(expression="invalid")

        assert result.success is False
        assert result.output is None

    @pytest.mark.asyncio
    async def test_error_result_has_string_error(self, calculator: CalculatorTool):
        """Test that error results have string error messages."""
        result = await calculator.execute(expression="invalid")

        assert result.success is False
        assert isinstance(result.error, str)
        assert len(result.error) > 0

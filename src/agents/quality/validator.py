"""Output validation for agent responses.

Validates:
1. Response format matches expected format (JSON, etc.)
2. Tool results match expected schema
3. Response quality (length, completeness)
"""
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of output validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_output: Optional[Any] = None


class OutputValidator:
    """
    Validates agent outputs for format and quality.

    This ensures:
    1. JSON outputs are valid JSON
    2. Responses match declared output_format
    3. Responses are complete (not truncated)
    4. Tool results match expected schemas

    Usage:
        validator = OutputValidator()
        result = validator.validate(response, expected_format="JSON")
        if not result.is_valid:
            # Handle validation failure
            logger.error(f"Validation errors: {result.errors}")
    """

    # Minimum response lengths for different query types
    MIN_LENGTHS = {
        "explain": 100,
        "describe": 80,
        "detail": 100,
        "list": 20,
        "summarize": 50,
        "default": 10,
    }

    # Patterns indicating truncation
    TRUNCATION_PATTERNS = [
        r"\.\.\.$",  # Ends with ...
        r"[^.!?]$",  # Doesn't end with sentence terminator
        r"\d+\)\s*$",  # Ends with number) suggesting list was cut off
        r":\s*$",  # Ends with colon
        r",\s*$",  # Ends with comma
    ]

    def validate(
        self,
        response: str,
        expected_format: Optional[str] = None,
        user_query: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate an agent response.

        Args:
            response: The agent's response text
            expected_format: Expected format (e.g., "JSON", "JSON array", "markdown")
            user_query: Original user query for context-aware validation

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        validated_output = response

        # Check format compliance
        if expected_format:
            format_result = self._validate_format(response, expected_format)
            errors.extend(format_result.errors)
            warnings.extend(format_result.warnings)
            if format_result.validated_output is not None:
                validated_output = format_result.validated_output

        # Check response quality
        quality_result = self._validate_quality(response, user_query)
        warnings.extend(quality_result.warnings)

        # Check for truncation
        if self._is_truncated(response):
            warnings.append("truncated: Response appears to be cut off")

        is_valid = len(errors) == 0

        if errors or warnings:
            logger.info(
                "output_validation_result",
                is_valid=is_valid,
                error_count=len(errors),
                warning_count=len(warnings),
            )

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_output=validated_output,
        )

    def _validate_format(
        self, response: str, expected_format: str
    ) -> ValidationResult:
        """Validate response matches expected format."""
        errors = []
        warnings = []
        validated_output = None

        format_lower = expected_format.lower()

        if "json" in format_lower:
            # Try to parse as JSON
            try:
                # Handle markdown code blocks
                json_text = response
                if "```json" in response:
                    json_text = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_text = response.split("```")[1].split("```")[0].strip()

                parsed = json.loads(json_text)
                validated_output = parsed

                # Check array requirement
                if "array" in format_lower and not isinstance(parsed, list):
                    errors.append(
                        f"format_mismatch: Expected JSON array, got {type(parsed).__name__}"
                    )

                # Check object requirement
                if "object" in format_lower and not isinstance(parsed, dict):
                    errors.append(
                        f"format_mismatch: Expected JSON object, got {type(parsed).__name__}"
                    )

            except json.JSONDecodeError as e:
                errors.append(f"format_mismatch: Invalid JSON - {e}")

        elif "markdown" in format_lower:
            # Check for markdown indicators
            if not any(marker in response for marker in ["#", "-", "*", "```", "|"]):
                warnings.append("format_warning: Response may not be properly formatted as markdown")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_output=validated_output,
        )

    def _validate_quality(
        self, response: str, user_query: Optional[str]
    ) -> ValidationResult:
        """Validate response quality based on query type."""
        warnings = []

        if not user_query:
            return ValidationResult(is_valid=True, warnings=warnings)

        # Determine expected minimum length
        query_lower = user_query.lower()
        min_length = self.MIN_LENGTHS["default"]

        for keyword, length in self.MIN_LENGTHS.items():
            if keyword in query_lower:
                min_length = length
                break

        # Check response length
        if len(response) < min_length:
            warnings.append(
                f"short_response: Response ({len(response)} chars) may be too brief "
                f"for query type (expected ~{min_length}+ chars)"
            )

        return ValidationResult(is_valid=True, warnings=warnings)

    def _is_truncated(self, response: str) -> bool:
        """Check if response appears truncated."""
        response = response.strip()
        if not response:
            return False

        for pattern in self.TRUNCATION_PATTERNS:
            if re.search(pattern, response):
                # Exclude valid endings
                if response.endswith("...") and len(response) < 50:
                    continue  # Short response with ... might be intentional
                if response[-1] in ".!?":
                    continue  # Valid sentence ending
                return True

        return False

    def validate_tool_result(
        self,
        result: Dict[str, Any],
        expected_schema: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate a tool execution result.

        Args:
            result: Tool result dict
            expected_schema: Optional JSON schema for validation

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        # Basic structure validation
        if not isinstance(result, dict):
            errors.append(f"type_error: Expected dict, got {type(result).__name__}")
            return ValidationResult(is_valid=False, errors=errors)

        # Check for success/error structure
        if "success" not in result and "error" not in result:
            warnings.append("missing_status: Tool result lacks 'success' or 'error' field")

        # Schema validation if provided
        if expected_schema:
            schema_result = self._validate_schema(result, expected_schema)
            errors.extend(schema_result.errors)
            warnings.extend(schema_result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_output=result,
        )

    def _validate_schema(
        self, data: Any, schema: Dict[str, Any]
    ) -> ValidationResult:
        """Simple JSON schema validation."""
        errors = []
        warnings = []

        schema_type = schema.get("type")

        # Type validation
        if schema_type == "object" and not isinstance(data, dict):
            errors.append(f"type_error: Expected object, got {type(data).__name__}")
            return ValidationResult(is_valid=False, errors=errors)

        if schema_type == "array" and not isinstance(data, list):
            errors.append(f"type_error: Expected array, got {type(data).__name__}")
            return ValidationResult(is_valid=False, errors=errors)

        # Required fields validation
        if isinstance(data, dict):
            required = schema.get("required", [])
            for field in required:
                if field not in data:
                    errors.append(f"missing_field: Required field '{field}' not found")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

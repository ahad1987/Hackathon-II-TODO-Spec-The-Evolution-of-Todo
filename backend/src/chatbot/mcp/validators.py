"""
Input validation for MCP tools.

Validates all user inputs before tool execution.
Prevents injection attacks, malformed requests, and invalid states.

Critical for security:
- Validates string lengths
- Checks for null bytes and script injection patterns
- Validates enum values (role, status)
- Validates UUIDs
- Type checking
"""

import logging
from typing import Any, Dict, Optional
import uuid

logger = logging.getLogger(__name__)

# Constants
MAX_TITLE_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 5000
MAX_ROLE_LENGTH = 20
MAX_FIELD_LENGTH = 10000

ALLOWED_ROLES = {"user", "assistant"}
ALLOWED_STATUSES = {"pending", "completed", "archived"}

DANGEROUS_PATTERNS = [
    "\x00",  # Null byte injection
    "<script",  # XSS attempt
    "javascript:",  # XSS attempt
    "on",  # Event handlers (onclick, onerror, etc.)
    "eval(",  # Code injection
    "exec(",  # Code injection
]


class MCPInputValidator:
    """
    Validates MCP tool inputs.

    Usage:
        validator = MCPInputValidator()
        validator.validate_title("My Task")
        validator.validate_task_id("uuid-string")
        validator.validate_required_field("content", value)
    """

    @staticmethod
    def validate_string(value: Any, field_name: str, min_length: int = 0, max_length: int = MAX_FIELD_LENGTH) -> str:
        """
        Validate string input.

        Args:
            value: Value to validate
            field_name: Name of field (for error messages)
            min_length: Minimum string length
            max_length: Maximum string length

        Returns:
            Validated string

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string, got {type(value).__name__}")

        if len(value) < min_length:
            raise ValueError(f"{field_name} must be at least {min_length} characters")

        if len(value) > max_length:
            raise ValueError(f"{field_name} must be at most {max_length} characters")

        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if pattern.lower() in value.lower():
                logger.warning(f"Potentially dangerous pattern detected in {field_name}: {pattern}")
                raise ValueError(f"{field_name} contains invalid content")

        return value.strip()

    @staticmethod
    def validate_title(title: Any) -> str:
        """Validate task title."""
        return MCPInputValidator.validate_string(
            title,
            "title",
            min_length=1,
            max_length=MAX_TITLE_LENGTH
        )

    @staticmethod
    def validate_description(description: Any) -> str:
        """Validate task description."""
        if description is None:
            return None
        return MCPInputValidator.validate_string(
            description,
            "description",
            min_length=0,
            max_length=MAX_DESCRIPTION_LENGTH
        )

    @staticmethod
    def validate_task_id(task_id: Any) -> str:
        """
        Validate task ID (UUID format).

        Args:
            task_id: UUID string to validate

        Returns:
            Validated UUID string

        Raises:
            ValueError: If not valid UUID
        """
        if not isinstance(task_id, str):
            raise ValueError(f"task_id must be a string, got {type(task_id).__name__}")

        try:
            # Validate it's a proper UUID
            uuid.UUID(task_id)
            return task_id
        except (ValueError, AttributeError):
            raise ValueError(f"task_id must be a valid UUID, got: {task_id}")

    @staticmethod
    def validate_user_id(user_id: Any) -> str:
        """
        Validate user ID (UUID format).

        Args:
            user_id: UUID string to validate

        Returns:
            Validated UUID string

        Raises:
            ValueError: If not valid UUID
        """
        if not isinstance(user_id, str):
            raise ValueError(f"user_id must be a string, got {type(user_id).__name__}")

        try:
            uuid.UUID(user_id)
            return user_id
        except (ValueError, AttributeError):
            raise ValueError(f"user_id must be a valid UUID, got: {user_id}")

    @staticmethod
    def validate_boolean(value: Any, field_name: str) -> bool:
        """
        Validate boolean input.

        Args:
            value: Value to validate
            field_name: Name of field (for error messages)

        Returns:
            Validated boolean

        Raises:
            ValueError: If not boolean
        """
        if not isinstance(value, bool):
            raise ValueError(f"{field_name} must be a boolean, got {type(value).__name__}")
        return value

    @staticmethod
    def validate_role(role: Any) -> str:
        """
        Validate role enum.

        Args:
            role: Role string ('user' or 'assistant')

        Returns:
            Validated role

        Raises:
            ValueError: If not valid role
        """
        role = MCPInputValidator.validate_string(role, "role", min_length=1, max_length=MAX_ROLE_LENGTH)
        if role.lower() not in ALLOWED_ROLES:
            raise ValueError(f"role must be one of {ALLOWED_ROLES}, got: {role}")
        return role.lower()

    @staticmethod
    def validate_required_field(field_name: str, value: Any) -> None:
        """
        Validate that a required field is not null/empty.

        Args:
            field_name: Field name (for error messages)
            value: Value to check

        Raises:
            ValueError: If value is None or empty string
        """
        if value is None or value == "":
            raise ValueError(f"{field_name} is required")


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

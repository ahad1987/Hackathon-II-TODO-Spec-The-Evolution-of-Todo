"""
Error handling for MCP tools.

Provides consistent error handling across all tools.
Errors are never propagated as exceptions - always returned as structured responses.

Error taxonomy:
- ValidationError: Input validation failed (client error)
- AuthorizationError: User does not own resource (client error)
- NotFoundError: Resource not found (client error)
- ConflictError: Resource conflict (client error)
- InternalError: Database or unexpected error (server error)

User-facing errors:
- Sanitized to prevent information leakage
- Include helpful context for user
- Logged with full details for debugging
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Error type enumeration."""
    VALIDATION_ERROR = "validation_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    CONFLICT_ERROR = "conflict_error"
    INTERNAL_ERROR = "internal_error"


class MCPError(Exception):
    """Base error class for MCP tools."""

    def __init__(self, error_type: ErrorType, message: str, details: Optional[Dict[str, Any]] = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to structured response."""
        return {
            "status": "error",
            "error_type": self.error_type.value,
            "message": self.message,
            **({"details": self.details} if self.details else {})
        }


class ValidationError(MCPError):
    """Input validation failed."""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(ErrorType.VALIDATION_ERROR, message, details)
        logger.warning(f"Validation error: {message}" + (f" (field: {field})" if field else ""))


class AuthorizationError(MCPError):
    """User does not have permission to access resource."""

    def __init__(self, resource_type: str, resource_id: str, user_id: str):
        message = f"You do not have permission to access this {resource_type}"
        details = {"resource_type": resource_type, "resource_id": resource_id}
        super().__init__(ErrorType.AUTHORIZATION_ERROR, message, details)
        logger.warning(f"Authorization failed: user {user_id} attempted to access {resource_type} {resource_id}")


class NotFoundError(MCPError):
    """Resource not found."""

    def __init__(self, resource_type: str, resource_id: str):
        message = f"The {resource_type} you're looking for was not found"
        details = {"resource_type": resource_type, "resource_id": resource_id}
        super().__init__(ErrorType.NOT_FOUND_ERROR, message, details)
        logger.debug(f"Not found: {resource_type} {resource_id}")


class ConflictError(MCPError):
    """Resource conflict (e.g., duplicate, incompatible state)."""

    def __init__(self, message: str, conflict_reason: Optional[str] = None):
        details = {"conflict_reason": conflict_reason} if conflict_reason else {}
        super().__init__(ErrorType.CONFLICT_ERROR, message, details)
        logger.warning(f"Conflict: {message}" + (f" ({conflict_reason})" if conflict_reason else ""))


class InternalError(MCPError):
    """Internal server error (database, unexpected exception)."""

    def __init__(self, original_exception: Optional[Exception] = None):
        message = "An unexpected error occurred while processing your request"
        details = {
            "exception_type": type(original_exception).__name__ if original_exception else "Unknown"
        }
        super().__init__(ErrorType.INTERNAL_ERROR, message, details)
        if original_exception:
            logger.error(f"Internal error: {original_exception}", exc_info=True)


class MCPErrorHandler:
    """
    Handles errors in MCP tool execution.

    Usage:
        try:
            # Execute tool
            result = await tool_function()
        except MCPError as e:
            return e.to_dict()
        except Exception as e:
            return MCPErrorHandler.handle_unexpected_error(e)
    """

    @staticmethod
    def handle_validation_error(message: str, field: Optional[str] = None) -> Dict[str, Any]:
        """Handle validation error."""
        return ValidationError(message, field).to_dict()

    @staticmethod
    def handle_authorization_error(resource_type: str, resource_id: str, user_id: str) -> Dict[str, Any]:
        """Handle authorization error."""
        return AuthorizationError(resource_type, resource_id, user_id).to_dict()

    @staticmethod
    def handle_not_found_error(resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Handle not found error."""
        return NotFoundError(resource_type, resource_id).to_dict()

    @staticmethod
    def handle_conflict_error(message: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Handle conflict error."""
        return ConflictError(message, reason).to_dict()

    @staticmethod
    def handle_unexpected_error(exception: Exception) -> Dict[str, Any]:
        """Handle unexpected exception (never show details to user)."""
        error = InternalError(exception)
        return error.to_dict()

    @staticmethod
    def success_response(data: Dict[str, Any], **additional_fields) -> Dict[str, Any]:
        """
        Create a success response.

        Args:
            data: Response data
            **additional_fields: Additional fields to include

        Returns:
            Success response dict with status='success'
        """
        return {
            "status": "success",
            "data": data,
            **additional_fields
        }

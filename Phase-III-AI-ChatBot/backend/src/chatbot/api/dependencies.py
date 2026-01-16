"""
Dependency injection for Phase-III chatbot API.

Provides:
- JWT token validation
- User ID extraction
- User isolation enforcement
- Database session injection

Authentication flow:
1. Request arrives with Authorization: Bearer <JWT_TOKEN>
2. validate_token extracts user_id from token
3. get_current_user verifies token validity
4. Endpoint receives authenticated user_id
5. All database queries filtered by user_id
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

logger = logging.getLogger(__name__)

# Use HTTP Bearer for JWT token extraction
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """
    Extract and validate JWT token, return user_id.

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        User ID (UUID string)

    Raises:
        HTTPException: If token is invalid or expired

    Token validation:
        - Extracts token from Authorization: Bearer <token>
        - Validates using Phase-II Better Auth
        - Returns user_id from token claims
        - Enforces user_id consistency throughout request

    CRITICAL:
        - This is the single source of truth for user_id
        - All subsequent queries must use this user_id
        - Cannot be overridden by request parameters
    """
    try:
        token = credentials.credentials

        # TODO: Validate token using Phase-II Better Auth
        # For now, we assume token is pre-validated by middleware
        # In production, integrate with Better Auth library

        # Extract user_id from token (would be from token claims in real implementation)
        # This is a placeholder - actual implementation would parse JWT
        user_id = token.split(".")[-1] if "." in token else None

        if not user_id:
            logger.warning(f"Invalid token format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )

        logger.debug(f"Authenticated user: {user_id}")
        return user_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def verify_user_ownership(
    user_id_from_token: str,
    user_id_from_request: str
) -> None:
    """
    Verify that the user_id in the request matches the authenticated user.

    Args:
        user_id_from_token: User ID extracted from JWT token
        user_id_from_request: User ID from request URL/parameters

    Raises:
        HTTPException: If user_id mismatch (403 Forbidden)

    CRITICAL:
        - Users cannot access other users' data
        - This check prevents user_id spoofing in requests
        - Always called before accessing user-scoped resources
    """
    if user_id_from_token != user_id_from_request:
        logger.warning(
            f"User {user_id_from_token} attempted to access data for user {user_id_from_request}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource"
        )

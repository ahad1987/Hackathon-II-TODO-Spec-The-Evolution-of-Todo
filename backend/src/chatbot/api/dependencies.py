"""
Dependency injection for Phase-III chatbot API.

Uses Phase-II's existing authentication middleware for JWT validation.
The middleware validates tokens and stores user_id in request.state.

Authentication flow:
1. Request arrives with JWT token (via Authorization header or cookie)
2. AuthenticationMiddleware validates token
3. User ID stored in request.state.user_id
4. This dependency gets user_id from request state
5. Endpoint receives authenticated user_id
6. All database queries filtered by user_id
"""

import logging
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> str:
    """
    Get authenticated user_id from request state.

    This assumes AuthenticationMiddleware has already validated the JWT token
    and populated request.state.user_id.

    Args:
        request: FastAPI Request object

    Returns:
        User ID (UUID string) from token claims

    Raises:
        HTTPException: If user_id is not found in request state

    CRITICAL:
        - This is the single source of truth for user_id
        - All subsequent queries must use this user_id
        - Cannot be overridden by request parameters
    """
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        logger.warning("User ID not found in request state - auth middleware may have failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    logger.debug(f"Authenticated user: {user_id}")
    return user_id


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

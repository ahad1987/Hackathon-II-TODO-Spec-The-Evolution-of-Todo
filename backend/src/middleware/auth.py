"""
JWT authentication middleware for verifying tokens.
Extracts and validates JWT tokens from Authorization headers.
"""

import logging
import json
from typing import Callable, Optional
from datetime import datetime
import jwt
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# List of paths that don't require authentication
UNPROTECTED_PATHS = {
    "/health",
    "/health/live",
    "/health/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/signup",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify JWT tokens and extract user identity.
    Applied globally but only validates routes not in UNPROTECTED_PATHS.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> object:
        """
        Process request and attach user_id to request state if authenticated.
        """
        # Check if path is protected
        if request.url.path in UNPROTECTED_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        # Extract and validate JWT token
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            # Check for token in cookies (Better Auth stores JWT in cookies)
            token = None
            for cookie in request.cookies.values():
                try:
                    # Try to decode as JWT
                    jwt.decode(
                        cookie,
                        settings.BETTER_AUTH_SECRET,
                        algorithms=[settings.JWT_ALGORITHM],
                    )
                    token = cookie
                    break
                except jwt.InvalidTokenError:
                    continue

            if not token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Authorization header required",
                        "code": "MISSING_AUTH_HEADER",
                        "message": "Authorization header with Bearer token is required",
                    },
                )
        else:
            # Extract Bearer token from header
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "Invalid authorization header format",
                            "code": "INVALID_AUTH_FORMAT",
                            "message": "Authorization header must be 'Bearer <token>'",
                        },
                    )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Invalid authorization header format",
                        "code": "INVALID_AUTH_FORMAT",
                        "message": "Authorization header must be 'Bearer <token>'",
                    },
                )

        # Verify JWT token
        try:
            payload = jwt.decode(
                token,
                settings.BETTER_AUTH_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )

            # Extract user_id from token
            user_id = payload.get("sub") or payload.get("user_id")
            if not user_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Invalid token claims",
                        "code": "INVALID_TOKEN_CLAIMS",
                        "message": "Token does not contain required claims",
                    },
                )

            # Attach user_id to request state
            request.state.user_id = user_id
            request.state.token_claims = payload

            # Log successful authentication
            logger.debug(f"User {user_id} authenticated successfully")

        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Token has expired",
                    "code": "TOKEN_EXPIRED",
                    "message": "Your session has expired. Please log in again.",
                },
            )
        except jwt.InvalidSignatureError:
            logger.warning(f"Invalid token signature in request from {request.client}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Invalid token signature",
                    "code": "INVALID_SIGNATURE",
                    "message": "Token signature is invalid",
                },
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token error: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Invalid or expired token",
                    "code": "INVALID_TOKEN",
                    "message": "Token is invalid or expired",
                },
            )
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication failed",
                    "code": "AUTH_ERROR",
                    "message": "Authentication failed. Please try again.",
                },
            )

        # Continue to next middleware/route
        response = await call_next(request)
        return response


def get_current_user(request: Request) -> str:
    """
    Dependency to get current authenticated user_id from request.
    Usage:
        async def protected_route(user_id: str = Depends(get_current_user)):
            ...
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user_id


def get_token_claims(request: Request) -> dict:
    """
    Dependency to get JWT token claims from request.
    """
    claims = getattr(request.state, "token_claims", {})
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return claims

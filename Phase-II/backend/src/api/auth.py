"""
Authentication API endpoints.
Handles user signup, login, logout, and current user retrieval.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_session
from src.middleware.auth import get_current_user
from src.models.user import UserCreate, UserLogin, UserResponse
from src.services.user_service import UserService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_service: Optional[UserService] = None


async def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    """Dependency to get user service."""
    return UserService(session)


@router.post("/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """
    Register a new user account.

    Request body:
    - email: User's email address
    - password: User's password (minimum 8 characters)

    Returns:
    - user_id: Unique user identifier
    - email: User's email
    - token: JWT token for authentication

    Status codes:
    - 201: User created successfully
    - 400: Validation error (invalid email, weak password, duplicate email)
    - 500: Server error
    """
    logger.info(f"Signup request received for email: {user_data.email}")
    user_service = UserService(session)

    # Create user
    logger.info("Creating user...")
    user, error = await user_service.create_user(user_data)
    logger.info(f"User creation result: error={error}, user={user}")

    if error:
        logger.warning(f"Signup validation error: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": error,
                "code": "SIGNUP_ERROR",
                "message": error,
            },
        )

    # Create JWT token
    logger.info("Creating JWT token...")
    token = UserService.create_jwt_token(user.id, user.email)

    # Set secure cookie with token
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="none",
        secure=False,  # Set to True in production with HTTPS
        path="/"
    )

    logger.info(f"User signed up successfully: {user.email}")
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
        "token": token,
        "message": "User registered successfully",
    }


@router.post("/login", response_model=dict)
async def login(
    user_data: UserLogin,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """
    Authenticate user and return JWT token.

    Request body:
    - email: User's email address
    - password: User's password

    Returns:
    - user_id: Unique user identifier
    - email: User's email
    - token: JWT token for authentication

    Status codes:
    - 200: Authentication successful
    - 401: Invalid credentials
    - 500: Server error
    """
    user_service = UserService(session)

    # Authenticate user
    user, error = await user_service.authenticate_user(user_data)
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid email or password",
                "code": "INVALID_CREDENTIALS",
                "message": "Email or password is incorrect",
            },
        )

    # Create JWT token
    token = UserService.create_jwt_token(user.id, user.email)

    # Set secure cookie with token
    # SameSite=None for cross-origin (local dev with different ports)
    # Secure=False for local HTTP testing (should be True in production with HTTPS)
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,  # Prevent JavaScript access
        max_age=86400,  # 24 hours
        samesite="none",  # Allow cross-origin cookies
        secure=False,  # Set to True in production with HTTPS
        path="/"
    )

    logger.info(f"User logged in: {user.email}")
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
        "token": token,
        "message": "Login successful",
    }


@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """
    Logout user and invalidate session.

    Returns:
    - message: Logout confirmation

    Status codes:
    - 200: Logout successful
    - 401: Not authenticated
    - 500: Server error
    """
    # TODO: Implement logout logic
    # This will be implemented in T099
    logger.info(f"User {user_id} logged out")
    return {
        "status": "pending",
        "message": "Logout endpoint created (T022 stub). Implementation in T099.",
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get current authenticated user's information.

    Returns:
    - id: User ID
    - email: User's email
    - created_at: Account creation timestamp

    Status codes:
    - 200: Success
    - 401: Not authenticated
    - 404: User not found
    - 500: Server error
    """
    try:
        from src.services.user_service import UserService
        user_service = UserService(session)
        user = await user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "User not found",
                    "code": "USER_NOT_FOUND",
                    "message": "The user associated with this token no longer exists",
                },
            )

        logger.info(f"Retrieved current user info: {user.email}")
        return user

    except Exception as e:
        logger.error(f"Error retrieving current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve user information",
                "code": "USER_RETRIEVAL_ERROR",
                "message": str(e),
            },
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(request: Request):
    """
    Refresh access token using refresh token.
    Better Auth compatible endpoint for token renewal.

    Request body (optional):
    - refresh_token: Refresh token from cookies or body

    Returns:
    - token: New access token
    - message: Success message

    Status codes:
    - 200: Token refreshed successfully
    - 401: Refresh token invalid or expired
    - 500: Server error
    """
    try:
        from src.services.better_auth_compat import BetterAuthCompatible

        # Try to get refresh token from cookies first
        refresh_token_value = request.cookies.get("refresh_token")

        # If not in cookies, try request body
        if not refresh_token_value:
            try:
                body = await request.json()
                refresh_token_value = body.get("refresh_token")
            except Exception:
                pass

        if not refresh_token_value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "No refresh token provided",
                    "code": "NO_REFRESH_TOKEN",
                    "message": "Refresh token required",
                },
            )

        # Use compatibility layer to refresh token
        new_token = BetterAuthCompatible.refresh_access_token(refresh_token_value)

        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Invalid or expired refresh token",
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired",
                },
            )

        logger.info("Token refreshed successfully")
        return {
            "token": new_token,
            "message": "Token refreshed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to refresh token",
                "code": "TOKEN_REFRESH_ERROR",
                "message": str(e),
            },
        )

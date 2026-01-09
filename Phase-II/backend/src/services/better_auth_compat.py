"""
Better Auth Compatibility Layer
Provides Better Auth-like functionality while maintaining compatibility with existing JWT system.

This module allows optional Better Auth integration without breaking the current custom JWT implementation.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BetterAuthCompatible:
    """
    Compatibility layer that makes our JWT system compatible with Better Auth expectations.

    This allows gradual migration to Better Auth without breaking existing functionality.
    Current system fully supported during transition period.
    """

    @staticmethod
    def create_access_token(user_id: str, email: str, expires_in_seconds: Optional[int] = None) -> str:
        """
        Create an access token compatible with Better Auth standards.
        Uses same secret and algorithm as current system.

        Args:
            user_id: User identifier
            email: User email address
            expires_in_seconds: Token expiration time (default: settings.JWT_EXPIRY)

        Returns:
            JWT token string compatible with Better Auth
        """
        expiry_seconds = expires_in_seconds or settings.JWT_EXPIRY

        payload = {
            "sub": user_id,
            "email": email,
            "type": "access",  # Better Auth convention
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=expiry_seconds),
        }

        token = jwt.encode(
            payload,
            settings.BETTER_AUTH_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token

    @staticmethod
    def create_refresh_token(user_id: str, email: str) -> str:
        """
        Create a refresh token for token renewal.
        Better Auth compatible format.

        Args:
            user_id: User identifier
            email: User email address

        Returns:
            JWT refresh token string
        """
        # Refresh tokens live longer (7 days)
        refresh_expiry = 7 * 24 * 60 * 60  # 7 days in seconds

        payload = {
            "sub": user_id,
            "email": email,
            "type": "refresh",  # Better Auth convention
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=refresh_expiry),
        }

        token = jwt.encode(
            payload,
            settings.BETTER_AUTH_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify a token and return claims.
        Works with both access and refresh tokens.

        Args:
            token: JWT token to verify

        Returns:
            Token claims (dict) if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.BETTER_AUTH_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        Check if a token is expired.

        Args:
            token: JWT token to check

        Returns:
            True if expired, False if still valid
        """
        claims = BetterAuthCompatible.verify_token(token)
        return claims is None

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token, or None if refresh token invalid
        """
        claims = BetterAuthCompatible.verify_token(refresh_token)

        if not claims or claims.get("type") != "refresh":
            logger.warning("Invalid refresh token")
            return None

        # Create new access token with same user info
        return BetterAuthCompatible.create_access_token(
            user_id=claims.get("sub"),
            email=claims.get("email"),
        )

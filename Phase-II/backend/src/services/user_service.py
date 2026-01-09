"""
User service module.
Handles user-related business logic (signup, login, password hashing, etc.).
"""

import logging
import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlmodel import Session
import bcrypt
import jwt
from datetime import datetime, timedelta

from src.config import get_settings
from src.models.user import User, UserCreate, UserLogin

logger = logging.getLogger(__name__)
settings = get_settings()


class UserService:
    """Service for user operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plaintext password using bcrypt.

        Args:
            password: Plaintext password

        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt(rounds=settings.PASSWORD_HASH_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plaintext: str, hashed: str) -> bool:
        """
        Verify a plaintext password against a hash.

        Args:
            plaintext: Plaintext password to verify
            hashed: Hashed password from database

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(plaintext.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format using RFC 5322 pattern.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email)) and len(email) <= settings.EMAIL_MAX_LENGTH

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"

        # Additional checks
        if not any(c.isupper() for c in password):
            return True, None  # Optional: could require uppercase

        return True, None

    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists in database.

        Args:
            email: Email to check

        Returns:
            True if email exists, False otherwise
        """
        try:
            stmt = select(User).where(User.email == email.lower())
            result = await self.session.execute(stmt)
            return result.scalars().first() is not None
        except Exception as e:
            logger.error(f"Error checking email existence: {e}")
            return False

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        try:
            stmt = select(User).where(User.email == email.lower())
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object if found, None otherwise
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    async def create_user(self, user_data: UserCreate) -> tuple[Optional[User], Optional[str]]:
        """
        Create a new user account.

        Args:
            user_data: User creation data

        Returns:
            Tuple of (user, error_message)
        """
        try:
            # Validate email format
            if not self.validate_email(user_data.email):
                return None, "Invalid email format"

            # Check if email already exists
            if await self.email_exists(user_data.email):
                return None, "Email already registered"

            # Validate password strength
            is_valid, error_msg = self.validate_password_strength(user_data.password)
            if not is_valid:
                return None, error_msg

            # Hash password
            hashed_password = self.hash_password(user_data.password)

            # Create user
            user = User(
                email=user_data.email.lower(),
                hashed_password=hashed_password,
            )

            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            logger.info(f"User created: {user.email}")
            return user, None

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await self.session.rollback()
            return None, "Failed to create user account"

    async def authenticate_user(self, user_data: UserLogin) -> tuple[Optional[User], Optional[str]]:
        """
        Authenticate user with email and password.

        Args:
            user_data: Login data

        Returns:
            Tuple of (user, error_message)
        """
        try:
            user = await self.get_user_by_email(user_data.email)
            if not user:
                return None, "Invalid email or password"

            if not self.verify_password(user_data.password, user.hashed_password):
                return None, "Invalid email or password"

            logger.info(f"User authenticated: {user.email}")
            return user, None

        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None, "Authentication failed"

    @staticmethod
    def create_jwt_token(user_id: str, email: str) -> str:
        """
        Create JWT token for authenticated user.

        Args:
            user_id: User ID
            email: User's email

        Returns:
            JWT token string
        """
        try:
            payload = {
                "sub": user_id,
                "email": email,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRY),
            }
            token = jwt.encode(
                payload,
                settings.BETTER_AUTH_SECRET,
                algorithm=settings.JWT_ALGORITHM,
            )
            return token
        except Exception as e:
            logger.error(f"Error creating JWT token: {e}")
            raise

"""
Configuration module for the Todo Backend application.
Loads settings from environment variables with defaults.
"""

import os
from typing import Optional
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/todo_db"
    )

    # JWT Configuration
    BETTER_AUTH_SECRET: str = os.getenv(
        "BETTER_AUTH_SECRET",
        "your-very-long-secret-key-at-least-32-characters-for-jwt-signing-phase-ii-todo"
    )
    JWT_EXPIRY: int = int(os.getenv("JWT_EXPIRY", "86400"))  # 24 hours default
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # CORS Configuration
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://localhost:5173,https://mytodoappv2.vercel.app,https://stately-dieffenbachia-b565a9.netlify.app"
        ).split(",")
    ]

    # Server Configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    API_TITLE: str = "Todo API"
    API_VERSION: str = "0.1.0"

    # API Configuration
    API_PREFIX: str = "/api/v1"

    # Password hashing
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    PASSWORD_HASH_ROUNDS: int = 12

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100

    # Email validation
    EMAIL_REGEX: str = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    # Task constraints
    TASK_TITLE_MIN_LENGTH: int = 1
    TASK_TITLE_MAX_LENGTH: int = 255
    TASK_DESCRIPTION_MAX_LENGTH: int = 5000

    # User constraints
    PASSWORD_MIN_LENGTH: int = 8
    EMAIL_MAX_LENGTH: int = 255

    def __init__(self):
        """Validate critical settings on initialization."""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
        if len(self.BETTER_AUTH_SECRET) < 32:
            raise ValueError("BETTER_AUTH_SECRET must be at least 32 characters long")


def get_settings() -> Settings:
    """Get application settings (loads fresh from environment on each call)."""
    return Settings()

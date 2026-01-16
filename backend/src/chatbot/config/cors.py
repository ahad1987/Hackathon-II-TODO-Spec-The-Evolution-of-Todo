"""
CORS configuration for Phase-III chatbot.

Configures cross-origin request handling for the chat endpoint.
Allows Phase-III frontend to make requests to chatbot API.
"""

from typing import Dict, Any
import os


def get_cors_config() -> Dict[str, Any]:
    """
    Get CORS configuration.

    Returns:
        CORS config dict for FastAPI.add_middleware(CORSMiddleware, ...)

    Configuration:
    - allow_origins: Frontend URLs (localhost for dev, deployed URL for prod)
    - allow_credentials: Allow cookies/auth headers
    - allow_methods: POST for chat endpoint
    - allow_headers: Content-Type, Authorization
    """
    # Get frontend URL from environment (or default to localhost for dev)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    return {
        "allow_origins": [frontend_url, "http://localhost:5173", "http://localhost:3000"],
        "allow_credentials": True,
        "allow_methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["*"],
        "max_age": 3600,
    }

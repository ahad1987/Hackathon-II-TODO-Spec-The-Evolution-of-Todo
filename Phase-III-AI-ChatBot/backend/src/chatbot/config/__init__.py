"""
Phase-III Chatbot configuration module.

Configuration for:
- CORS (cross-origin requests)
- Feature flags
- Rate limiting
- Security settings
"""

from src.chatbot.config.cors import get_cors_config

__all__ = ["get_cors_config"]

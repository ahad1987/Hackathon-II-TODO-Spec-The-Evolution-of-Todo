"""
Phase-III Chatbot API module.

Provides REST endpoints for chat operations.

Endpoints:
- POST /api/{user_id}/chat - Process chat message
"""

from src.chatbot.api.routes.chat import router as chat_router

__all__ = ["chat_router"]

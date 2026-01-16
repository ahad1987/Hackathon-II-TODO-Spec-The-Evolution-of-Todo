"""
Phase-III Chatbot models module.
SQLModel-based ORM models for conversation and message persistence.

These models integrate with Phase-II's database infrastructure:
- Uses same database connection (Neon PostgreSQL)
- Uses same SQLModel and SQLAlchemy setup
- Foreign keys reference Phase-II "users" table
- Backward-compatible migrations (Phase-II Task table unchanged)
"""

from src.chatbot.models.conversation import Conversation, ConversationCreate, ConversationResponse
from src.chatbot.models.message import Message, MessageCreate, MessageResponse

# Register models for SQLModel.metadata (used by init_db in Phase-II)
__all__ = [
    "Conversation",
    "ConversationCreate",
    "ConversationResponse",
    "Message",
    "MessageCreate",
    "MessageResponse",
]

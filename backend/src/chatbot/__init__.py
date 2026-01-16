"""
Phase-III AI Chatbot module.

This module contains all Phase-III chatbot functionality:
- Models: Conversation, Message (new SQLModel tables)
- Services: Agent, Conversation management
- MCP: Model Context Protocol server and tools
- API: Chat endpoint (POST /api/{user_id}/chat)

Architecture principles:
- Namespace isolation: All Phase-III code in chatbot/ (does not modify Phase-II)
- User isolation: All queries filtered by user_id from JWT token
- Statelessness: Request loads history, executes, persists, releases (no in-memory state)
- Backward compatibility: Phase-II models/endpoints/auth unchanged

Integration with Phase-II:
- Shares database connection and SQLModel setup
- Reuses Better Auth JWT validation
- Writes to Phase-II Task table via MCP tools (not direct DB access)
- Reads Phase-II User, Task tables for operations

Safety guarantees:
✅ Phase-II Task table unchanged (migrations are additive only)
✅ Phase-II Auth flow unchanged (Better Auth reused)
✅ Phase-II API endpoints unchanged
✅ Phase-II UI components unchanged
✅ User isolation enforced at every query (WHERE user_id = :user_id)
"""

from src.chatbot.models import (
    Conversation,
    ConversationCreate,
    ConversationResponse,
    Message,
    MessageCreate,
    MessageResponse,
)

__all__ = [
    "Conversation",
    "ConversationCreate",
    "ConversationResponse",
    "Message",
    "MessageCreate",
    "MessageResponse",
]

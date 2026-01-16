"""
Message model using SQLModel ORM.
Represents a single message in a conversation between user and AI.
"""

from datetime import datetime
from typing import Optional, Any, List
from sqlmodel import SQLModel, Field, Relationship
import uuid
import json


class Message(SQLModel, table=True):
    """
    Message entity representing a single message in a conversation.

    Attributes:
        id: Unique message identifier (UUID)
        user_id: Owner's user ID (for isolation; foreign key to Phase-II "user" table)
        conversation_id: Associated conversation ID (foreign key)
        role: Message role ('user' or 'assistant')
        content: Message text content
        tool_calls: List of MCP tool calls made (JSONB array, serialized)
        created_at: Message creation timestamp
    """

    __tablename__ = "message"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="Unique message identifier"
    )
    user_id: str = Field(
        foreign_key="users.id",
        index=True,
        description="Owner's user ID (references Phase-II user table) - for user isolation"
    )
    conversation_id: str = Field(
        foreign_key="conversation.id",
        index=True,
        description="Associated conversation ID"
    )
    role: str = Field(
        min_length=1,
        max_length=20,
        description="Message role: 'user' or 'assistant'"
    )
    content: str = Field(
        description="Message text content"
    )
    tool_calls: Optional[str] = Field(
        default=None,
        description="JSON serialized list of MCP tool calls made by agent (null if user message)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message creation timestamp (immutable)"
    )

    # Relationship to parent conversation
    conversation: Optional["Conversation"] = Relationship(
        back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} conversation_id={self.conversation_id}>"

    @property
    def tool_calls_parsed(self) -> List[dict]:
        """Parse tool_calls JSON string to list of dicts."""
        if not self.tool_calls:
            return []
        try:
            return json.loads(self.tool_calls)
        except (json.JSONDecodeError, TypeError):
            return []

    @staticmethod
    def serialize_tool_calls(tool_calls: Optional[List[dict]]) -> Optional[str]:
        """Serialize tool_calls list to JSON string."""
        if not tool_calls:
            return None
        try:
            return json.dumps(tool_calls)
        except (TypeError, ValueError):
            return None


class MessageCreate(SQLModel):
    """Schema for message creation."""
    user_id: str = Field(description="Owner's user ID")
    conversation_id: str = Field(description="Conversation ID")
    role: str = Field(
        min_length=1,
        max_length=20,
        description="Message role: 'user' or 'assistant'"
    )
    content: str = Field(
        min_length=1,
        description="Message text content"
    )
    tool_calls: Optional[str] = Field(
        default=None,
        description="JSON serialized list of tool calls (optional)"
    )


class MessageResponse(SQLModel):
    """Schema for message response."""
    id: str = Field(description="Message ID")
    user_id: str = Field(description="Owner's user ID")
    conversation_id: str = Field(description="Conversation ID")
    role: str = Field(description="Message role")
    content: str = Field(description="Message content")
    tool_calls: Optional[List[dict]] = Field(
        default=None,
        description="Parsed list of tool calls"
    )
    created_at: datetime = Field(description="Creation timestamp")

    class Config:
        from_attributes = True


class MessageInDB(MessageResponse):
    """Message model as it exists in the database."""

    class Config:
        from_attributes = True


# Lazy import to avoid circular dependencies
from src.chatbot.models.conversation import Conversation  # noqa: E402, F401

Message.update_forward_refs()

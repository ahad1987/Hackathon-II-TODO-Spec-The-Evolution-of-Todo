"""
Conversation model using SQLModel ORM.
Represents a conversation thread between user and AI chatbot.
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
import uuid


class Conversation(SQLModel, table=True):
    """
    Conversation entity representing a chat thread.

    Attributes:
        id: Unique conversation identifier (UUID)
        user_id: Owner's user ID (foreign key to Phase-II "user" table)
        created_at: Conversation creation timestamp
        updated_at: Last activity timestamp
        messages: Relationship to associated messages
    """

    __tablename__ = "conversation"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="Unique conversation identifier"
    )
    user_id: str = Field(
        foreign_key="users.id",
        index=True,
        description="Owner's user ID (references Phase-II user table)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Conversation creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity timestamp (updated on each message)"
    )

    # Relationship to messages in this conversation
    messages: List["Message"] = Relationship(
        back_populates="conversation",
        cascade_delete=True
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} user_id={self.user_id} messages={len(self.messages)}>"


class ConversationCreate(SQLModel):
    """Schema for conversation creation (minimal - only user_id needed)."""
    user_id: str = Field(description="Owner's user ID")


class ConversationResponse(SQLModel):
    """Schema for conversation response."""
    id: str = Field(description="Conversation ID")
    user_id: str = Field(description="Owner's user ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last activity timestamp")
    message_count: int = Field(default=0, description="Number of messages in conversation")

    class Config:
        from_attributes = True


class ConversationInDB(ConversationResponse):
    """Conversation model as it exists in the database."""

    class Config:
        from_attributes = True


# Lazy import to avoid circular dependencies
from src.chatbot.models.message import Message  # noqa: E402, F401

Conversation.update_forward_refs()

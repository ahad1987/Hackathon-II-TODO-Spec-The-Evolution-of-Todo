"""
Task model using SQLModel ORM.
Represents a todo item owned by a user.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
import uuid


class Task(SQLModel, table=True):
    """
    Task entity representing a todo item.

    Attributes:
        id: Unique task identifier (UUID)
        user_id: Owner's user ID (foreign key)
        title: Task title (required, max 255 chars)
        description: Task description (optional)
        completed: Whether task is completed (default: False)
        created_at: Task creation timestamp
        updated_at: Last task update timestamp
        user: Relationship to the owning user
    """

    __tablename__ = "tasks"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="Unique task identifier"
    )
    user_id: str = Field(
        foreign_key="users.id",
        index=True,
        description="Owner's user ID"
    )
    title: str = Field(
        max_length=255,
        description="Task title"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Task description (optional)"
    )
    completed: bool = Field(
        default=False,
        description="Whether task is completed"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last task update timestamp"
    )

    # Relationship to user
    user: Optional["User"] = Relationship(
        back_populates="tasks"
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title} user_id={self.user_id}>"


class TaskBase(SQLModel):
    """Base task schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Task description"
    )
    completed: bool = Field(default=False, description="Completion status")


class TaskCreate(SQLModel):
    """Schema for task creation."""
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Task description"
    )


class TaskUpdate(SQLModel):
    """Schema for task updates."""
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Task title"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Task description"
    )
    completed: Optional[bool] = Field(
        default=None,
        description="Completion status"
    )


class TaskResponse(TaskBase):
    """Schema for task response."""
    id: str = Field(description="Task ID")
    user_id: str = Field(description="Owner's user ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        from_attributes = True


class TaskListResponse(SQLModel):
    """Schema for task list response."""
    id: str
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskInDB(TaskResponse):
    """Task model as it exists in the database."""

    class Config:
        from_attributes = True


# Fix circular import
from src.models.user import User  # noqa: E402, F401

Task.update_forward_refs()

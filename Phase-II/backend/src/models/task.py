"""
Task model using SQLModel ORM.
Represents a todo item owned by a user.

Phase V Extensions:
- Recurring task fields (recurrence_pattern, parent_recurring_task_id, occurrence_date)
- Due date and reminder fields (due_date, reminder_offset, reminder_status)
"""

from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column, Text
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

    # Phase V: Recurring Task Fields (User Story 1)
    recurrence_pattern: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Recurrence pattern (e.g., 'daily', 'weekly:monday,friday', 'monthly:1,15')"
    )
    recurrence_end_date: Optional[datetime] = Field(
        default=None,
        description="End date for recurring task generation"
    )
    parent_recurring_task_id: Optional[str] = Field(
        default=None,
        index=True,
        description="ID of parent recurring task (null for master, populated for instances)"
    )
    occurrence_date: Optional[date] = Field(
        default=None,
        description="Specific occurrence date for task instance"
    )

    # Phase V: Due Date and Reminder Fields (User Story 2)
    due_date: Optional[datetime] = Field(
        default=None,
        description="Task due date/time"
    )
    reminder_offset: Optional[str] = Field(
        default=None,
        description="Reminder offset interval (e.g., '1 hour', '30 minutes', '1 day')"
    )
    reminder_status: Optional[str] = Field(
        default=None,
        description="Reminder status (pending, triggered, cancelled)"
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
    """
    Schema for task creation.

    Phase V: Includes recurring task and reminder fields.
    """
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Task description"
    )

    # Phase V: Recurring task fields
    recurrence_pattern: Optional[str] = Field(
        default=None,
        description="Recurrence pattern (e.g., 'daily', 'weekly:monday', 'monthly:1,15')"
    )
    recurrence_end_date: Optional[datetime] = Field(
        default=None,
        description="End date for recurring task generation"
    )

    # Phase V: Due date and reminder fields
    due_date: Optional[datetime] = Field(
        default=None,
        description="Task due date/time"
    )
    reminder_offset: Optional[str] = Field(
        default=None,
        description="Reminder offset interval (e.g., '1 hour', '30 minutes', '1 day')"
    )


class TaskUpdate(SQLModel):
    """
    Schema for task updates.

    Phase V: Includes recurring task and reminder fields.
    """
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

    # Phase V: Recurring task fields
    recurrence_pattern: Optional[str] = Field(
        default=None,
        description="Recurrence pattern"
    )
    recurrence_end_date: Optional[datetime] = Field(
        default=None,
        description="End date for recurring task generation"
    )

    # Phase V: Due date and reminder fields
    due_date: Optional[datetime] = Field(
        default=None,
        description="Task due date/time"
    )
    reminder_offset: Optional[str] = Field(
        default=None,
        description="Reminder offset interval"
    )


class TaskResponse(TaskBase):
    """
    Schema for task response.

    Phase V: Includes all recurring task and reminder fields.
    """
    id: str = Field(description="Task ID")
    user_id: str = Field(description="Owner's user ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    # Phase V: Recurring task fields
    recurrence_pattern: Optional[str] = Field(default=None, description="Recurrence pattern")
    recurrence_end_date: Optional[datetime] = Field(default=None, description="Recurrence end date")
    parent_recurring_task_id: Optional[str] = Field(default=None, description="Parent recurring task ID")
    occurrence_date: Optional[date] = Field(default=None, description="Occurrence date")

    # Phase V: Due date and reminder fields
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    reminder_offset: Optional[str] = Field(default=None, description="Reminder offset")
    reminder_status: Optional[str] = Field(default=None, description="Reminder status")

    class Config:
        from_attributes = True


class TaskListResponse(SQLModel):
    """
    Schema for task list response.

    Phase V: Includes all recurring task and reminder fields.
    """
    id: str
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime

    # Phase V: Recurring task fields
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None
    parent_recurring_task_id: Optional[str] = None
    occurrence_date: Optional[date] = None

    # Phase V: Due date and reminder fields
    due_date: Optional[datetime] = None
    reminder_offset: Optional[str] = None
    reminder_status: Optional[str] = None

    class Config:
        from_attributes = True


class TaskInDB(TaskResponse):
    """Task model as it exists in the database."""

    class Config:
        from_attributes = True


# Fix circular import
from src.models.user import User  # noqa: E402, F401

Task.update_forward_refs()

"""
User model using SQLModel ORM.
Represents a registered user in the application.
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
import uuid


class User(SQLModel, table=True):
    """
    User entity representing a registered user account.

    Attributes:
        id: Unique user identifier (UUID)
        email: User's email address (unique, required)
        hashed_password: Bcrypt hashed password (never expose this)
        created_at: Account creation timestamp
        updated_at: Last account update timestamp
        tasks: Relationship to user's tasks
    """

    __tablename__ = "users"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="Unique user identifier"
    )
    email: str = Field(
        unique=True,
        index=True,
        max_length=255,
        description="User's email address"
    )
    hashed_password: str = Field(
        description="Bcrypt hashed password"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last account update timestamp"
    )

    # Relationship to tasks
    tasks: List["Task"] = Relationship(
        back_populates="user",
        cascade_delete=True
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class UserBase(SQLModel):
    """Base user schema for request/response."""
    email: str = Field(..., max_length=255, description="User's email address")


class UserCreate(UserBase):
    """Schema for user creation (signup)."""
    password: str = Field(..., min_length=8, description="User password (plain text)")


class UserLogin(UserBase):
    """Schema for user login."""
    password: str = Field(..., min_length=8, description="User password (plain text)")


class UserResponse(UserBase):
    """Schema for user response (no sensitive data)."""
    id: str = Field(description="User ID")
    created_at: datetime = Field(description="Account creation timestamp")

    class Config:
        from_attributes = True


class UserInDB(UserBase):
    """User model as it exists in the database (with password)."""
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Fix circular import
from src.models.task import Task  # noqa: E402, F401

User.update_forward_refs()

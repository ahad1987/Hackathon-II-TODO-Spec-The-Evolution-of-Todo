"""
Alembic migration: Create message table for Phase-III AI Chatbot.

Revision ID: 002
Create Date: 2026-01-15 00:00:01.000000

This migration is BACKWARD-COMPATIBLE:
- Adds new table "message" (does not modify Phase-II tables)
- Depends on: 001_create_conversation.py (conversation table must exist)
- Uses foreign keys to Phase-II "users" table and Phase-III "conversation" table
- Phase-II Task CRUD operations remain unchanged
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """
    Create message table.

    Message table schema:
    - id: UUID primary key
    - user_id: Foreign key to Phase-II user table (for isolation validation)
    - conversation_id: Foreign key to Phase-III conversation table
    - role: 'user' or 'assistant' (varchar 20)
    - content: Message text (no length limit to support long conversations)
    - tool_calls: JSON array of MCP tool calls (nullable, for user messages)
    - created_at: Immutable timestamp of message creation

    Indexes:
    - user_id: Fast filtering by user (ensures user isolation)
    - conversation_id: Fast filtering by conversation (load conversation history)
    """
    op.create_table(
        'message',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_calls', sa.Text(), nullable=True),  # JSON serialized
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Index on user_id for user isolation verification (fast permission checks)
    op.create_index(
        op.f('ix_message_user_id'),
        'message',
        ['user_id'],
        unique=False
    )

    # Index on conversation_id for loading conversation history (most critical query)
    op.create_index(
        op.f('ix_message_conversation_id'),
        'message',
        ['conversation_id'],
        unique=False
    )

    # Composite index for conversation history queries (user_id + conversation_id)
    # Useful for validation queries that verify user owns conversation
    op.create_index(
        'ix_message_user_conversation',
        'message',
        ['user_id', 'conversation_id'],
        unique=False
    )


def downgrade() -> None:
    """
    Drop message table.

    Safe to downgrade as this is a new Phase-III table.
    Conversation table will remain (downgrade those separately if needed).
    No Phase-II data is affected.
    """
    op.drop_index('ix_message_user_conversation', table_name='message')
    op.drop_index(op.f('ix_message_conversation_id'), table_name='message')
    op.drop_index(op.f('ix_message_user_id'), table_name='message')
    op.drop_table('message')

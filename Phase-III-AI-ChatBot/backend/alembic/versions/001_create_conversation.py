"""
Alembic migration: Create conversation table for Phase-III AI Chatbot.

Revision ID: 001
Create Date: 2026-01-15 00:00:00.000000

This migration is BACKWARD-COMPATIBLE:
- Adds new table "conversation" (does not modify Phase-II tables)
- Uses foreign key to Phase-II "users" table
- Phase-II Task CRUD operations remain unchanged
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


def upgrade() -> None:
    """
    Create conversation table.

    Conversation table schema:
    - id: UUID primary key
    - user_id: Foreign key to Phase-II user table (for isolation)
    - created_at: Timestamp of conversation creation
    - updated_at: Timestamp of last message (for relevance sorting)
    """
    op.create_table(
        'conversation',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on user_id for fast filtering (critical for per-user queries)
    op.create_index(
        op.f('ix_conversation_user_id'),
        'conversation',
        ['user_id'],
        unique=False
    )


def downgrade() -> None:
    """
    Drop conversation table.

    Safe to downgrade as this is a new Phase-III table.
    No Phase-II data is affected.
    """
    op.drop_index(op.f('ix_conversation_user_id'), table_name='conversation')
    op.drop_table('conversation')

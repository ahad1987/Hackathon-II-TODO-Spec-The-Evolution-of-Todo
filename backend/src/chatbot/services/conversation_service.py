"""
Conversation persistence service for Phase-III AI Chatbot.

Handles conversation creation, retrieval, message appending, and user isolation.
All operations are scoped by user_id to enforce user isolation.

Critical guarantee:
- All database queries include WHERE user_id = :user_id filter
- User cannot access other users' conversations
- Prevents data leakage across user boundaries
"""

import logging
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlmodel import func

from src.chatbot.models import Conversation, Message, MessageCreate

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Service for managing conversations and messages.

    All operations enforce user isolation:
    - Create: new conversation is scoped to user_id
    - Load: only return conversations owned by user_id
    - Append: verify message belongs to user's conversation
    - Get: strict ownership check before returning data
    """

    async def create_conversation(
        self,
        session: AsyncSession,
        user_id: str
    ) -> Conversation:
        """
        Create a new conversation for a user.

        Args:
            session: Database session
            user_id: Owner's user ID (from JWT token)

        Returns:
            Newly created Conversation object

        Raises:
            Exception: If database operation fails

        Guarantees:
            - Conversation is immediately saved to database
            - Returns new conversation with populated id and timestamps
            - Only accessible to the owning user
        """
        conversation = Conversation(
            id=str(uuid4()),
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    async def get_conversation(
        self,
        session: AsyncSession,
        conversation_id: str,
        user_id: str
    ) -> Optional[Conversation]:
        """
        Retrieve a conversation with user ownership verification.

        Args:
            session: Database session
            conversation_id: Conversation ID to retrieve
            user_id: Requesting user ID (from JWT token) - MUST match owner

        Returns:
            Conversation object if found and owned by user_id, None otherwise

        Guarantees:
            - Strict ownership check: WHERE conversation_id = :id AND user_id = :user_id
            - Returns None (no error) if conversation not found or not owned by user
            - Prevents unauthorized access attempts (logs as warning)
        """
        statement = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id  # CRITICAL: User isolation filter
            )
        )

        result = await session.execute(statement)
        conversation = result.scalars().first()

        if not conversation:
            logger.warning(
                f"Conversation {conversation_id} not found or not owned by user {user_id}"
            )

        return conversation

    async def get_conversation_history(
        self,
        session: AsyncSession,
        conversation_id: str,
        user_id: str
    ) -> List[Message]:
        """
        Load conversation history for chat context.

        Args:
            session: Database session
            conversation_id: Conversation ID to load
            user_id: Requesting user ID (from JWT token)

        Returns:
            List of Message objects in conversation order (oldest first)

        Guarantees:
            - User isolation: verified by checking user_id on conversation
            - Immutable: messages are ordered by created_at
            - Complete: returns all messages in conversation
            - Ordered correctly: oldest message first (for context building)
        """
        # First verify user owns this conversation
        conversation = await self.get_conversation(session, conversation_id, user_id)
        if not conversation:
            logger.warning(
                f"User {user_id} attempted to access conversation {conversation_id} they don't own"
            )
            return []

        # Load all messages for this conversation (ordered by creation time)
        statement = select(Message).where(
            and_(
                Message.conversation_id == conversation_id,
                Message.user_id == user_id  # Additional safety: verify message owner
            )
        ).order_by(Message.created_at.asc())

        result = await session.execute(statement)
        messages = result.scalars().all()

        logger.debug(
            f"Loaded {len(messages)} messages for conversation {conversation_id} (user {user_id})"
        )
        return list(messages)

    async def append_message(
        self,
        session: AsyncSession,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        tool_calls: Optional[str] = None
    ) -> Message:
        """
        Append a message to a conversation.

        Args:
            session: Database session
            conversation_id: Conversation ID to append to
            user_id: Requesting user ID (from JWT token)
            role: Message role ('user' or 'assistant')
            content: Message content
            tool_calls: Optional JSON serialized list of tool calls

        Returns:
            Newly created Message object

        Raises:
            ValueError: If conversation not found or not owned by user
            Exception: If database operation fails

        Guarantees:
            - Message is immediately saved to database
            - Conversation updated_at timestamp is updated (for sorting)
            - Message is scoped to user_id (double-safety check)
            - Tool calls are preserved as JSON string for storage
        """
        # Verify user owns this conversation
        conversation = await self.get_conversation(session, conversation_id, user_id)
        if not conversation:
            raise ValueError(
                f"Conversation {conversation_id} not found or not owned by user {user_id}"
            )

        # Create message
        message = Message(
            id=str(uuid4()),
            user_id=user_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            created_at=datetime.utcnow()
        )

        session.add(message)

        # Update conversation's updated_at timestamp
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)

        await session.commit()
        await session.refresh(message)

        logger.info(
            f"Appended message {message.id} ({role}) to conversation {conversation_id} (user {user_id})"
        )
        return message

    async def get_conversation_summary(
        self,
        session: AsyncSession,
        user_id: str
    ) -> List[dict]:
        """
        Get list of recent conversations for a user (for conversation sidebar).

        Args:
            session: Database session
            user_id: User ID (from JWT token)

        Returns:
            List of dicts with: id, created_at, updated_at, message_count

        Guarantees:
            - Ordered by recent activity (updated_at DESC)
            - Only user's conversations returned
            - Includes message count (for preview)
        """
        statement = select(
            Conversation.id,
            Conversation.created_at,
            Conversation.updated_at,
            func.count(Message.id).label("message_count")
        ).where(
            Conversation.user_id == user_id  # CRITICAL: User isolation
        ).outerjoin(
            Message,
            (Message.conversation_id == Conversation.id) &
            (Message.user_id == user_id)
        ).group_by(
            Conversation.id
        ).order_by(
            Conversation.updated_at.desc()
        )

        result = await session.execute(statement)
        rows = result.all()

        return [
            {
                "id": row[0],
                "created_at": row[1],
                "updated_at": row[2],
                "message_count": row[3] or 0
            }
            for row in rows
        ]

    async def delete_conversation(
        self,
        session: AsyncSession,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            session: Database session
            conversation_id: Conversation to delete
            user_id: Requesting user ID (from JWT token)

        Returns:
            True if deleted, False if not found or not owned

        Guarantees:
            - Ownership verification before deletion
            - Cascading delete of all messages via ORM relationship
            - Single transaction (atomic operation)
        """
        conversation = await self.get_conversation(session, conversation_id, user_id)
        if not conversation:
            logger.warning(
                f"User {user_id} attempted to delete conversation {conversation_id} they don't own"
            )
            return False

        await session.delete(conversation)
        await session.commit()

        logger.info(f"Deleted conversation {conversation_id} and its messages (user {user_id})")
        return True

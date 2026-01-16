"""
Unit tests for Conversation Service.

Tests conversation CRUD operations with user isolation.
Verifies:
- Conversation creation
- Conversation retrieval with ownership check
- Message appending
- History loading
- User isolation enforcement
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatbot.services.conversation_service import ConversationService
from src.chatbot.models import Conversation, Message


class TestConversationService:
    """Test ConversationService."""

    @pytest.mark.asyncio
    async def test_create_conversation(self):
        """Test creating a conversation."""
        session = AsyncMock(spec=AsyncSession)
        user_id = str(uuid.uuid4())

        service = ConversationService()
        conversation = await service.create_conversation(
            session=session,
            user_id=user_id
        )

        assert conversation.user_id == user_id
        assert conversation.id is not None
        assert session.add.called
        assert session.commit.called
        assert session.refresh.called

    @pytest.mark.asyncio
    async def test_get_conversation_owned_by_user(self):
        """Test retrieving a conversation owned by user."""
        session = AsyncMock(spec=AsyncSession)
        user_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        # Mock conversation
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = conversation
        session.execute.return_value = mock_result

        service = ConversationService()
        result = await service.get_conversation(
            session=session,
            conversation_id=conversation_id,
            user_id=user_id
        )

        assert result is not None
        assert result.id == conversation_id
        assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_conversation_user_isolation(self):
        """Test that user cannot access other user's conversation."""
        session = AsyncMock(spec=AsyncSession)
        user_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        # Mock not found (user doesn't own conversation)
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        session.execute.return_value = mock_result

        service = ConversationService()
        result = await service.get_conversation(
            session=session,
            conversation_id=conversation_id,
            user_id=user_id  # Different user trying to access
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_append_message(self):
        """Test appending a message to conversation."""
        session = AsyncMock(spec=AsyncSession)
        user_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        # Mock conversation
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = conversation
        session.execute.return_value = mock_result

        service = ConversationService()
        message = await service.append_message(
            session=session,
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content="Hello"
        )

        assert message.conversation_id == conversation_id
        assert message.user_id == user_id
        assert message.role == "user"
        assert message.content == "Hello"
        assert session.add.call_count >= 2  # message + conversation
        assert session.commit.called

    @pytest.mark.asyncio
    async def test_append_message_not_owned(self):
        """Test appending message to conversation user doesn't own."""
        session = AsyncMock(spec=AsyncSession)
        user_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        # Mock conversation not found
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        session.execute.return_value = mock_result

        service = ConversationService()

        with pytest.raises(ValueError, match="not found"):
            await service.append_message(
                session=session,
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content="Hello"
            )

    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        """Test loading conversation history."""
        session = AsyncMock(spec=AsyncSession)
        user_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        # Mock conversation
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Mock messages
        msg1 = Message(
            id=str(uuid.uuid4()),
            user_id=user_id,
            conversation_id=conversation_id,
            role="user",
            content="Hi",
            created_at=datetime.utcnow()
        )
        msg2 = Message(
            id=str(uuid.uuid4()),
            user_id=user_id,
            conversation_id=conversation_id,
            role="assistant",
            content="Hello!",
            created_at=datetime.utcnow()
        )

        # Mock first query (get_conversation)
        conv_result = AsyncMock()
        conv_result.scalars.return_value.first.return_value = conversation

        # Mock second query (messages)
        msg_result = AsyncMock()
        msg_result.scalars.return_value.all.return_value = [msg1, msg2]

        session.execute.side_effect = [conv_result, msg_result]

        service = ConversationService()
        history = await service.get_conversation_history(
            session=session,
            conversation_id=conversation_id,
            user_id=user_id
        )

        assert len(history) == 2
        assert history[0].content == "Hi"
        assert history[1].content == "Hello!"

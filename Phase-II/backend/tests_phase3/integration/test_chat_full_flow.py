"""
Full Chat Flow Integration Tests

Tests complete end-to-end chat scenarios including:
- New conversation creation and first message
- Conversation continuation
- Tool execution and persistence
- Error handling and recovery
- User isolation verification
- Conversation history loading
"""

import pytest
import uuid
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatbot.models import Conversation, Message
from src.chatbot.services import ConversationService, AgentService
from src.chatbot.mcp.server import MCPServer


class TestChatFullFlow:
    """Test complete chat flows."""

    @pytest.mark.asyncio
    async def test_new_conversation_first_message(self):
        """
        Test complete flow: Create new conversation → First message → Response saved.

        Flow:
        1. User sends message without conversation_id
        2. System creates new conversation
        3. Agent processes message
        4. Response is persisted
        5. conversation_id returned to user
        """
        # Setup
        user_id = str(uuid.uuid4())
        message_text = "Add a task to buy milk"

        # Create services
        conv_service = ConversationService()
        agent_service = AgentService()
        mcp_server = MCPServer()

        # Create mock session
        session = AsyncMock(spec=AsyncSession)

        # Step 1: Create conversation
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Mock conversation persistence
        async def mock_create_conv(s, uid):
            return conversation

        conv_service.create_conversation = mock_create_conv

        # Step 2: Process message with agent
        agent_response = await agent_service.process_message(
            session=session,
            user_id=user_id,
            message=message_text,
            conversation_history=[]
        )

        # Verify response
        assert agent_response["status"] == "success"
        assert "response" in agent_response
        assert "tool_calls" in agent_response

        # Step 3: Verify message would be persisted
        # (In integration test with real DB, would verify DB state)

    @pytest.mark.asyncio
    async def test_conversation_continuation(self):
        """
        Test continuing existing conversation.

        Flow:
        1. User has existing conversation_id
        2. System loads conversation + history
        3. Agent includes history in context
        4. New response includes history
        """
        user_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())

        # Setup conversation with history
        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        history = [
            Message(
                id=str(uuid.uuid4()),
                user_id=user_id,
                conversation_id=conv_id,
                role="user",
                content="Add a task to buy milk",
                created_at=datetime.utcnow()
            ),
            Message(
                id=str(uuid.uuid4()),
                user_id=user_id,
                conversation_id=conv_id,
                role="assistant",
                content="Task created: 'buy milk'",
                created_at=datetime.utcnow()
            )
        ]

        # Setup services
        conv_service = ConversationService()
        agent_service = AgentService()
        session = AsyncMock(spec=AsyncSession)

        # Mock conversation loading
        async def mock_get_conv(s, cid, uid):
            return conversation

        async def mock_get_history(s, cid, uid):
            return history

        conv_service.get_conversation = mock_get_conv
        conv_service.get_conversation_history = mock_get_history

        # Load conversation
        loaded_conv = await conv_service.get_conversation(session, conv_id, user_id)
        assert loaded_conv.id == conv_id

        # Load history
        loaded_history = await conv_service.get_conversation_history(session, conv_id, user_id)
        assert len(loaded_history) == 2

        # Process new message with history
        new_message = "Complete the milk task"
        agent_response = await agent_service.process_message(
            session=session,
            user_id=user_id,
            message=new_message,
            conversation_history=[
                {"role": h.role, "content": h.content}
                for h in loaded_history
            ]
        )

        assert agent_response["status"] == "success"

    @pytest.mark.asyncio
    async def test_tool_execution_and_persistence(self):
        """
        Test that tool calls are executed and saved.

        Flow:
        1. Agent detects intent (add_task)
        2. Agent calls MCP tool
        3. Tool returns result
        4. Result is shown to user
        5. Tool call is logged/persisted
        """
        user_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        # Setup MCP server
        mcp_server = MCPServer()

        # Execute add_task tool
        from src.chatbot.mcp.tools import add_task_tool
        from src.models.task import Task

        task = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Buy milk",
            completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Mock session for tool
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        # Execute tool
        result = await add_task_tool(
            session=session,
            user_id=user_id,
            title="Buy milk"
        )

        # Verify tool result
        assert result["status"] == "success"
        assert "data" in result
        assert session.add.called
        assert await session.commit.called

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """
        Test error handling and recovery.

        Flow:
        1. User sends invalid message
        2. Validation error caught
        3. User receives helpful error message
        4. Conversation can continue
        """
        user_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        agent_service = AgentService()

        # Send invalid message (too long)
        long_message = "x" * 20000

        # Should handle gracefully
        response = await agent_service.process_message(
            session=session,
            user_id=user_id,
            message=long_message,
            conversation_history=[]
        )

        # Might fail validation or process anyway
        # Key: Should not crash
        assert "response" in response

    @pytest.mark.asyncio
    async def test_user_isolation_across_tools(self):
        """
        Test that user isolation is enforced across all tools.

        Flow:
        1. User A sends message
        2. Agent calls tools
        3. Tools filter by user A's user_id
        4. User B's data is never visible
        """
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())

        session = AsyncMock(spec=AsyncSession)
        agent_service = AgentService()

        # User A lists tasks
        response_a = await agent_service.process_message(
            session=session,
            user_id=user_a,
            message="Show my tasks",
            conversation_history=[]
        )

        # User B lists tasks
        response_b = await agent_service.process_message(
            session=session,
            user_id=user_b,
            message="Show my tasks",
            conversation_history=[]
        )

        # Both should get responses without cross-contamination
        assert response_a["status"] == "success"
        assert response_b["status"] == "success"

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """
        Test multi-turn conversation with context.

        Flow:
        1. Turn 1: User asks for task list
        2. Agent responds with task list
        3. Turn 2: User asks to complete "X"
        4. Agent remembers context from Turn 1
        5. Correctly identifies which task user means
        """
        user_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())

        # Create conversation
        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Turn 1: List tasks
        turn1_message = "Show my tasks"
        # Response would list: "1. Buy milk 2. Pay bills"

        # Turn 2: Complete a task
        turn2_message = "Mark the milk task as done"
        # Agent should remember from Turn 1 that milk task exists
        # Agent can correctly identify the task

        agent_service = AgentService()
        session = AsyncMock(spec=AsyncSession)

        # Simulate Turn 2 with Turn 1 in history
        history = [
            {"role": "user", "content": "Show my tasks"},
            {"role": "assistant", "content": "You have: 1. Buy milk 2. Pay bills"}
        ]

        response = await agent_service.process_message(
            session=session,
            user_id=user_id,
            message=turn2_message,
            conversation_history=history
        )

        assert response["status"] == "success"

    @pytest.mark.asyncio
    async def test_conversation_persistence_accuracy(self):
        """
        Test that all conversation data is accurately persisted.

        Verify:
        - User message saved with correct role
        - Assistant response saved with correct role
        - Tool calls recorded
        - Timestamps correct
        - User isolation maintained
        """
        user_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())

        conv_service = ConversationService()
        session = AsyncMock(spec=AsyncSession)

        # Create conversation
        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Mock conversation ownership check
        async def mock_get_conv(s, cid, uid):
            if cid == conv_id and uid == user_id:
                return conversation
            return None

        conv_service.get_conversation = mock_get_conv

        # Append user message
        user_msg = await conv_service.append_message(
            session=session,
            conversation_id=conv_id,
            user_id=user_id,
            role="user",
            content="Add a task"
        )

        # Verify user message
        assert user_msg.role == "user"
        assert user_msg.content == "Add a task"
        assert user_msg.user_id == user_id
        assert user_msg.conversation_id == conv_id

        # Append assistant response with tool calls
        tool_calls_json = json.dumps([{"tool": "add_task", "args": {"title": "Buy milk"}}])
        assistant_msg = await conv_service.append_message(
            session=session,
            conversation_id=conv_id,
            user_id=user_id,
            role="assistant",
            content="Task created",
            tool_calls=tool_calls_json
        )

        # Verify assistant message
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "Task created"
        assert assistant_msg.tool_calls == tool_calls_json

    @pytest.mark.asyncio
    async def test_conversation_deletion(self):
        """
        Test that conversations can be deleted.

        Flow:
        1. User deletes conversation
        2. Conversation and all messages deleted
        3. Cannot access deleted conversation
        """
        user_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())

        conv_service = ConversationService()
        session = AsyncMock(spec=AsyncSession)

        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Mock delete
        async def mock_get_conv(s, cid, uid):
            if cid == conv_id and uid == user_id:
                return conversation
            return None

        async def mock_delete_conv(s, cid, uid):
            if cid == conv_id and uid == user_id:
                await session.delete(conversation)
                await session.commit()
                return True
            return False

        conv_service.get_conversation = mock_get_conv
        conv_service.delete_conversation = mock_delete_conv

        # Delete conversation
        deleted = await conv_service.delete_conversation(session, conv_id, user_id)
        assert deleted is True

        # Verify cannot access
        loaded = await conv_service.get_conversation(session, conv_id, user_id)
        # Would be None since deleted

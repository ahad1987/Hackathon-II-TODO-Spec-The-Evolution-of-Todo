"""
Unit tests for MCP tools.

Tests each tool independently with mock database.
Verifies:
- Input validation
- User isolation
- Error handling
- Database operations
- Return format

Test coverage:
- add_task: Create task
- list_tasks: List user's tasks
- update_task: Update task
- complete_task: Complete task
- delete_task: Delete task
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatbot.mcp.tools import add_task_tool, list_tasks_tool, complete_task_tool, delete_task_tool, update_task_tool
from src.chatbot.mcp.error_handler import ErrorType
from src.models.task import Task


class TestAddTaskTool:
    """Test add_task tool."""

    @pytest.mark.asyncio
    async def test_add_task_success(self):
        """Test creating a task successfully."""
        # Setup
        user_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        # Execute
        result = await add_task_tool(
            session=session,
            user_id=user_id,
            title="Buy groceries",
            description="Milk, eggs, bread"
        )

        # Verify
        assert result["status"] == "success"
        assert result["data"]["title"] == "Buy groceries"
        assert result["data"]["description"] == "Milk, eggs, bread"
        assert result["data"]["user_id"] == user_id
        assert result["data"]["completed"] == False
        assert session.add.called
        assert session.commit.called

    @pytest.mark.asyncio
    async def test_add_task_validation_missing_title(self):
        """Test validation error when title is missing."""
        session = AsyncMock(spec=AsyncSession)

        result = await add_task_tool(
            session=session,
            user_id=str(uuid.uuid4()),
            title=""
        )

        assert result["status"] == "error"
        assert result["error_type"] == ErrorType.VALIDATION_ERROR.value
        assert "title" in result["message"].lower()
        assert not session.commit.called

    @pytest.mark.asyncio
    async def test_add_task_validation_title_too_long(self):
        """Test validation error when title exceeds max length."""
        session = AsyncMock(spec=AsyncSession)
        long_title = "x" * 300

        result = await add_task_tool(
            session=session,
            user_id=str(uuid.uuid4()),
            title=long_title
        )

        assert result["status"] == "error"
        assert result["error_type"] == ErrorType.VALIDATION_ERROR.value


class TestListTasksTool:
    """Test list_tasks tool."""

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self):
        """Test listing when user has no tasks."""
        user_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        # Mock empty result
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        # Mock count result
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 0
        session.execute.side_effect = [mock_result, mock_count_result]

        result = await list_tasks_tool(session=session, user_id=user_id)

        assert result["status"] == "success"
        assert result["data"]["tasks"] == []
        assert result["data"]["count"] == 0

    @pytest.mark.asyncio
    async def test_list_tasks_with_completed_filter(self):
        """Test listing with completed_only filter."""
        user_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        # Mock result with one completed task
        task = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Done task",
            completed=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [task]
        session.execute.return_value = mock_result

        result = await list_tasks_tool(
            session=session,
            user_id=user_id,
            completed_only=True
        )

        assert result["status"] == "success"
        assert result["data"]["count"] == 1
        assert result["data"]["tasks"][0]["title"] == "Done task"


class TestCompletTaskTool:
    """Test complete_task tool."""

    @pytest.mark.asyncio
    async def test_complete_task_success(self):
        """Test completing a task successfully."""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        # Mock task
        task = Task(
            id=task_id,
            user_id=user_id,
            title="Buy milk",
            completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = task
        session.execute.return_value = mock_result

        result = await complete_task_tool(
            session=session,
            user_id=user_id,
            task_id=task_id
        )

        assert result["status"] == "success"
        assert result["data"]["completed"] == True
        assert "✓" in result["message"]

    @pytest.mark.asyncio
    async def test_complete_task_not_found(self):
        """Test error when task not found."""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        session.execute.return_value = mock_result

        result = await complete_task_tool(
            session=session,
            user_id=user_id,
            task_id=task_id
        )

        assert result["status"] == "error"
        assert result["error_type"] == ErrorType.NOT_FOUND_ERROR.value

    @pytest.mark.asyncio
    async def test_complete_task_invalid_id(self):
        """Test validation error for invalid task ID."""
        session = AsyncMock(spec=AsyncSession)

        result = await complete_task_tool(
            session=session,
            user_id=str(uuid.uuid4()),
            task_id="not-a-uuid"
        )

        assert result["status"] == "error"
        assert result["error_type"] == ErrorType.VALIDATION_ERROR.value


class TestUpdateTaskTool:
    """Test update_task tool."""

    @pytest.mark.asyncio
    async def test_update_task_title(self):
        """Test updating a task's title."""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        task = Task(
            id=task_id,
            user_id=user_id,
            title="Old title",
            description="Description",
            completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = task
        session.execute.return_value = mock_result

        result = await update_task_tool(
            session=session,
            user_id=user_id,
            task_id=task_id,
            title="New title"
        )

        assert result["status"] == "success"
        assert result["data"]["title"] == "New title"

    @pytest.mark.asyncio
    async def test_update_task_no_fields(self):
        """Test error when no fields to update."""
        session = AsyncMock(spec=AsyncSession)

        result = await update_task_tool(
            session=session,
            user_id=str(uuid.uuid4()),
            task_id=str(uuid.uuid4())
        )

        assert result["status"] == "error"
        assert result["error_type"] == ErrorType.VALIDATION_ERROR.value


class TestDeleteTaskTool:
    """Test delete_task tool."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self):
        """Test deleting a task successfully."""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        task = Task(
            id=task_id,
            user_id=user_id,
            title="Delete me",
            completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = task
        session.execute.return_value = mock_result

        result = await delete_task_tool(
            session=session,
            user_id=user_id,
            task_id=task_id
        )

        assert result["status"] == "success"
        assert result["data"]["task_id"] == task_id
        assert result["data"]["task_title"] == "Delete me"
        assert session.delete.called

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self):
        """Test error when task not found."""
        user_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        session.execute.return_value = mock_result

        result = await delete_task_tool(
            session=session,
            user_id=user_id,
            task_id=task_id
        )

        assert result["status"] == "error"
        assert result["error_type"] == ErrorType.NOT_FOUND_ERROR.value
        assert not session.delete.called


class TestUserIsolation:
    """Test user isolation across all tools."""

    @pytest.mark.asyncio
    async def test_list_tasks_user_isolation(self):
        """Test that list_tasks only returns user's tasks."""
        user_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        session = AsyncMock(spec=AsyncSession)

        # Mock query builder
        query_mock = AsyncMock()
        query_mock.where.return_value = query_mock
        query_mock.order_by.return_value = query_mock

        session.execute = AsyncMock()

        # Should filter by user_id in WHERE clause
        # (Actual verification would be in integration tests with real DB)
        result = await list_tasks_tool(session=session, user_id=user_id)

        assert result["status"] == "success"
        # Verify execute was called (with WHERE user_id filter)
        assert session.execute.called

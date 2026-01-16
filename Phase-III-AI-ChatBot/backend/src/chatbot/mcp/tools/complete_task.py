"""
MCP Tool: complete_task

Marks a task as complete.

Input:
    - task_id: str (required, must be UUID)
    - user_id: str (extracted from JWT token by caller)

Output (on success):
    - Updated task with completed=true

Error cases:
    - validation_error: task_id invalid format
    - not_found_error: task doesn't exist
    - authorization_error: task not owned by user
    - internal_error: database failure

Guarantees:
    - User isolation: verifies task_id is owned by user_id
    - Idempotent: marking already-complete task is safe (no error)
    - Atomic: completion is single transaction
    - Returns full updated task data

Agent use:
    - Agent calls list_tasks first to get valid task IDs
    - Agent extracts task_id from user's language ("complete buying groceries")
    - Agent verifies task_id from list_tasks matches user's intent
    - Agent confirms completion to user with returned task data
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from src.models.task import Task, TaskResponse
from src.chatbot.mcp.validators import MCPInputValidator
from src.chatbot.mcp.error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)


async def complete_task_tool(
    session: AsyncSession,
    user_id: str,
    task_id: str
) -> Dict[str, Any]:
    """
    Mark a task as complete.

    Args:
        session: Database session (async)
        user_id: Owner's user ID (from JWT token)
        task_id: Task ID to complete (required)

    Returns:
        Success dict with updated task, or error dict

    User isolation:
        - Verifies task is owned by user_id before completing
        - WHERE user_id = :user_id AND id = :task_id
    """
    try:
        # Validate task_id
        task_id = MCPInputValidator.validate_task_id(task_id)

        # Load task with user isolation check
        query = select(Task).where(
            (Task.id == task_id) & (Task.user_id == user_id)  # User isolation
        )
        result = await session.execute(query)
        task = result.scalars().first()

        if not task:
            logger.warning(f"Task {task_id} not found for user {user_id}")
            return MCPErrorHandler.handle_not_found_error("task", task_id)

        # Mark as complete
        task.completed = True
        task.updated_at = datetime.utcnow()

        # Persist changes
        session.add(task)
        await session.commit()
        await session.refresh(task)

        logger.info(f"Completed task {task_id} '{task.title}' for user {user_id}")

        # Return completed task
        task_response = TaskResponse.from_orm(task)
        return MCPErrorHandler.success_response(
            data=task_response.dict(),
            message=f"Task '{task.title}' marked as complete ✓"
        )

    except ValueError as e:
        logger.warning(f"Validation error in complete_task: {e}")
        return MCPErrorHandler.handle_validation_error(str(e))

    except Exception as e:
        logger.error(f"Error in complete_task: {e}", exc_info=True)
        return MCPErrorHandler.handle_unexpected_error(e)

"""
MCP Tool: delete_task

Permanently deletes a task.

Input:
    - task_id: str (required, must be UUID)
    - user_id: str (extracted from JWT token by caller)

Output (on success):
    - task_id: ID of deleted task
    - message: Confirmation message

Error cases:
    - validation_error: task_id invalid format
    - not_found_error: task doesn't exist
    - authorization_error: task not owned by user
    - internal_error: database failure

Guarantees:
    - User isolation: verifies task_id is owned by user_id
    - Permanent: deletion is irreversible (no soft delete)
    - Atomic: deletion is single transaction
    - Confirmation: returns task_id of deleted task

Agent use:
    - DESTRUCTIVE OPERATION: requires agent confirmation
    - Agent should ask user to confirm before calling this tool
    - Agent calls list_tasks first to verify task exists
    - Agent uses task_id from list_tasks results
    - Agent never hallucinated task IDs
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.task import Task
from src.chatbot.mcp.validators import MCPInputValidator
from src.chatbot.mcp.error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)


async def delete_task_tool(
    session: AsyncSession,
    user_id: str,
    task_id: str
) -> Dict[str, Any]:
    """
    Delete a task permanently.

    Args:
        session: Database session (async)
        user_id: Owner's user ID (from JWT token)
        task_id: Task ID to delete (required)

    Returns:
        Success dict with deleted task_id, or error dict

    User isolation:
        - Verifies task is owned by user_id before deleting
        - WHERE user_id = :user_id AND id = :task_id

    WARNING:
        - This is a destructive operation
        - Deletion is permanent and irreversible
        - Agent should confirm with user before calling
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

        # Store task info for response
        task_title = task.title

        # Delete task
        await session.delete(task)
        await session.commit()

        logger.info(f"Deleted task {task_id} '{task_title}' for user {user_id}")

        return MCPErrorHandler.success_response(
            data={
                "task_id": task_id,
                "task_title": task_title
            },
            message=f"Task '{task_title}' has been deleted"
        )

    except ValueError as e:
        logger.warning(f"Validation error in delete_task: {e}")
        return MCPErrorHandler.handle_validation_error(str(e))

    except Exception as e:
        logger.error(f"Error in delete_task: {e}", exc_info=True)
        return MCPErrorHandler.handle_unexpected_error(e)

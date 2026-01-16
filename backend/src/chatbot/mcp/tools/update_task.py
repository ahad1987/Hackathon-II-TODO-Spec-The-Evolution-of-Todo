"""
MCP Tool: update_task

Updates a task's title and/or description.

Input:
    - task_id: str (required, must be UUID)
    - user_id: str (extracted from JWT token by caller)
    - title: str (optional, 1-255 chars)
    - description: str (optional, max 5000 chars)

Output (on success):
    - Updated task with all fields

Error cases:
    - validation_error: task_id invalid, title/description invalid
    - not_found_error: task doesn't exist
    - authorization_error: task not owned by user
    - internal_error: database failure

Guarantees:
    - User isolation: verifies task_id is owned by user_id
    - Atomic: entire update is single transaction
    - Returns full updated task data

Agent use:
    - Agent calls list_tasks first to get valid task IDs
    - Agent extracts task_id from list_tasks results
    - Agent only updates fields explicitly provided
    - Agent never hallucinated task IDs (validates against list)
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.task import Task, TaskResponse
from src.chatbot.mcp.validators import MCPInputValidator
from src.chatbot.mcp.error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)


async def update_task_tool(
    session: AsyncSession,
    user_id: str,
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update task title and/or description.

    Args:
        session: Database session (async)
        user_id: Owner's user ID (from JWT token)
        task_id: Task ID to update (required)
        title: New title (optional)
        description: New description (optional)

    Returns:
        Success dict with updated task, or error dict

    User isolation:
        - Verifies task is owned by user_id before updating
        - WHERE user_id = :user_id AND id = :task_id
    """
    try:
        # Validate task_id
        task_id = MCPInputValidator.validate_task_id(task_id)

        # Validate optional fields
        if title is not None:
            title = MCPInputValidator.validate_title(title)
        if description is not None:
            description = MCPInputValidator.validate_description(description)

        # At least one field must be provided
        if title is None and description is None:
            return MCPErrorHandler.handle_validation_error(
                "At least one of title or description must be provided"
            )

        # Load task with user isolation check
        query = select(Task).where(
            (Task.id == task_id) & (Task.user_id == user_id)  # User isolation
        )
        result = await session.execute(query)
        task = result.scalars().first()

        if not task:
            logger.warning(f"Task {task_id} not found for user {user_id}")
            return MCPErrorHandler.handle_not_found_error("task", task_id)

        # Update fields
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description

        # Persist changes
        session.add(task)
        await session.commit()
        await session.refresh(task)

        logger.info(f"Updated task {task_id} for user {user_id}")

        # Return updated task
        task_response = TaskResponse.from_orm(task)
        return MCPErrorHandler.success_response(
            data=task_response.dict(),
            message=f"Task updated successfully"
        )

    except ValueError as e:
        logger.warning(f"Validation error in update_task: {e}")
        return MCPErrorHandler.handle_validation_error(str(e))

    except Exception as e:
        logger.error(f"Error in update_task: {e}", exc_info=True)
        return MCPErrorHandler.handle_unexpected_error(e)

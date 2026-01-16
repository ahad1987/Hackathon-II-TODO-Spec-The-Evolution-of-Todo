"""
MCP Tool: add_task

Creates a new task for the user.

Input:
    - title: str (required, 1-255 chars)
    - description: str (optional, max 5000 chars)
    - user_id: str (extracted from JWT token by caller)

Output (on success):
    - id: UUID of created task
    - user_id: Owner's user ID
    - title: Task title
    - description: Task description (if provided)
    - completed: false (new tasks are never completed)
    - created_at: ISO timestamp
    - updated_at: ISO timestamp

Error cases:
    - validation_error: title missing, too long, or invalid content
    - internal_error: database failure

Guarantees:
    - Task is immediately persisted to database
    - User isolation: task is scoped to user_id
    - Returns full task data so agent can confirm creation to user
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Task, TaskResponse
from src.chatbot.mcp.validators import MCPInputValidator
from src.chatbot.mcp.error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)


async def add_task_tool(
    session: AsyncSession,
    user_id: str,
    title: str,
    description: str = None
) -> Dict[str, Any]:
    """
    Create a new task.

    Args:
        session: Database session (async)
        user_id: Owner's user ID (from JWT token)
        title: Task title (required)
        description: Task description (optional)

    Returns:
        Success dict with created task data, or error dict

    User isolation:
        - Task is automatically scoped to user_id
        - User cannot create tasks for other users (no user_id parameter)
    """
    try:
        # Validate inputs
        title = MCPInputValidator.validate_title(title)
        if description:
            description = MCPInputValidator.validate_description(description)

        # Create task (scoped to user_id)
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            completed=False
        )

        # Persist to database
        session.add(task)
        await session.commit()
        await session.refresh(task)

        logger.info(f"[MCP] Created task {task.id} '{task.title}' for user {user_id}")
        logger.info(f"[MCP] Task details - completed: {task.completed}, created_at: {task.created_at}")

        # Return task response
        task_response = TaskResponse.from_orm(task)
        return MCPErrorHandler.success_response(
            data=task_response.dict(),
            message=f"Task '{title}' created successfully"
        )

    except ValueError as e:
        # Validation error
        logger.warning(f"Validation error in add_task: {e}")
        return MCPErrorHandler.handle_validation_error(str(e))

    except Exception as e:
        # Unexpected error
        logger.error(f"Error in add_task: {e}", exc_info=True)
        return MCPErrorHandler.handle_unexpected_error(e)

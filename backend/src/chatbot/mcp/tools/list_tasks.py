"""
MCP Tool: list_tasks

Lists all tasks for the current user.

Input:
    - user_id: str (extracted from JWT token by caller)
    - completed_only: bool (optional, default false)

Output (on success):
    - tasks: array of task objects, each with:
        - id: UUID
        - title: Task title
        - description: Task description (nullable)
        - completed: boolean
        - created_at: ISO timestamp
        - updated_at: ISO timestamp
    - count: total number of tasks returned
    - completed_count: number of completed tasks

Error cases:
    - internal_error: database failure

Guarantees:
    - Only returns user's own tasks (WHERE user_id = :user_id)
    - Tasks sorted by created_at (oldest first)
    - No pagination (returns all tasks)
    - Includes both pending and completed tasks (unless filtered)

Agent use:
    - Agent calls this FIRST when user asks about tasks
    - Agent uses task IDs to map user language ("complete buying groceries") to task_id
    - Agent prevents hallucinated task IDs (checks against actual list)
"""

import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlmodel import func

from src.models.task import Task, TaskListResponse
from src.chatbot.mcp.error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)


async def list_tasks_tool(
    session: AsyncSession,
    user_id: str,
    completed_only: bool = False
) -> Dict[str, Any]:
    """
    List all tasks for a user.

    Args:
        session: Database session (async)
        user_id: Owner's user ID (from JWT token)
        completed_only: Filter to completed tasks only (optional)

    Returns:
        Success dict with tasks array, or error dict

    User isolation:
        - WHERE user_id = :user_id filter on all queries
        - User only sees their own tasks
    """
    try:
        # Build query to list tasks
        query = select(Task).where(
            Task.user_id == user_id  # CRITICAL: User isolation
        )

        # Optional filter for completed tasks
        if completed_only:
            query = query.where(Task.completed == True)

        # Order by creation date (oldest first)
        query = query.order_by(Task.created_at.asc())

        # Execute query
        result = await session.execute(query)
        tasks = result.scalars().all()

        # Count completed tasks (for summary)
        count_query = select(func.count(Task.id)).where(
            and_(
                Task.user_id == user_id,
                Task.completed == True
            )
        )
        completed_result = await session.execute(count_query)
        completed_count = completed_result.scalar() or 0

        logger.debug(f"Listed {len(tasks)} tasks for user {user_id}" +
                    (f" (completed only)" if completed_only else ""))

        # Convert to response format
        task_responses = [TaskListResponse.from_orm(task) for task in tasks]

        return MCPErrorHandler.success_response(
            data={
                "tasks": [t.dict() for t in task_responses],
                "count": len(tasks),
                "completed_count": completed_count,
                "pending_count": len(tasks) - (completed_count if not completed_only else 0)
            }
        )

    except Exception as e:
        # Unexpected error
        logger.error(f"Error in list_tasks: {e}", exc_info=True)
        return MCPErrorHandler.handle_unexpected_error(e)

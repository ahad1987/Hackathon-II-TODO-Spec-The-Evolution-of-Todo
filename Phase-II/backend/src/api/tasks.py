"""
Task API endpoints.
Handles task CRUD operations with user isolation.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_session
from src.middleware.auth import get_current_user
from src.models.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from src.services.task_service import TaskService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/tasks", tags=["Tasks"])


async def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    """Dependency to get task service."""
    return TaskService(session)


@router.get("", response_model=List[TaskListResponse])
async def list_tasks(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get all tasks for the authenticated user.

    Returns:
    - List of tasks with id, title, description, completed, created_at, updated_at

    Status codes:
    - 200: Success
    - 401: Not authenticated
    - 500: Server error
    """
    logger.info(f"Fetching tasks for user: {user_id}")
    task_service = TaskService(session)
    tasks, error = await task_service.get_user_tasks(user_id)

    if error:
        logger.error(f"Failed to fetch tasks: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": error, "code": "TASK_FETCH_ERROR", "message": error},
        )

    logger.info(f"Retrieved {len(tasks)} tasks for user {user_id}")
    return tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new task for the authenticated user.

    Request body:
    - title: Task title (required, 1-255 characters)
    - description: Task description (optional, max 5000 characters)

    Returns:
    - id: Task ID
    - user_id: Owner's user ID
    - title: Task title
    - description: Task description
    - completed: Completion status (default: false)
    - created_at: Creation timestamp
    - updated_at: Last update timestamp

    Status codes:
    - 201: Task created
    - 400: Validation error
    - 401: Not authenticated
    - 500: Server error
    """
    logger.info(f"Creating task for user: {user_id}")
    task_service = TaskService(session)
    task, error = await task_service.create_task(user_id, task_data)

    if error:
        logger.warning(f"Task creation validation error: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error, "code": "TASK_CREATION_ERROR", "message": error},
        )

    logger.info(f"Task created: {task.id}")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str = Path(..., description="Task ID"),
    task_data: TaskUpdate = None,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a task (title, description, or completion status).

    Path parameters:
    - task_id: Task ID to update

    Request body:
    - title: New task title (optional)
    - description: New task description (optional)
    - completed: New completion status (optional)

    Returns:
    - Updated task with all fields

    Status codes:
    - 200: Task updated
    - 400: Validation error
    - 401: Not authenticated
    - 403: Forbidden (task belongs to another user)
    - 404: Task not found
    - 500: Server error
    """
    logger.info(f"Updating task {task_id} for user: {user_id}")
    task_service = TaskService(session)
    updated_task, error = await task_service.update_task(task_id, user_id, task_data)

    if error:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in error.lower() else status.HTTP_400_BAD_REQUEST
        logger.warning(f"Task update error: {error}")
        raise HTTPException(
            status_code=status_code,
            detail={"error": error, "code": "TASK_UPDATE_ERROR", "message": error},
        )

    logger.info(f"Task updated: {task_id}")
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a task permanently.

    Path parameters:
    - task_id: Task ID to delete

    Status codes:
    - 204: Task deleted
    - 401: Not authenticated
    - 403: Forbidden (task belongs to another user)
    - 404: Task not found
    - 500: Server error
    """
    logger.info(f"Deleting task {task_id} for user: {user_id}")
    task_service = TaskService(session)
    success, error = await task_service.delete_task(task_id, user_id)

    if not success:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in error.lower() else status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.warning(f"Task deletion error: {error}")
        raise HTTPException(
            status_code=status_code,
            detail={"error": error, "code": "TASK_DELETION_ERROR", "message": error},
        )

    logger.info(f"Task deleted: {task_id}")

"""
Task service module.
Handles task-related business logic (CRUD operations).
"""

import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from src.models.task import Task, TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def create_task(self, user_id: str, task_data: TaskCreate) -> tuple:
        """Create a new task for a user."""
        try:
            if not task_data.title or len(task_data.title.strip()) == 0:
                return None, "Task title cannot be empty"

            if len(task_data.title) > 255:
                return None, "Task title must be 255 characters or less"

            if task_data.description and len(task_data.description) > 5000:
                return None, "Task description must be 5000 characters or less"

            task = Task(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=task_data.title.strip(),
                description=task_data.description.strip() if task_data.description else None,
                completed=False,
            )

            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)

            logger.info(f"Task created: {task.id} for user {user_id}")
            return task, None

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            await self.session.rollback()
            return None, "Failed to create task"

    async def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Task]:
        """Get task by ID, ensuring user owns the task."""
        try:
            stmt = select(Task).where(
                (Task.id == task_id) & (Task.user_id == user_id)
            )
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting task: {e}")
            return None

    async def get_user_tasks(self, user_id: str) -> tuple:
        """Get all tasks for a user."""
        try:
            stmt = select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
            result = await self.session.execute(stmt)
            tasks = result.scalars().all()
            logger.info(f"Retrieved {len(tasks)} tasks for user {user_id}")
            return tasks, None
        except Exception as e:
            logger.error(f"Error getting user tasks: {e}")
            return [], "Failed to retrieve tasks"

    async def update_task(self, task_id: str, user_id: str, task_data: TaskUpdate) -> tuple:
        """Update a task (title, description, or completion status)."""
        try:
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return None, "Task not found or you don't have permission to edit it"

            if task_data.title is not None:
                if len(task_data.title.strip()) == 0:
                    return None, "Task title cannot be empty"
                if len(task_data.title) > 255:
                    return None, "Task title must be 255 characters or less"
                task.title = task_data.title.strip()

            if task_data.description is not None:
                if len(task_data.description) > 5000:
                    return None, "Task description must be 5000 characters or less"
                task.description = task_data.description.strip() if task_data.description else None

            if task_data.completed is not None:
                task.completed = task_data.completed

            task.updated_at = datetime.utcnow()

            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)

            logger.info(f"Task updated: {task.id}")
            return task, None

        except Exception as e:
            logger.error(f"Error updating task: {e}")
            await self.session.rollback()
            return None, "Failed to update task"

    async def delete_task(self, task_id: str, user_id: str) -> tuple:
        """Delete a task permanently."""
        try:
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return False, "Task not found or you don't have permission to delete it"

            await self.session.delete(task)
            await self.session.commit()

            logger.info(f"Task deleted: {task_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            await self.session.rollback()
            return False, "Failed to delete task"

    async def toggle_task_completion(self, task_id: str, user_id: str) -> tuple:
        """Toggle task completion status."""
        try:
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return None, "Task not found or you don't have permission to edit it"

            task.completed = not task.completed
            task.updated_at = datetime.utcnow()

            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)

            logger.info(f"Task completion toggled: {task.id} -> {task.completed}")
            return task, None

        except Exception as e:
            logger.error(f"Error toggling task completion: {e}")
            await self.session.rollback()
            return None, "Failed to update task"

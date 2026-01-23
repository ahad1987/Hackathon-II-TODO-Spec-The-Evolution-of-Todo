"""
Task service module.
Handles task-related business logic (CRUD operations).

Phase V Extensions:
- Recurring task handling (parse recurrence_pattern, set parent_recurring_task_id)
- Event publishing (task.created, task.updated, task.deleted, task.completed)
"""

import logging
logger = logging.getLogger(__name__)
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from src.models.task import Task, TaskCreate, TaskUpdate
from src.config import get_settings

# Phase V imports
try:
    from src.utils.recurrence import validate_pattern
    from src.dapr_integration.factory import get_publisher


    PHASE_V_ENABLED = True
except ImportError:
    PHASE_V_ENABLED = False
    logger.warning("Phase V modules not available - recurring tasks and events disabled")


settings = get_settings()


class TaskService:
    """Service for task operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def create_task(self, user_id: str, task_data: TaskCreate) -> tuple:
        """
        Create a new task for a user.

        Phase V: Handles recurrence patterns and publishes task.created event.
        """
        try:
            if not task_data.title or len(task_data.title.strip()) == 0:
                return None, "Task title cannot be empty"

            if len(task_data.title) > 255:
                return None, "Task title must be 255 characters or less"

            if task_data.description and len(task_data.description) > 5000:
                return None, "Task description must be 5000 characters or less"

            # Phase V: Validate recurrence pattern if provided
            if PHASE_V_ENABLED and task_data.recurrence_pattern:
                is_valid, error_msg = validate_pattern(task_data.recurrence_pattern)
                if not is_valid:
                    return None, f"Invalid recurrence pattern: {error_msg}"

            # Phase V: Validate due_date is in the future if provided
            if task_data.due_date and task_data.due_date < datetime.utcnow():
                return None, "Due date must be in the future"

            # Phase V: Validate reminder_offset if due_date provided
            if task_data.reminder_offset and not task_data.due_date:
                return None, "Reminder offset requires a due date"

            task = Task(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=task_data.title.strip(),
                description=task_data.description.strip() if task_data.description else None,
                completed=False,
                # Phase V fields
                recurrence_pattern=task_data.recurrence_pattern,
                recurrence_end_date=task_data.recurrence_end_date,
                due_date=task_data.due_date,
                reminder_offset=task_data.reminder_offset,
                reminder_status="pending" if task_data.reminder_offset else None,
            )

            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)

            logger.info(f"Task created: {task.id} for user {user_id}")

            # Phase V: Publish task.created event (T027)
            if PHASE_V_ENABLED and settings.DAPR_ENABLED:
                await self._publish_task_created_event(task)

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
        """
        Update a task (title, description, completion status, etc.).

        Phase V: Tracks changes and publishes task.updated event (T028).
        """
        try:
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return None, "Task not found or you don't have permission to edit it"

            # Phase V: Track changes for event publishing
            changes = {}

            if task_data.title is not None:
                if len(task_data.title.strip()) == 0:
                    return None, "Task title cannot be empty"
                if len(task_data.title) > 255:
                    return None, "Task title must be 255 characters or less"
                if task.title != task_data.title.strip():
                    changes["title"] = {"old": task.title, "new": task_data.title.strip()}
                    task.title = task_data.title.strip()

            if task_data.description is not None:
                if len(task_data.description) > 5000:
                    return None, "Task description must be 5000 characters or less"
                new_desc = task_data.description.strip() if task_data.description else None
                if task.description != new_desc:
                    changes["description"] = {"old": task.description, "new": new_desc}
                    task.description = new_desc

            if task_data.completed is not None:
                if task.completed != task_data.completed:
                    changes["completed"] = {"old": task.completed, "new": task_data.completed}
                    task.completed = task_data.completed

            # Phase V: Handle recurrence pattern updates
            if PHASE_V_ENABLED and task_data.recurrence_pattern is not None:
                if task_data.recurrence_pattern:
                    is_valid, error_msg = validate_pattern(task_data.recurrence_pattern)
                    if not is_valid:
                        return None, f"Invalid recurrence pattern: {error_msg}"
                if task.recurrence_pattern != task_data.recurrence_pattern:
                    changes["recurrence_pattern"] = {"old": task.recurrence_pattern, "new": task_data.recurrence_pattern}
                    task.recurrence_pattern = task_data.recurrence_pattern

            # Phase V: Handle due_date updates
            if task_data.due_date is not None:
                if task.due_date != task_data.due_date:
                    changes["due_date"] = {
                        "old": task.due_date.isoformat() if task.due_date else None,
                        "new": task_data.due_date.isoformat() if task_data.due_date else None
                    }
                    task.due_date = task_data.due_date

            # Phase V: Handle reminder_offset updates
            if task_data.reminder_offset is not None:
                if task.reminder_offset != task_data.reminder_offset:
                    changes["reminder_offset"] = {"old": task.reminder_offset, "new": task_data.reminder_offset}
                    task.reminder_offset = task_data.reminder_offset
                    task.reminder_status = "pending" if task_data.reminder_offset else None

            task.updated_at = datetime.utcnow()

            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)

            logger.info(f"Task updated: {task.id}")

            # Phase V: Publish task.updated event if there were changes (T028)
            if PHASE_V_ENABLED and settings.DAPR_ENABLED and changes:
                await self._publish_task_updated_event(task, changes)

            return task, None

        except Exception as e:
            logger.error(f"Error updating task: {e}")
            await self.session.rollback()
            return None, "Failed to update task"

    async def delete_task(self, task_id: str, user_id: str) -> tuple:
        """
        Delete a task permanently.

        Phase V: Publishes task.deleted event (T029).
        """
        try:
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return False, "Task not found or you don't have permission to delete it"

            # Phase V: Publish task.deleted event BEFORE deletion (T029)
            if PHASE_V_ENABLED and settings.DAPR_ENABLED:
                await self._publish_task_deleted_event(task)

            await self.session.delete(task)
            await self.session.commit()

            logger.info(f"Task deleted: {task_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            await self.session.rollback()
            return False, "Failed to delete task"

    async def toggle_task_completion(self, task_id: str, user_id: str) -> tuple:
        """
        Toggle task completion status.

        Phase V: Publishes task.completed event when task is marked as completed.
        """
        try:
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return None, "Task not found or you don't have permission to edit it"

            old_completed = task.completed
            task.completed = not task.completed
            task.updated_at = datetime.utcnow()

            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)

            logger.info(f"Task completion toggled: {task.id} -> {task.completed}")

            # Phase V: Publish task.completed event if task was just completed
            if PHASE_V_ENABLED and settings.DAPR_ENABLED and not old_completed and task.completed:
                await self._publish_task_completed_event(task)

            return task, None

        except Exception as e:
            logger.error(f"Error toggling task completion: {e}")
            await self.session.rollback()
            return None, "Failed to update task"

    # ========== Phase V: Event Publishing Methods ==========

    async def _publish_task_created_event(self, task: Task) -> None:
        """
        Publish task.created event to Dapr Pub/Sub (T027).

        Args:
            task: Created task object
        """
        try:
            publisher = get_publisher()
            success = publisher.publish_task_created(
                task_id=task.id,
                user_id=task.user_id,
                title=task.title,
                description=task.description,
                due_date=task.due_date.isoformat() if task.due_date else None,
                recurrence_pattern=task.recurrence_pattern,
                reminder_offset=task.reminder_offset
            )
            if success:
                logger.info(f"Published task.created event for task {task.id}")
            else:
                logger.warning(f"Failed to publish task.created event for task {task.id}")
        except Exception as e:
            logger.error(f"Error publishing task.created event: {e}", exc_info=True)

    async def _publish_task_updated_event(self, task: Task, changes: Dict[str, Dict[str, Any]]) -> None:
        """
        Publish task.updated event to Dapr Pub/Sub (T028).

        Args:
            task: Updated task object
            changes: Dictionary of field changes {field_name: {"old": value, "new": value}}
        """
        try:
            publisher = get_publisher()
            success = publisher.publish_task_updated(
                task_id=task.id,
                user_id=task.user_id,
                changes=changes
            )
            if success:
                logger.info(f"Published task.updated event for task {task.id}")
            else:
                logger.warning(f"Failed to publish task.updated event for task {task.id}")
        except Exception as e:
            logger.error(f"Error publishing task.updated event: {e}", exc_info=True)

    async def _publish_task_deleted_event(self, task: Task) -> None:
        """
        Publish task.deleted event to Dapr Pub/Sub (T029).

        Args:
            task: Deleted task object
        """
        try:
            publisher = get_publisher()
            success = publisher.publish_task_deleted(
                task_id=task.id,
                user_id=task.user_id
            )
            if success:
                logger.info(f"Published task.deleted event for task {task.id}")
            else:
                logger.warning(f"Failed to publish task.deleted event for task {task.id}")
        except Exception as e:
            logger.error(f"Error publishing task.deleted event: {e}", exc_info=True)

    async def _publish_task_completed_event(self, task: Task) -> None:
        """
        Publish task.completed event to Dapr Pub/Sub.

        Args:
            task: Completed task object
        """
        try:
            publisher = get_publisher()
            success = publisher.publish_task_completed(
                task_id=task.id,
                user_id=task.user_id,
                completed_at=task.updated_at.isoformat()
            )
            if success:
                logger.info(f"Published task.completed event for task {task.id}")
            else:
                logger.warning(f"Failed to publish task.completed event for task {task.id}")
        except Exception as e:
            logger.error(f"Error publishing task.completed event: {e}", exc_info=True)

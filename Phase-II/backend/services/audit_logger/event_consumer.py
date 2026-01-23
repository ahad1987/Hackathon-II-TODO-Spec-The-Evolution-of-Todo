"""
Audit Logger Event Consumer for Phase V (T059, T061)

Handles all task events from Dapr Pub/Sub:
- task.created: Log task creation
- task.updated: Log task updates with changes
- task.completed: Log task completion
- task.deleted: Log task deletion

All events stored immutably in task_events table.

Constitutional Compliance:
- Idempotent event handling (via event_id deduplication)
- Graceful error recovery
- Complete payload preservation
"""

import logging
from typing import Dict, Any

from storage import get_audit_storage

logger = logging.getLogger(__name__)


async def handle_task_created_event(event_data: Dict[str, Any]) -> None:
    """
    Handle task.created event (T061).

    Persists event to task_events table.

    Args:
        event_data: CloudEvent data from Dapr
    """
    try:
        # Extract CloudEvent data
        data = event_data.get("data", {})
        event_id = data.get("event_id")
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        timestamp = data.get("timestamp")

        if not event_id or not task_id or not user_id:
            logger.warning("Missing required fields in task.created event")
            return

        # Write to audit log
        storage = get_audit_storage()
        success = await storage.write_event(
            event_id=event_id,
            event_type="task.created",
            task_id=task_id,
            user_id=user_id,
            payload=data,
            correlation_id=data.get("correlation_id")
        )

        if success:
            logger.info(f"Logged task.created event for task {task_id}")
        else:
            logger.warning(f"Failed to log task.created event for task {task_id}")

    except Exception as e:
        logger.error(f"Error handling task.created event: {e}", exc_info=True)


async def handle_task_updated_event(event_data: Dict[str, Any]) -> None:
    """
    Handle task.updated event (T061).

    Persists event to task_events table with changes.

    Args:
        event_data: CloudEvent data from Dapr
    """
    try:
        # Extract CloudEvent data
        data = event_data.get("data", {})
        event_id = data.get("event_id")
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        changes = data.get("changes", {})

        if not event_id or not task_id or not user_id:
            logger.warning("Missing required fields in task.updated event")
            return

        # Write to audit log
        storage = get_audit_storage()
        success = await storage.write_event(
            event_id=event_id,
            event_type="task.updated",
            task_id=task_id,
            user_id=user_id,
            payload={
                **data,
                "changes": changes
            },
            correlation_id=data.get("correlation_id")
        )

        if success:
            logger.info(f"Logged task.updated event for task {task_id} (changes: {len(changes)})")
        else:
            logger.warning(f"Failed to log task.updated event for task {task_id}")

    except Exception as e:
        logger.error(f"Error handling task.updated event: {e}", exc_info=True)


async def handle_task_completed_event(event_data: Dict[str, Any]) -> None:
    """
    Handle task.completed event (T061).

    Persists event to task_events table.

    Args:
        event_data: CloudEvent data from Dapr
    """
    try:
        # Extract CloudEvent data
        data = event_data.get("data", {})
        event_id = data.get("event_id")
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        completed_at = data.get("completed_at")

        if not event_id or not task_id or not user_id:
            logger.warning("Missing required fields in task.completed event")
            return

        # Write to audit log
        storage = get_audit_storage()
        success = await storage.write_event(
            event_id=event_id,
            event_type="task.completed",
            task_id=task_id,
            user_id=user_id,
            payload={
                **data,
                "completed_at": completed_at
            },
            correlation_id=data.get("correlation_id")
        )

        if success:
            logger.info(f"Logged task.completed event for task {task_id}")
        else:
            logger.warning(f"Failed to log task.completed event for task {task_id}")

    except Exception as e:
        logger.error(f"Error handling task.completed event: {e}", exc_info=True)


async def handle_task_deleted_event(event_data: Dict[str, Any]) -> None:
    """
    Handle task.deleted event (T061).

    Persists event to task_events table.

    Args:
        event_data: CloudEvent data from Dapr
    """
    try:
        # Extract CloudEvent data
        data = event_data.get("data", {})
        event_id = data.get("event_id")
        task_id = data.get("task_id")
        user_id = data.get("user_id")

        if not event_id or not task_id or not user_id:
            logger.warning("Missing required fields in task.deleted event")
            return

        # Write to audit log
        storage = get_audit_storage()
        success = await storage.write_event(
            event_id=event_id,
            event_type="task.deleted",
            task_id=task_id,
            user_id=user_id,
            payload=data,
            correlation_id=data.get("correlation_id")
        )

        if success:
            logger.info(f"Logged task.deleted event for task {task_id}")
        else:
            logger.warning(f"Failed to log task.deleted event for task {task_id}")

    except Exception as e:
        logger.error(f"Error handling task.deleted event: {e}", exc_info=True)

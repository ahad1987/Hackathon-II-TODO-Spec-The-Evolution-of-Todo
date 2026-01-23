"""
Notification Event Consumer for Phase V (T050, T051)

Handles all task events and reminder.triggered events from Dapr Pub/Sub:
- task.created: Notify user about new task
- task.updated: Notify user about changes
- task.completed: Notify user about completion
- task.deleted: Notify user about deletion
- reminder.triggered: Notify user about upcoming due date

Constitutional Compliance:
- Idempotent event handling
- Graceful error recovery
- Notifications sent within 2 seconds
"""

import logging
from typing import Dict, Any
from datetime import datetime

from services.notification.sse_handler import get_notification_manager

logger = logging.getLogger(__name__)


def format_notification(
    event_type: str,
    task_id: str,
    user_id: str,
    data: Dict[str, Any]
) -> dict:
    """
    Format event data into notification format.

    Args:
        event_type: Type of event
        task_id: Task ID
        user_id: User ID
        data: Event data

    Returns:
        dict: Formatted notification
    """
    return {
        "type": "notification",
        "event": event_type,
        "task_id": task_id,
        "user_id": user_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


async def handle_task_created_event(event_data: Dict[str, Any]) -> None:
    """
    Handle task.created event (T051).

    Sends notification: "New task created: {title}"

    Args:
        event_data: CloudEvent data from Dapr
    """
    try:
        # Extract CloudEvent data
        data = event_data.get("data", {})
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        task_info = data.get("task", {})

        if not task_id or not user_id:
            logger.warning("Missing task_id or user_id in task.created event")
            return

        # Format notification
        notification = format_notification(
            event_type="task_created",
            task_id=task_id,
            user_id=user_id,
            data={
                "title": task_info.get("title", "Untitled"),
                "description": task_info.get("description"),
                "message": f"New task created: {task_info.get('title', 'Untitled')}"
            }
        )

        # Send to user
        manager = get_notification_manager()
        sent_count = await manager.send_notification(user_id, notification)

        logger.info(f"Sent task.created notification for task {task_id} to {sent_count} connection(s)")

    except Exception as e:
        logger.error(f"Error handling task.created event: {e}", exc_info=True)


async def handle_task_updated_event(event_data: Dict[str, Any]) -> None:
    """
    Handle task.updated event (T051).

    Sends notification: "Task updated: {title} - {changes}"

    Args:
        event_data: CloudEvent data from Dapr
    """
    try:
        # Extract CloudEvent data
        data = event_data.get("data", {})
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        changes = data.get("changes", {})

        if not task_id or not user_id:
            logger.warning("Missing task_id or user_id in task.updated event")
            return

        # Format changes for notification
        change_summary = []
        for field, change_data in changes.items():
            old_val = change_data.get("old")
            new_val = change_data.get("new")
            change_summary.append(f"{field}: {old_val} → {new_val}")

        # Format notification
        notification = format_notification(
            event_type="task_updated",
            task_id=task_id,
            user_id=user_id,
            data={
                "changes": changes,
                "change_summary": ", ".join(change_summary),
                "message": f"Task updated: {', '.join(change_summary)}"
            }
        )

        # Send to user
        manager = get_notification_manager()
        sent_count = await manager.send_notification(user_id, notification)

        logger.info(f"Sent task.updated notification for task {task_id} to {sent_count} connection(s)")

    except Exception as e:
        logger.error(f"Error handling task.updated event: {e}", exc_info=True)


async def handle_task_completed_event(event_data: Dict[str, Any]) -> None:
    """
    Handle task.completed event (T051).

    Sends notification: "Task completed: {title}"

    Args:
        event_data: CloudEvent data from Dapr
    """
    try:
        # Extract CloudEvent data
        data = event_data.get("data", {})
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        completed_at = data.get("completed_at")

        if not task_id or not user_id:
            logger.warning("Missing task_id or user_id in task.completed event")
            return

        # Format notification
        notification = format_notification(
            event_type="task_completed",
            task_id=task_id,
            user_id=user_id,
            data={
                "completed_at": completed_at,
                "message": f"Task completed!"
            }
        )

        # Send to user
        manager = get_notification_manager()
        sent_count = await manager.send_notification(user_id, notification)

        logger.info(f"Sent task.completed notification for task {task_id} to {sent_count} connection(s)")

    except Exception as e:
        logger.error(f"Error handling task.completed event: {e}", exc_info=True)


async def handle_task_deleted_event(event_data: Dict[str, Any]) -> None:
    """
    Handle task.deleted event (T051).

    Sends notification: "Task deleted"

    Args:
        event_data: CloudEvent data from Dapr
    """
    try:
        # Extract CloudEvent data
        data = event_data.get("data", {})
        task_id = data.get("task_id")
        user_id = data.get("user_id")

        if not task_id or not user_id:
            logger.warning("Missing task_id or user_id in task.deleted event")
            return

        # Format notification
        notification = format_notification(
            event_type="task_deleted",
            task_id=task_id,
            user_id=user_id,
            data={
                "message": "Task deleted"
            }
        )

        # Send to user
        manager = get_notification_manager()
        sent_count = await manager.send_notification(user_id, notification)

        logger.info(f"Sent task.deleted notification for task {task_id} to {sent_count} connection(s)")

    except Exception as e:
        logger.error(f"Error handling task.deleted event: {e}", exc_info=True)


async def handle_reminder_triggered_event(event_data: Dict[str, Any]) -> None:
    """
    Handle reminder.triggered event (T051).

    Sends notification: "Reminder: {title} is due in {time}"

    Args:
        event_data: CloudEvent data from Dapr
    """
    try:
        # Extract CloudEvent data
        data = event_data.get("data", {})
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        reminder_type = data.get("reminder_type")
        task_info = data.get("task", {})

        if not task_id or not user_id:
            logger.warning("Missing task_id or user_id in reminder.triggered event")
            return

        # Format notification
        title = task_info.get("title", "Untitled")
        due_date = task_info.get("due_date")

        notification = format_notification(
            event_type="reminder_triggered",
            task_id=task_id,
            user_id=user_id,
            data={
                "title": title,
                "due_date": due_date,
                "reminder_type": reminder_type,
                "message": f"Reminder: '{title}' is due soon!"
            }
        )

        # Send to user
        manager = get_notification_manager()
        sent_count = await manager.send_notification(user_id, notification)

        logger.info(f"Sent reminder.triggered notification for task {task_id} to {sent_count} connection(s)")

    except Exception as e:
        logger.error(f"Error handling reminder.triggered event: {e}", exc_info=True)

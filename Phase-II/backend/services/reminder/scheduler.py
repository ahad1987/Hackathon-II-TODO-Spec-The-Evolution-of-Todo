"""
Reminder Scheduler for Phase V (T042, T043)

Background scheduler that:
1. Checks priority queue every 10 seconds
2. Triggers due reminders
3. Publishes reminder.triggered events via Dapr
4. Persists queue snapshot every 5 minutes

Constitutional Compliance:
- Non-blocking background task
- Graceful shutdown
- Error recovery
"""

import logging
import asyncio
import os
from datetime import datetime
from typing import Optional
import httpx

from services.reminder.priority_queue import get_reminder_queue, save_reminders_to_db

logger = logging.getLogger(__name__)

# Configuration
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3500"))
PUBSUB_NAME = os.getenv("PUBSUB_NAME", "taskflow-pubsub")
CHECK_INTERVAL = 10  # Check queue every 10 seconds
PERSISTENCE_INTERVAL = 300  # Persist queue every 5 minutes (300 seconds)

# Global scheduler state
_scheduler_task: Optional[asyncio.Task] = None
_persistence_task: Optional[asyncio.Task] = None
_scheduler_running = False


async def publish_reminder_triggered_event(
    task_id: str,
    user_id: str,
    reminder_type: str,
    task_data: dict
) -> bool:
    """
    Publish reminder.triggered event via Dapr Pub/Sub (T043).

    Args:
        task_id: Task ID
        user_id: User ID to notify
        reminder_type: Type of reminder
        task_data: Additional task data for notification

    Returns:
        bool: True if published successfully

    Constitutional Compliance:
    - Uses Dapr Pub/Sub (NO direct Kafka)
    """
    try:
        # Prepare event data
        event_data = {
            "event_type": "reminder.triggered",
            "event_id": f"reminder-{task_id}-{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "task_id": task_id,
            "user_id": user_id,
            "reminder_type": reminder_type,
            "task": task_data
        }

        # Publish via Dapr Pub/Sub
        dapr_url = f"http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/{PUBSUB_NAME}/taskflow.tasks.reminder-triggered"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                dapr_url,
                json=event_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

        logger.info(f"Published reminder.triggered event for task {task_id}")
        return True

    except Exception as e:
        logger.error(f"Error publishing reminder.triggered event: {e}", exc_info=True)
        return False


async def process_due_reminders() -> int:
    """
    Process all due reminders from the queue (T042).

    Returns:
        int: Number of reminders triggered
    """
    try:
        queue = get_reminder_queue()
        now = datetime.utcnow()
        triggered_count = 0

        while True:
            # Peek at next reminder
            reminder = await queue.peek()

            if reminder is None:
                # Queue empty
                break

            if reminder.trigger_at > now:
                # Next reminder not due yet
                break

            # Pop and trigger reminder
            reminder = await queue.pop()
            logger.info(f"Triggering reminder for task {reminder.task_id}")

            # Publish reminder.triggered event
            success = await publish_reminder_triggered_event(
                task_id=reminder.task_id,
                user_id=reminder.user_id,
                reminder_type=reminder.reminder_type,
                task_data=reminder.task_data
            )

            if success:
                triggered_count += 1
            else:
                logger.warning(f"Failed to publish reminder for task {reminder.task_id}")

        if triggered_count > 0:
            logger.info(f"Triggered {triggered_count} reminders")

        return triggered_count

    except Exception as e:
        logger.error(f"Error processing due reminders: {e}", exc_info=True)
        return 0


async def reminder_scheduler_loop():
    """
    Main scheduler loop - checks queue every 10 seconds (T042).

    Constitutional Guarantee:
    - Non-blocking
    - Continues on errors
    - Graceful shutdown
    """
    logger.info("Reminder scheduler loop started")

    while _scheduler_running:
        try:
            await process_due_reminders()
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)

        # Wait 10 seconds before next check
        await asyncio.sleep(CHECK_INTERVAL)

    logger.info("Reminder scheduler loop stopped")


async def persistence_loop():
    """
    Persistence loop - saves queue snapshot every 5 minutes (T044).

    Constitutional Guarantee:
    - Non-blocking
    - Continues on errors
    - Graceful shutdown
    """
    logger.info("Reminder persistence loop started")

    while _scheduler_running:
        try:
            await asyncio.sleep(PERSISTENCE_INTERVAL)

            # Persist queue to database
            queue = get_reminder_queue()
            success = await save_reminders_to_db(queue)

            if success:
                logger.info("Queue snapshot persisted to database")
            else:
                logger.warning("Failed to persist queue snapshot")

        except Exception as e:
            logger.error(f"Error in persistence loop: {e}", exc_info=True)

    logger.info("Reminder persistence loop stopped")


async def start_reminder_scheduler():
    """
    Start the reminder scheduler background task.

    Constitutional Guarantee:
    - Non-blocking (runs in background)
    - Idempotent (safe to call multiple times)
    """
    global _scheduler_task, _persistence_task, _scheduler_running

    if _scheduler_running:
        logger.warning("Reminder scheduler already running - skipping start")
        return

    try:
        logger.info("Starting reminder scheduler...")

        _scheduler_running = True

        # Start scheduler loop
        _scheduler_task = asyncio.create_task(reminder_scheduler_loop())

        # Start persistence loop
        _persistence_task = asyncio.create_task(persistence_loop())

        logger.info("Reminder scheduler started successfully")
        logger.info(f"Checking queue every {CHECK_INTERVAL} seconds")
        logger.info(f"Persisting queue every {PERSISTENCE_INTERVAL} seconds")

    except Exception as e:
        logger.error(f"Failed to start reminder scheduler: {e}", exc_info=True)
        _scheduler_running = False
        raise


async def stop_reminder_scheduler():
    """
    Stop the reminder scheduler background task.

    Constitutional Guarantee:
    - Graceful shutdown (waits for current operations)
    - Idempotent (safe to call multiple times)
    """
    global _scheduler_task, _persistence_task, _scheduler_running

    if not _scheduler_running:
        logger.info("Reminder scheduler not running - skipping stop")
        return

    try:
        logger.info("Stopping reminder scheduler...")

        _scheduler_running = False

        # Wait for scheduler task to complete
        if _scheduler_task:
            await _scheduler_task
            _scheduler_task = None

        # Wait for persistence task to complete
        if _persistence_task:
            await _persistence_task
            _persistence_task = None

        logger.info("Reminder scheduler stopped successfully")

    except Exception as e:
        logger.error(f"Error stopping reminder scheduler: {e}", exc_info=True)
        _scheduler_running = False


def is_scheduler_running() -> bool:
    """
    Check if scheduler is currently running.

    Returns:
        bool: True if scheduler is running, False otherwise
    """
    return _scheduler_running

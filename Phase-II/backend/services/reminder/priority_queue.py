"""
Reminder Priority Queue for Phase V (T039, T044)

Min-heap priority queue using heapq for efficient reminder scheduling.
Supports persistence to database for crash recovery.

Constitutional Compliance:
- Thread-safe operations
- Snapshot persistence every 5 minutes
- Load from database on startup
"""

import logging
import heapq
import asyncio
import os
from typing import List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/todo_db")


@dataclass(order=True)
class ReminderItem:
    """
    Reminder item for priority queue.

    Attributes:
        trigger_at: When to trigger the reminder (used for heap ordering)
        task_id: Task ID to remind about
        user_id: User ID to notify
        reminder_type: Type of reminder (e.g., "due_date_reminder")
        task_data: Additional task data for notification
    """
    trigger_at: datetime
    task_id: str = field(compare=False)
    user_id: str = field(compare=False)
    reminder_type: str = field(compare=False)
    task_data: dict = field(default_factory=dict, compare=False)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "trigger_at": self.trigger_at.isoformat(),
            "task_id": self.task_id,
            "user_id": self.user_id,
            "reminder_type": self.reminder_type,
            "task_data": self.task_data
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReminderItem":
        """Create from dictionary."""
        return cls(
            trigger_at=datetime.fromisoformat(data["trigger_at"]),
            task_id=data["task_id"],
            user_id=data["user_id"],
            reminder_type=data["reminder_type"],
            task_data=data.get("task_data", {})
        )


class ReminderPriorityQueue:
    """
    Thread-safe priority queue for reminders using heapq (T039).

    Min-heap ordered by trigger_at timestamp.
    """

    def __init__(self):
        """Initialize empty priority queue."""
        self._queue: List[ReminderItem] = []
        self._lock = asyncio.Lock()

    def __len__(self) -> int:
        """Get queue size."""
        return len(self._queue)

    async def add(self, reminder: ReminderItem) -> None:
        """
        Add reminder to queue (T039).

        Args:
            reminder: ReminderItem to add

        Thread-safe operation.
        """
        async with self._lock:
            heapq.heappush(self._queue, reminder)
            logger.debug(f"Added reminder for task {reminder.task_id} at {reminder.trigger_at}")

    async def peek(self) -> Optional[ReminderItem]:
        """
        Peek at next reminder without removing it (T039).

        Returns:
            ReminderItem: Next reminder, or None if queue empty

        Thread-safe operation.
        """
        async with self._lock:
            if not self._queue:
                return None
            return self._queue[0]

    async def pop(self) -> Optional[ReminderItem]:
        """
        Remove and return next reminder from queue (T039).

        Returns:
            ReminderItem: Next reminder, or None if queue empty

        Thread-safe operation.
        """
        async with self._lock:
            if not self._queue:
                return None
            reminder = heapq.heappop(self._queue)
            logger.debug(f"Popped reminder for task {reminder.task_id}")
            return reminder

    async def remove(self, task_id: str) -> bool:
        """
        Remove all reminders for a specific task (T039).

        Args:
            task_id: Task ID to remove reminders for

        Returns:
            bool: True if any reminders were removed

        Thread-safe operation.
        """
        async with self._lock:
            original_size = len(self._queue)
            self._queue = [r for r in self._queue if r.task_id != task_id]
            heapq.heapify(self._queue)

            removed = original_size - len(self._queue)
            if removed > 0:
                logger.info(f"Removed {removed} reminder(s) for task {task_id}")
            return removed > 0

    async def get_all_reminders(self) -> List[ReminderItem]:
        """
        Get all reminders in queue (for persistence).

        Returns:
            List[ReminderItem]: All reminders in queue

        Thread-safe operation.
        """
        async with self._lock:
            return list(self._queue)

    async def clear(self) -> None:
        """
        Clear all reminders from queue.

        Thread-safe operation.
        """
        async with self._lock:
            self._queue.clear()
            logger.info("Cleared all reminders from queue")


# Global queue instance
_reminder_queue: Optional[ReminderPriorityQueue] = None


def get_reminder_queue() -> ReminderPriorityQueue:
    """
    Get global reminder queue instance.

    Returns:
        ReminderPriorityQueue: Global queue instance
    """
    global _reminder_queue
    if _reminder_queue is None:
        _reminder_queue = ReminderPriorityQueue()
    return _reminder_queue


# ========== Database Persistence (T044) ==========

async def save_reminders_to_db(queue: ReminderPriorityQueue) -> bool:
    """
    Save reminder queue snapshot to database (T044).

    Saves to reminder_schedule table for crash recovery.

    Args:
        queue: ReminderPriorityQueue to persist

    Returns:
        bool: True if saved successfully
    """
    try:
        import sys
        sys.path.insert(0, "/app/backend/src")
        sys.path.insert(0, os.path.abspath("../../src"))

        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import text

        reminders = await queue.get_all_reminders()

        if not reminders:
            logger.debug("No reminders to persist")
            return True

        db_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
        engine = create_async_engine(db_url, echo=False)

        async with AsyncSession(engine) as session:
            # Clear existing reminders (snapshot approach)
            await session.execute(text("DELETE FROM reminder_schedule WHERE status = 'pending'"))

            # Insert current reminders
            for reminder in reminders:
                query = text("""
                    INSERT INTO reminder_schedule (
                        reminder_id, task_id, user_id, trigger_at, reminder_type, status
                    ) VALUES (
                        gen_random_uuid(), :task_id, :user_id, :trigger_at, :reminder_type, 'pending'
                    )
                    ON CONFLICT (task_id) DO UPDATE SET
                        trigger_at = EXCLUDED.trigger_at,
                        reminder_type = EXCLUDED.reminder_type,
                        updated_at = NOW()
                """)

                await session.execute(query, {
                    "task_id": reminder.task_id,
                    "user_id": reminder.user_id,
                    "trigger_at": reminder.trigger_at,
                    "reminder_type": reminder.reminder_type
                })

            await session.commit()

        logger.info(f"Persisted {len(reminders)} reminders to database")
        return True

    except Exception as e:
        logger.error(f"Error persisting reminders to database: {e}", exc_info=True)
        return False


async def load_reminders_from_db(queue: ReminderPriorityQueue) -> bool:
    """
    Load reminder queue snapshot from database (T044).

    Loads from reminder_schedule table on startup.

    Args:
        queue: ReminderPriorityQueue to populate

    Returns:
        bool: True if loaded successfully
    """
    try:
        import sys
        sys.path.insert(0, "/app/backend/src")
        sys.path.insert(0, os.path.abspath("../../src"))

        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import text

        db_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
        engine = create_async_engine(db_url, echo=False)

        async with AsyncSession(engine) as session:
            # Load pending reminders
            query = text("""
                SELECT task_id, user_id, trigger_at, reminder_type
                FROM reminder_schedule
                WHERE status = 'pending' AND trigger_at > NOW()
                ORDER BY trigger_at ASC
            """)

            result = await session.execute(query)
            rows = result.fetchall()

            for row in rows:
                reminder = ReminderItem(
                    task_id=row[0],
                    user_id=row[1],
                    trigger_at=row[2],
                    reminder_type=row[3],
                    task_data={}
                )
                await queue.add(reminder)

            logger.info(f"Loaded {len(rows)} reminders from database")
            return True

    except Exception as e:
        logger.error(f"Error loading reminders from database: {e}", exc_info=True)
        return False

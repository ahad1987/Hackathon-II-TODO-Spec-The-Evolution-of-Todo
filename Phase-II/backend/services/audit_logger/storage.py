"""
Audit Log Storage Module for Phase V (T060, T062)

Stores audit events to task_events table with:
- Batch write optimization (buffer 100 events, flush every 1 second)
- Duplicate detection via event_id
- Monthly partitioning support
- Immutable audit trail

Constitutional Compliance:
- Thread-safe operations
- Graceful error handling
- Efficient batch writes
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from collections import deque
import json
import uuid

logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/todo_db")
BATCH_SIZE = 100
FLUSH_INTERVAL = 1.0  # seconds


class AuditLogStorage:
    """
    Audit log storage manager (T060, T062).

    Features:
    - Batch write optimization (buffer 100 events, flush every 1 second)
    - Duplicate detection via event_id
    - Automatic partition_key calculation
    - Async write operations
    """

    def __init__(self):
        """Initialize audit log storage."""
        self._buffer: deque = deque()
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

    async def write_event(
        self,
        event_id: str,
        event_type: str,
        task_id: str,
        user_id: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Write audit event to buffer (T060).

        Event will be flushed to database when:
        - Buffer reaches 100 events, OR
        - 1 second has elapsed since last flush

        Args:
            event_id: Unique event ID (for deduplication)
            event_type: Event type (task.created, task.updated, etc.)
            task_id: Task ID
            user_id: User ID
            payload: Event payload (stored as JSONB)
            correlation_id: Optional correlation ID

        Returns:
            bool: True if buffered successfully
        """
        try:
            # Create event record
            timestamp = datetime.utcnow()
            partition_key = date(timestamp.year, timestamp.month, 1)  # First day of month

            event = {
                "event_id": event_id,
                "event_type": event_type,
                "task_id": task_id,
                "user_id": user_id,
                "timestamp": timestamp,
                "payload": payload,
                "correlation_id": correlation_id,
                "partition_key": partition_key
            }

            async with self._lock:
                self._buffer.append(event)
                buffer_size = len(self._buffer)

            logger.debug(f"Buffered event {event_id} (buffer size: {buffer_size})")

            # Flush if buffer full
            if buffer_size >= BATCH_SIZE:
                logger.info(f"Buffer full ({buffer_size} events), flushing...")
                await self.flush()

            return True

        except Exception as e:
            logger.error(f"Error buffering event: {e}", exc_info=True)
            return False

    async def flush(self) -> int:
        """
        Flush buffered events to database (T062).

        Returns:
            int: Number of events flushed
        """
        try:
            # Get events from buffer
            async with self._lock:
                if not self._buffer:
                    return 0

                events = list(self._buffer)
                self._buffer.clear()

            logger.info(f"Flushing {len(events)} event(s) to database...")

            # Write to database
            import sys
            sys.path.insert(0, "/app/backend/src")
            sys.path.insert(0, os.path.abspath("../../src"))

            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy import text

            db_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
            engine = create_async_engine(db_url, echo=False)

            async with AsyncSession(engine) as session:
                for event in events:
                    # Insert event (ON CONFLICT DO NOTHING for deduplication)
                    query = text("""
                        INSERT INTO task_events (
                            event_id, event_type, task_id, user_id,
                            timestamp, payload, correlation_id, partition_key
                        ) VALUES (
                            :event_id, :event_type, :task_id, :user_id,
                            :timestamp, :payload, :correlation_id, :partition_key
                        )
                        ON CONFLICT (event_id) DO NOTHING
                    """)

                    await session.execute(query, {
                        "event_id": event["event_id"],
                        "event_type": event["event_type"],
                        "task_id": event["task_id"],
                        "user_id": event["user_id"],
                        "timestamp": event["timestamp"],
                        "payload": json.dumps(event["payload"]),
                        "correlation_id": event["correlation_id"],
                        "partition_key": event["partition_key"]
                    })

                await session.commit()

            logger.info(f"Flushed {len(events)} event(s) to database")
            return len(events)

        except Exception as e:
            logger.error(f"Error flushing events to database: {e}", exc_info=True)
            return 0

    async def flush_loop(self):
        """
        Background task to flush buffer every 1 second (T062).

        Constitutional Guarantee:
        - Non-blocking
        - Continues on errors
        - Graceful shutdown
        """
        logger.info("Flush loop started")

        while self._running:
            try:
                await asyncio.sleep(FLUSH_INTERVAL)

                # Flush buffer
                flushed_count = await self.flush()

                if flushed_count > 0:
                    logger.debug(f"Auto-flushed {flushed_count} event(s)")

            except asyncio.CancelledError:
                logger.info("Flush loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}", exc_info=True)

        logger.info("Flush loop stopped")

    async def start_background_task(self):
        """
        Start background flush task.

        Called on service startup.
        """
        if self._flush_task is None:
            self._running = True
            self._flush_task = asyncio.create_task(self.flush_loop())
            logger.info("Started flush background task")

    async def stop_background_task(self):
        """
        Stop background flush task and flush remaining events.

        Called on service shutdown.
        """
        if self._flush_task:
            self._running = False
            self._flush_task.cancel()
            await self._flush_task
            self._flush_task = None
            logger.info("Stopped flush background task")

        # Flush remaining events
        remaining = len(self._buffer)
        if remaining > 0:
            logger.info(f"Flushing {remaining} remaining event(s) on shutdown...")
            await self.flush()

    async def get_task_events(
        self,
        task_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get chronological event history for a task (T063).

        Args:
            task_id: Task ID
            limit: Maximum number of events to return

        Returns:
            List[Dict]: List of events in chronological order
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
                query = text("""
                    SELECT event_id, event_type, task_id, user_id,
                           timestamp, payload, correlation_id
                    FROM task_events
                    WHERE task_id = :task_id
                    ORDER BY timestamp ASC
                    LIMIT :limit
                """)

                result = await session.execute(query, {
                    "task_id": task_id,
                    "limit": limit
                })
                rows = result.fetchall()

                events = []
                for row in rows:
                    events.append({
                        "event_id": row[0],
                        "event_type": row[1],
                        "task_id": row[2],
                        "user_id": row[3],
                        "timestamp": row[4].isoformat() + "Z" if row[4] else None,
                        "payload": json.loads(row[5]) if isinstance(row[5], str) else row[5],
                        "correlation_id": row[6]
                    })

                logger.info(f"Retrieved {len(events)} event(s) for task {task_id}")
                return events

        except Exception as e:
            logger.error(f"Error retrieving task events: {e}", exc_info=True)
            return []


# Global storage instance
_audit_storage: Optional[AuditLogStorage] = None


def get_audit_storage() -> AuditLogStorage:
    """
    Get global audit storage instance.

    Returns:
        AuditLogStorage: Global storage instance
    """
    global _audit_storage
    if _audit_storage is None:
        _audit_storage = AuditLogStorage()
    return _audit_storage

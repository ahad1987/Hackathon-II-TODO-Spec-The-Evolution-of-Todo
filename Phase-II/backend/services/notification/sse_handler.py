"""
SSE Handler Module for Phase V (T049, T053, T054)

Server-Sent Events (SSE) connection manager for real-time notifications.

Features:
- Manages SSE connections per user_id
- Rate limiting (max 10 notifications/second per connection)
- Heartbeat mechanism (every 30 seconds)
- Automatic stale connection cleanup
- Max 3 concurrent connections per user

Constitutional Compliance:
- Thread-safe operations
- Graceful connection handling
- Memory-efficient design
"""

import asyncio
import logging
import time
from typing import Dict, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class SSEConnection:
    """
    Represents an SSE connection.

    Attributes:
        user_id: User ID owning this connection
        queue: Async queue for sending messages
        connected_at: Connection timestamp
        last_heartbeat: Last heartbeat timestamp
        message_count: Number of messages sent
        rate_limiter: Deque for rate limiting (timestamps of last 10 messages)
    """
    user_id: str
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue())
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    rate_limiter: deque = field(default_factory=lambda: deque(maxlen=10))

    def can_send_message(self) -> bool:
        """
        Check if message can be sent (rate limiting - T053).

        Rate limit: Max 10 notifications/second per connection.

        Returns:
            bool: True if message can be sent, False if rate limited
        """
        now = time.time()

        # Remove timestamps older than 1 second
        while self.rate_limiter and (now - self.rate_limiter[0]) > 1.0:
            self.rate_limiter.popleft()

        # Check if we've hit the rate limit (10 messages in last second)
        if len(self.rate_limiter) >= 10:
            logger.warning(f"Rate limit exceeded for user {self.user_id}")
            return False

        return True

    def record_message(self):
        """Record that a message was sent (for rate limiting)."""
        self.rate_limiter.append(time.time())
        self.message_count += 1

    def update_heartbeat(self):
        """Update last heartbeat timestamp (T054)."""
        self.last_heartbeat = datetime.utcnow()

    def is_stale(self, timeout_seconds: int = 90) -> bool:
        """
        Check if connection is stale (T054).

        Connection is stale if no heartbeat in last 90 seconds (3x heartbeat interval).

        Args:
            timeout_seconds: Timeout in seconds (default 90)

        Returns:
            bool: True if connection is stale
        """
        elapsed = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return elapsed > timeout_seconds


class NotificationManager:
    """
    Manages SSE connections and notifications (T049).

    Features:
    - Per-user connection management
    - Rate limiting (10 messages/second per connection)
    - Max 3 concurrent connections per user
    - Heartbeat every 30 seconds
    - Automatic stale connection cleanup
    """

    def __init__(self):
        """Initialize notification manager."""
        self._connections: Dict[str, Set[SSEConnection]] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def register_connection(self, user_id: str) -> SSEConnection:
        """
        Register a new SSE connection (T049).

        Rate limit: Max 3 concurrent connections per user (T053).

        Args:
            user_id: User ID for this connection

        Returns:
            SSEConnection: New connection object

        Raises:
            ValueError: If user already has 3 connections
        """
        async with self._lock:
            # Initialize user connection set if not exists
            if user_id not in self._connections:
                self._connections[user_id] = set()

            # Check connection limit (max 3 per user)
            if len(self._connections[user_id]) >= 3:
                raise ValueError(f"User {user_id} already has 3 active connections")

            # Create new connection
            connection = SSEConnection(user_id=user_id)
            self._connections[user_id].add(connection)

            logger.info(f"Registered SSE connection for user {user_id} (total: {len(self._connections[user_id])})")
            return connection

    async def unregister_connection(self, connection: SSEConnection):
        """
        Unregister an SSE connection (T049).

        Args:
            connection: Connection to unregister
        """
        async with self._lock:
            user_id = connection.user_id

            if user_id in self._connections:
                self._connections[user_id].discard(connection)

                # Clean up empty user entries
                if not self._connections[user_id]:
                    del self._connections[user_id]

                logger.info(f"Unregistered SSE connection for user {user_id}")

    async def send_notification(self, user_id: str, notification: dict) -> int:
        """
        Send notification to all connections for a user (T049).

        Args:
            user_id: User ID to send notification to
            notification: Notification data dictionary

        Returns:
            int: Number of connections notified

        Rate limiting applied per connection (max 10 messages/second).
        """
        async with self._lock:
            if user_id not in self._connections:
                logger.debug(f"No active connections for user {user_id}")
                return 0

            connections = self._connections[user_id].copy()

        # Send to all user connections
        sent_count = 0
        for connection in connections:
            try:
                # Check rate limit
                if not connection.can_send_message():
                    logger.warning(f"Rate limit exceeded for user {user_id}, skipping notification")
                    continue

                # Queue notification
                await connection.queue.put(notification)
                connection.record_message()
                sent_count += 1

            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}", exc_info=True)

        if sent_count > 0:
            logger.info(f"Sent notification to {sent_count} connection(s) for user {user_id}")

        return sent_count

    async def send_heartbeat(self, connection: SSEConnection) -> bool:
        """
        Send heartbeat to a connection (T054).

        Args:
            connection: Connection to send heartbeat to

        Returns:
            bool: True if heartbeat sent successfully
        """
        try:
            heartbeat = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            await connection.queue.put(heartbeat)
            connection.update_heartbeat()
            return True

        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}", exc_info=True)
            return False

    async def heartbeat_loop(self):
        """
        Background task to send heartbeats every 30 seconds (T054).

        Constitutional Guarantee:
        - Non-blocking
        - Continues on errors
        - Graceful shutdown
        """
        logger.info("Heartbeat loop started")

        while True:
            try:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds

                async with self._lock:
                    all_connections = []
                    for connections in self._connections.values():
                        all_connections.extend(connections)

                # Send heartbeats to all connections
                for connection in all_connections:
                    await self.send_heartbeat(connection)

                logger.debug(f"Sent heartbeats to {len(all_connections)} connection(s)")

            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}", exc_info=True)

        logger.info("Heartbeat loop stopped")

    async def cleanup_stale_connections(self):
        """
        Background task to clean up stale connections (T054).

        Removes connections with no heartbeat in last 90 seconds.

        Constitutional Guarantee:
        - Non-blocking
        - Continues on errors
        - Graceful shutdown
        """
        logger.info("Cleanup loop started")

        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                stale_connections = []
                async with self._lock:
                    for user_id, connections in list(self._connections.items()):
                        for connection in list(connections):
                            if connection.is_stale():
                                stale_connections.append((user_id, connection))

                # Unregister stale connections
                for user_id, connection in stale_connections:
                    logger.warning(f"Removing stale connection for user {user_id}")
                    await self.unregister_connection(connection)

                if stale_connections:
                    logger.info(f"Cleaned up {len(stale_connections)} stale connection(s)")

            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

        logger.info("Cleanup loop stopped")

    async def start_background_tasks(self):
        """
        Start background tasks (heartbeat and cleanup).

        Called on service startup.
        """
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            logger.info("Started heartbeat background task")

        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self.cleanup_stale_connections())
            logger.info("Started cleanup background task")

    async def stop_background_tasks(self):
        """
        Stop background tasks (heartbeat and cleanup).

        Called on service shutdown.
        """
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            await self._heartbeat_task
            self._heartbeat_task = None
            logger.info("Stopped heartbeat background task")

        if self._cleanup_task:
            self._cleanup_task.cancel()
            await self._cleanup_task
            self._cleanup_task = None
            logger.info("Stopped cleanup background task")

    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """
        Get number of active connections.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            int: Number of active connections
        """
        if user_id:
            return len(self._connections.get(user_id, set()))
        else:
            return sum(len(connections) for connections in self._connections.values())


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """
    Get global notification manager instance.

    Returns:
        NotificationManager: Global manager instance
    """
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager

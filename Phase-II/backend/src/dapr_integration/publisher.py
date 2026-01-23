"""
Dapr Event Publisher for Phase V.

Constitutional Compliance:
- NO direct Kafka client usage (Principle IV)
- Events published ONLY via Dapr SDK
- Chat API is the ONLY producer of task events
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from dapr.clients import DaprClient
from dapr.clients.grpc._response import TopicEventResponse

logger = logging.getLogger(__name__)


class DaprEventPublisher:
    """
    Publishes events to Dapr Pub/Sub (Kafka backend).

    Constitutional Guarantee:
    - Zero direct Kafka client usage
    - All events routed through Dapr abstraction
    """

    def __init__(self, pubsub_name: str = "taskflow-pubsub"):
        """
        Initialize Dapr event publisher.

        Args:
            pubsub_name: Name of Dapr Pub/Sub component (configured in k8s/dapr/pubsub.yaml)
        """
        self.pubsub_name = pubsub_name
        self._client: Optional[DaprClient] = None
        logger.info(f"DaprEventPublisher initialized with pubsub: {pubsub_name}")

    def _get_client(self) -> DaprClient:
        """
        Get or create Dapr client.

        Lazy initialization to handle Dapr sidecar unavailability at startup.
        """
        if self._client is None:
            self._client = DaprClient()
            logger.debug("Dapr client created")
        return self._client

    def publish_event(
        self,
        topic: str,
        event_type: str,
        task_id: str,
        user_id: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish event to Dapr Pub/Sub.

        Args:
            topic: Kafka topic name (e.g., "taskflow.tasks.created")
            event_type: Event type (e.g., "task.created", "task.updated")
            task_id: Task identifier
            user_id: User who triggered the event
            payload: Event-specific data
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            bool: True if publish succeeded, False otherwise

        Constitutional Compliance:
            - Uses Dapr SDK (NO direct Kafka)
            - Idempotent (event_id for deduplication)
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Construct event payload matching events-schema.yaml
        event_data = {
            "event_type": event_type,
            "event_id": event_id,
            "timestamp": timestamp,
            "task_id": task_id,
            "user_id": user_id,
            **payload  # Merge event-specific payload
        }

        if correlation_id:
            event_data["correlation_id"] = correlation_id

        try:
            client = self._get_client()

            # Publish to Dapr Pub/Sub (NO direct Kafka!)
            client.publish_event(
                pubsub_name=self.pubsub_name,
                topic_name=topic,
                data=event_data,
                data_content_type="application/json"
            )

            logger.info(
                f"Event published successfully",
                extra={
                    "event_id": event_id,
                    "event_type": event_type,
                    "topic": topic,
                    "task_id": task_id,
                    "user_id": user_id
                }
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to publish event: {str(e)}",
                extra={
                    "event_type": event_type,
                    "topic": topic,
                    "task_id": task_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return False

    def publish_task_created(
        self,
        task_id: str,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        recurrence_pattern: Optional[str] = None,
        reminder_offset: Optional[str] = None
    ) -> bool:
        """
        Publish task.created event.

        Args:
            task_id: Task identifier
            user_id: User who created the task
            title: Task title
            description: Task description (optional)
            due_date: Task due date ISO8601 (optional)
            recurrence_pattern: Recurrence pattern (optional)
            reminder_offset: Reminder offset interval (optional)

        Returns:
            bool: True if publish succeeded
        """
        payload = {
            "task": {
                "id": task_id,
                "title": title,
                "description": description,
                "due_date": due_date,
                "recurrence_pattern": recurrence_pattern,
                "reminder_offset": reminder_offset
            }
        }

        return self.publish_event(
            topic="taskflow.tasks.created",
            event_type="task.created",
            task_id=task_id,
            user_id=user_id,
            payload=payload
        )

    def publish_task_updated(
        self,
        task_id: str,
        user_id: str,
        changes: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Publish task.updated event.

        Args:
            task_id: Task identifier
            user_id: User who updated the task
            changes: Dict of field changes {field_name: {"old": value, "new": value}}

        Returns:
            bool: True if publish succeeded
        """
        payload = {"changes": changes}

        return self.publish_event(
            topic="taskflow.tasks.updated",
            event_type="task.updated",
            task_id=task_id,
            user_id=user_id,
            payload=payload
        )

    def publish_task_completed(
        self,
        task_id: str,
        user_id: str,
        completed_at: str
    ) -> bool:
        """
        Publish task.completed event.

        Args:
            task_id: Task identifier
            user_id: User who completed the task
            completed_at: Completion timestamp ISO8601

        Returns:
            bool: True if publish succeeded
        """
        payload = {"completed_at": completed_at}

        return self.publish_event(
            topic="taskflow.tasks.completed",
            event_type="task.completed",
            task_id=task_id,
            user_id=user_id,
            payload=payload
        )

    def publish_task_deleted(
        self,
        task_id: str,
        user_id: str
    ) -> bool:
        """
        Publish task.deleted event.

        Args:
            task_id: Task identifier
            user_id: User who deleted the task

        Returns:
            bool: True if publish succeeded
        """
        payload = {}

        return self.publish_event(
            topic="taskflow.tasks.deleted",
            event_type="task.deleted",
            task_id=task_id,
            user_id=user_id,
            payload=payload
        )

    def close(self):
        """Close Dapr client connection."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Dapr client closed")



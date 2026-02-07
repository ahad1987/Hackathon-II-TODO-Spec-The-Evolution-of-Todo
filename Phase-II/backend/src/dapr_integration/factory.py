"""
Dapr Publisher Factory - Singleton management with graceful degradation.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global singleton instance
_publisher: Optional[object] = None


def get_publisher():
    """
    Get global Dapr publisher instance.

    Returns:
        DaprEventPublisher instance or mock if Dapr SDK unavailable
    """
    global _publisher

    if _publisher is None:
        try:
            from .publisher import DaprEventPublisher
            from src.config import get_settings
            settings = get_settings()
            _publisher = DaprEventPublisher(pubsub_name=settings.PUBSUB_NAME)
            logger.info(f"Dapr publisher initialized successfully with {settings.PUBSUB_NAME}")
        except ImportError as e:
            logger.warning(f"Dapr SDK not available: {e}")
            logger.info("Using mock publisher (events will not be published)")
            _publisher = _MockPublisher()
        except Exception as e:
            logger.error(f"Failed to initialize Dapr publisher: {e}")
            _publisher = _MockPublisher()

    return _publisher


def close_publisher():
    """Close global Dapr publisher instance."""
    global _publisher

    if _publisher is not None:
        try:
            if hasattr(_publisher, 'close'):
                _publisher.close()
            logger.info("Dapr publisher closed")
        except Exception as e:
            logger.error(f"Error closing publisher: {e}")
        finally:
            _publisher = None


class _MockPublisher:
    """Mock publisher used when Dapr SDK is unavailable."""

    def publish_event(self, *args, **kwargs):
        logger.debug("Mock publisher: event not published (Dapr unavailable)")
        return False

    def publish_task_created(self, *args, **kwargs):
        logger.debug("Mock publisher: task.created not published")
        return False

    def publish_task_updated(self, *args, **kwargs):
        logger.debug("Mock publisher: task.updated not published")
        return False

    def publish_task_completed(self, *args, **kwargs):
        logger.debug("Mock publisher: task.completed not published")
        return False

    def publish_task_deleted(self, *args, **kwargs):
        logger.debug("Mock publisher: task.deleted not published")
        return False

    def close(self):
        pass

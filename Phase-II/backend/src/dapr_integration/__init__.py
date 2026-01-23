"""
Dapr integration module for Phase V event-driven architecture.

This module provides Dapr runtime integration for:
- Event publishing (Pub/Sub)
- Health checks (sidecar connectivity)
- Service invocation (future)
"""

try:
    from .publisher import DaprEventPublisher
except ImportError:
    DaprEventPublisher = None

from .health import check_dapr_connectivity
from .factory import get_publisher, close_publisher

__all__ = [
    "DaprEventPublisher",
    "check_dapr_connectivity",
    "get_publisher",
    "close_publisher"
]

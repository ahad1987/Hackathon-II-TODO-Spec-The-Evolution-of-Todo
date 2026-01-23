"""
Dapr integration module for Phase V event-driven architecture.

This module provides Dapr runtime integration for:
- Event publishing (Pub/Sub)
- Health checks (sidecar connectivity)
- Service invocation (future)
"""

from .publisher import DaprEventPublisher
from .health import check_dapr_connectivity

__all__ = ["DaprEventPublisher", "check_dapr_connectivity"]

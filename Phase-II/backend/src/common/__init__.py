"""
Common utilities and shared modules for the Todo Backend.
Phase V: Health check endpoints for Kubernetes probes.
"""

from .health import (
    HealthCheckResponse,
    liveness_check,
    readiness_check
)

__all__ = [
    "HealthCheckResponse",
    "liveness_check",
    "readiness_check"
]

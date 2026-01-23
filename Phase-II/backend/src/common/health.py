"""
Health Check Module for Phase V.

Provides liveness and readiness probe implementations for Kubernetes.

Constitutional Compliance (Principle VIII):
- Liveness probe: Always pass (process alive)
- Readiness probe: Check database and Dapr connectivity
- Services MUST start even when dependencies unavailable
"""

import logging
from typing import Dict, Any, Tuple
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import text

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheckResponse(BaseModel):
    """
    Health check response model.

    Attributes:
        status: Overall health status (healthy, unhealthy, degraded)
        checks: Dictionary of individual component checks
        message: Optional message providing additional context
    """
    status: HealthStatus
    checks: Dict[str, Dict[str, Any]] = {}
    message: str = ""


def liveness_check() -> HealthCheckResponse:
    """
    Liveness probe implementation.

    Constitutional Guarantee (Principle VIII):
    - ALWAYS returns healthy if process is running
    - Does NOT check external dependencies
    - Used by Kubernetes to restart crashed pods

    Returns:
        HealthCheckResponse: Always returns status=healthy

    Example Response:
        {
            "status": "healthy",
            "checks": {},
            "message": "Process is alive"
        }
    """
    logger.debug("Liveness check passed (process alive)")

    return HealthCheckResponse(
        status=HealthStatus.HEALTHY,
        checks={},
        message="Process is alive"
    )


async def check_database_connectivity(timeout: float = 2.0) -> Tuple[bool, str]:
    """
    Check database connectivity.

    Args:
        timeout: Query timeout in seconds (default 2.0)

    Returns:
        Tuple[bool, str]: (is_healthy, message)
            - (True, "Database healthy") if connection successful
            - (False, error_message) if connection failed
    """
    try:
        # Import engine here to avoid circular dependency
        from src.database import engine

        # Execute simple query to verify connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()

        logger.debug("Database connectivity check passed")
        return True, "Database healthy"

    except Exception as e:
        error_msg = f"Database unhealthy: {str(e)}"
        logger.warning(error_msg)
        return False, error_msg


async def readiness_check() -> HealthCheckResponse:
    """
    Readiness probe implementation.

    Constitutional Guarantee (Principle VIII):
    - Checks database connectivity (required dependency)
    - Checks Dapr connectivity (if DAPR_ENABLED=true)
    - Service is NOT READY until dependencies are healthy
    - Used by Kubernetes to route traffic

    Returns:
        HealthCheckResponse: Status based on dependency health
            - status=healthy: All dependencies healthy
            - status=degraded: Some dependencies unhealthy but service can start
            - status=unhealthy: Critical dependencies unhealthy

    Example Response (all healthy):
        {
            "status": "healthy",
            "checks": {
                "database": {"status": "healthy", "message": "Database healthy"},
                "dapr": {"status": "healthy", "message": "Dapr healthy"}
            },
            "message": "All dependencies healthy"
        }

    Example Response (degraded - Dapr unavailable):
        {
            "status": "degraded",
            "checks": {
                "database": {"status": "healthy", "message": "Database healthy"},
                "dapr": {"status": "unhealthy", "message": "Dapr sidecar not available"}
            },
            "message": "Running in degraded mode: Dapr unavailable"
        }
    """
    checks = {}

    # Check database connectivity (CRITICAL dependency)
    db_healthy, db_message = await check_database_connectivity()
    checks["database"] = {
        "status": HealthStatus.HEALTHY if db_healthy else HealthStatus.UNHEALTHY,
        "message": db_message
    }

    # Check Dapr connectivity (OPTIONAL dependency if DAPR_ENABLED=true)
    if settings.DAPR_ENABLED:
        try:
            from src.dapr.health import check_dapr_connectivity
            dapr_healthy, dapr_message = await check_dapr_connectivity()
            checks["dapr"] = {
                "status": HealthStatus.HEALTHY if dapr_healthy else HealthStatus.UNHEALTHY,
                "message": dapr_message
            }
        except Exception as e:
            logger.warning(f"Dapr health check failed: {e}")
            checks["dapr"] = {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Dapr check failed: {str(e)}"
            }

    # Determine overall status
    # Database is CRITICAL - if unhealthy, service is unhealthy
    if not db_healthy:
        logger.warning("Readiness check failed: Database unhealthy")
        return HealthCheckResponse(
            status=HealthStatus.UNHEALTHY,
            checks=checks,
            message="Critical dependency unhealthy: Database"
        )

    # If Dapr enabled but unhealthy, service is degraded (can still function without events)
    if settings.DAPR_ENABLED and checks.get("dapr", {}).get("status") == HealthStatus.UNHEALTHY:
        logger.warning("Readiness check degraded: Dapr unhealthy")
        return HealthCheckResponse(
            status=HealthStatus.DEGRADED,
            checks=checks,
            message="Running in degraded mode: Dapr unavailable"
        )

    # All dependencies healthy
    logger.debug("Readiness check passed (all dependencies healthy)")
    return HealthCheckResponse(
        status=HealthStatus.HEALTHY,
        checks=checks,
        message="All dependencies healthy"
    )

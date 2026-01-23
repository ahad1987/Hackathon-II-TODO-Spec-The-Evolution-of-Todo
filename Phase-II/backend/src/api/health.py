"""
Health check endpoints for load balancers and Kubernetes probes.

Phase IV: Basic /health endpoint for backward compatibility
Phase V: Kubernetes liveness and readiness probes
"""

from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.common.health import (
    liveness_check,
    readiness_check,
    HealthStatus
)

settings = get_settings()
router = APIRouter(prefix="", tags=["Health"])


@router.get("/health")
async def health_check(request: Request):
    """
    Basic health check endpoint (Phase IV backward compatibility).

    Returns:
        dict: Status with version, environment, and feature flags
    """
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "chat_registered": getattr(request.app.state, "chat_registered", False),
    }


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe endpoint (Phase V).

    Constitutional Guarantee (Principle VIII):
    - ALWAYS returns 200 if process is running
    - Does NOT check external dependencies
    - Used by Kubernetes to restart crashed pods

    Returns:
        JSONResponse: Always 200 OK with status=healthy

    Example Response:
        {
            "status": "healthy",
            "checks": {},
            "message": "Process is alive"
        }
    """
    response = liveness_check()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.model_dump()
    )


@router.get("/health/ready")
async def readiness_probe():
    """
    Kubernetes readiness probe endpoint (Phase V).

    Constitutional Guarantee (Principle VIII):
    - Checks database connectivity (required)
    - Checks Dapr connectivity (if DAPR_ENABLED=true)
    - Returns 200 when all dependencies healthy
    - Returns 503 when dependencies unavailable
    - Used by Kubernetes to route traffic

    Returns:
        JSONResponse:
            - 200 OK if status=healthy (all dependencies available)
            - 503 Service Unavailable if status=unhealthy or degraded

    Example Response (healthy):
        {
            "status": "healthy",
            "checks": {
                "database": {"status": "healthy", "message": "Database healthy"},
                "dapr": {"status": "healthy", "message": "Dapr healthy"}
            },
            "message": "All dependencies healthy"
        }

    Example Response (degraded):
        {
            "status": "degraded",
            "checks": {
                "database": {"status": "healthy", "message": "Database healthy"},
                "dapr": {"status": "unhealthy", "message": "Dapr sidecar not available"}
            },
            "message": "Running in degraded mode: Dapr unavailable"
        }
    """
    response = await readiness_check()

    # Return 200 only if fully healthy
    # Return 503 for unhealthy or degraded (Kubernetes should not route traffic)
    if response.status == HealthStatus.HEALTHY:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.model_dump()
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump()
        )

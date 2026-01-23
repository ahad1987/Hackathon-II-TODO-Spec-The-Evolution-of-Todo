"""
Dapr Health Check Module for Phase V.

Constitutional Compliance:
- Services MUST start even when Dapr sidecar unavailable (Principle VIII)
- Liveness probe: Always pass (process alive)
- Readiness probe: Check Dapr connectivity
"""

import logging
from typing import Tuple

import httpx

logger = logging.getLogger(__name__)

# Dapr sidecar HTTP port (default 3500)
DAPR_HTTP_PORT = 3500
DAPR_HEALTH_ENDPOINT = f"http://localhost:{DAPR_HTTP_PORT}/v1.0/healthz"


async def check_dapr_connectivity(timeout: float = 2.0) -> Tuple[bool, str]:
    """
    Check Dapr sidecar connectivity.

    Used for readiness probe - service is ready only when Dapr is available.

    Args:
        timeout: Request timeout in seconds (default 2.0)

    Returns:
        Tuple[bool, str]: (is_healthy, message)
            - (True, "Dapr healthy") if sidecar accessible
            - (False, error_message) if sidecar unavailable

    Constitutional Guarantee:
        - Service can start WITHOUT Dapr (liveness passes)
        - Service is NOT READY without Dapr (readiness fails)
        - This enables graceful degradation
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(DAPR_HEALTH_ENDPOINT)

            if response.status_code == 204:
                # Dapr returns 204 No Content when healthy
                logger.debug("Dapr sidecar healthy")
                return True, "Dapr healthy"
            else:
                error_msg = f"Dapr unhealthy: status {response.status_code}"
                logger.warning(error_msg)
                return False, error_msg

    except httpx.ConnectError:
        error_msg = "Dapr sidecar not available (connection refused)"
        logger.warning(error_msg)
        return False, error_msg

    except httpx.TimeoutException:
        error_msg = f"Dapr sidecar timeout (>{timeout}s)"
        logger.warning(error_msg)
        return False, error_msg

    except Exception as e:
        error_msg = f"Dapr health check failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def get_dapr_status() -> dict:
    """
    Get Dapr sidecar status information.

    Returns:
        dict: Dapr status information including:
            - dapr_enabled: bool (whether Dapr is configured)
            - dapr_http_port: int (Dapr HTTP port)
            - dapr_health_endpoint: str (health check URL)
    """
    return {
        "dapr_enabled": True,  # Will be read from config in T015
        "dapr_http_port": DAPR_HTTP_PORT,
        "dapr_health_endpoint": DAPR_HEALTH_ENDPOINT
    }

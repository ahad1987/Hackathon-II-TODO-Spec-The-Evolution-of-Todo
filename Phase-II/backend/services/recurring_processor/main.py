"""
Recurring Task Processor Service - Phase V (T030)

FastAPI service that:
1. Subscribes to task.created and task.updated events via Dapr
2. Runs scheduler every 5 minutes to generate recurring task instances
3. Health endpoints for Kubernetes liveness/readiness probes

Constitutional Compliance:
- NO direct Kafka client usage (Dapr Pub/Sub only)
- Graceful degradation when Dapr unavailable
"""

import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_NAME = "recurring-processor"
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3500"))
APP_PORT = int(os.getenv("APP_PORT", "8001"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"{SERVICE_NAME} starting up...")

    # Phase V: Start background scheduler
    try:
        from .scheduler import start_scheduler, stop_scheduler
        await start_scheduler()
        logger.info("Recurring task scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start scheduler: {e}")
        logger.info("Service starting without scheduler - manual triggering required")

    yield

    # Shutdown
    logger.info(f"{SERVICE_NAME} shutting down...")

    # Phase V: Stop background scheduler
    try:
        from .scheduler import stop_scheduler
        await stop_scheduler()
        logger.info("Recurring task scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop scheduler: {e}")


# Create FastAPI app
app = FastAPI(
    title="Recurring Task Processor",
    version="1.0.0",
    description="Phase V service for generating recurring task instances",
    lifespan=lifespan,
)


# ========== Health Endpoints ==========

@app.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe.

    Always returns 200 if process is running (no dependency checks).
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": SERVICE_NAME,
            "message": "Process is alive"
        }
    )


@app.get("/health/ready")
async def readiness_probe():
    """
    Kubernetes readiness probe.

    Checks if service is ready to process events (scheduler running).
    """
    try:
        from .scheduler import is_scheduler_running
        scheduler_running = is_scheduler_running()

        if scheduler_running:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "service": SERVICE_NAME,
                    "checks": {
                        "scheduler": {"status": "healthy", "message": "Scheduler running"}
                    },
                    "message": "Service ready"
                }
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "service": SERVICE_NAME,
                    "checks": {
                        "scheduler": {"status": "unhealthy", "message": "Scheduler not running"}
                    },
                    "message": "Service not ready"
                }
            )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": SERVICE_NAME,
                "message": str(e)
            }
        )


# ========== Dapr Pub/Sub Subscription Endpoints ==========

@app.get("/dapr/subscribe")
async def dapr_subscribe():
    """
    Dapr Pub/Sub subscription configuration endpoint.

    Returns list of topics this service subscribes to.
    """
    subscriptions = [
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "taskflow.tasks.created",
            "route": "/dapr/subscribe/task-created"
        },
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "taskflow.tasks.updated",
            "route": "/dapr/subscribe/task-updated"
        }
    ]
    logger.info(f"Dapr subscribe endpoint called - returning {len(subscriptions)} subscriptions")
    return subscriptions


@app.post("/dapr/subscribe/task-created")
async def handle_task_created(request: Request):
    """
    Handle task.created events from Dapr Pub/Sub.

    If task has recurrence_pattern, track it for instance generation.
    """
    try:
        event_data = await request.json()
        logger.info(f"Received task.created event: {event_data.get('id', 'unknown')}")

        # Extract CloudEvent data
        data = event_data.get("data", {})
        task_id = data.get("task_id")
        recurrence_pattern = data.get("task", {}).get("recurrence_pattern")

        if recurrence_pattern:
            logger.info(f"Recurring task detected: {task_id} with pattern {recurrence_pattern}")
            # Scheduler will pick this up in next run
        else:
            logger.debug(f"Non-recurring task created: {task_id}")

        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.created event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/dapr/subscribe/task-updated")
async def handle_task_updated(request: Request):
    """
    Handle task.updated events from Dapr Pub/Sub.

    If recurrence_pattern changed, update tracking for instance generation.
    """
    try:
        event_data = await request.json()
        logger.info(f"Received task.updated event: {event_data.get('id', 'unknown')}")

        # Extract CloudEvent data
        data = event_data.get("data", {})
        task_id = data.get("task_id")
        changes = data.get("changes", {})

        if "recurrence_pattern" in changes:
            old_pattern = changes["recurrence_pattern"].get("old")
            new_pattern = changes["recurrence_pattern"].get("new")
            logger.info(f"Recurrence pattern changed for task {task_id}: {old_pattern} -> {new_pattern}")
            # Scheduler will pick this up in next run

        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.updated event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


# ========== Root Endpoint ==========

@app.get("/")
async def root():
    """Service info endpoint."""
    return {
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health_live": "/health/live",
            "health_ready": "/health/ready",
            "dapr_subscribe": "/dapr/subscribe"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=APP_PORT,
        log_level="info",
        reload=False
    )

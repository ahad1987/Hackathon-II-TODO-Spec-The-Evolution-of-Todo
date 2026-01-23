"""
Audit Logger Service - Phase V (T058, T063)

FastAPI service that:
1. Subscribes to all task events via Dapr Pub/Sub
2. Stores events immutably to task_events table
3. Provides audit query endpoint
4. Batch write optimization for efficiency
5. Health endpoints for Kubernetes liveness/readiness probes

Constitutional Compliance:
- NO direct Kafka client usage (Dapr Pub/Sub only)
- Immutable audit trail (ON CONFLICT DO NOTHING)
- Batch writes for efficiency
"""

import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_NAME = "audit-logger"
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3500"))
APP_PORT = int(os.getenv("APP_PORT", "8004"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"{SERVICE_NAME} starting up...")

    # Phase V: Start audit storage background task
    try:
        from storage import get_audit_storage
        storage = get_audit_storage()
        await storage.start_background_task()
        logger.info("Audit storage started (flush every 1 second)")
    except Exception as e:
        logger.warning(f"Failed to start audit storage: {e}")
        logger.info("Service starting without audit storage")

    yield

    # Shutdown
    logger.info(f"{SERVICE_NAME} shutting down...")

    # Phase V: Stop audit storage and flush remaining events
    try:
        from storage import get_audit_storage
        storage = get_audit_storage()
        await storage.stop_background_task()
        logger.info("Audit storage stopped and flushed")
    except Exception as e:
        logger.warning(f"Failed to stop audit storage: {e}")


# Create FastAPI app
app = FastAPI(
    title="Audit Logger Service",
    version="1.0.0",
    description="Phase V service for immutable audit logging",
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

    Checks if service is ready (storage initialized).
    """
    try:
        from storage import get_audit_storage

        storage = get_audit_storage()
        buffer_size = len(storage._buffer)

        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": SERVICE_NAME,
                "checks": {
                    "storage": {
                        "status": "healthy",
                        "message": f"{buffer_size} event(s) in buffer"
                    }
                },
                "message": "Service ready"
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


# ========== Audit Query Endpoint (T063) ==========

@app.get("/api/v1/audit/tasks/{task_id}")
async def get_task_audit_history(task_id: str, limit: int = 100):
    """
    Get chronological audit history for a task (T063).

    Returns all events for the specified task in chronological order.

    Args:
        task_id: Task ID to query
        limit: Maximum number of events to return (default 100)

    Returns:
        List of audit events with complete payloads

    Status codes:
    - 200: Success
    - 404: Task not found
    - 500: Server error
    """
    try:
        from storage import get_audit_storage

        storage = get_audit_storage()
        events = await storage.get_task_events(task_id, limit)

        if not events:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audit events found for task {task_id}"
            )

        return {
            "task_id": task_id,
            "event_count": len(events),
            "events": events
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit history"
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
        },
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "taskflow.tasks.completed",
            "route": "/dapr/subscribe/task-completed"
        },
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "taskflow.tasks.deleted",
            "route": "/dapr/subscribe/task-deleted"
        }
    ]
    logger.info(f"Dapr subscribe endpoint called - returning {len(subscriptions)} subscriptions")
    return subscriptions


@app.post("/dapr/subscribe/task-created")
async def handle_task_created(request: Request):
    """Handle task.created events from Dapr Pub/Sub."""
    try:
        from event_consumer import handle_task_created_event
        event_data = await request.json()
        await handle_task_created_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.created event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/dapr/subscribe/task-updated")
async def handle_task_updated(request: Request):
    """Handle task.updated events from Dapr Pub/Sub."""
    try:
        from event_consumer import handle_task_updated_event
        event_data = await request.json()
        await handle_task_updated_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.updated event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/dapr/subscribe/task-completed")
async def handle_task_completed(request: Request):
    """Handle task.completed events from Dapr Pub/Sub."""
    try:
        from event_consumer import handle_task_completed_event
        event_data = await request.json()
        await handle_task_completed_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.completed event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/dapr/subscribe/task-deleted")
async def handle_task_deleted(request: Request):
    """Handle task.deleted events from Dapr Pub/Sub."""
    try:
        from event_consumer import handle_task_deleted_event
        event_data = await request.json()
        await handle_task_deleted_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.deleted event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


# ========== Root Endpoint ==========

@app.get("/")
async def root():
    """Service info endpoint."""
    from storage import get_audit_storage

    storage = get_audit_storage()
    buffer_size = len(storage._buffer)

    return {
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "buffer_size": buffer_size,
        "endpoints": {
            "health_live": "/health/live",
            "health_ready": "/health/ready",
            "audit_query": "/api/v1/audit/tasks/{task_id}",
            "dapr_subscribe": "/dapr/subscribe"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.services.audit_logger.main:app",
        host="0.0.0.0",
        port=APP_PORT,
        log_level="info",
        reload=False
    )


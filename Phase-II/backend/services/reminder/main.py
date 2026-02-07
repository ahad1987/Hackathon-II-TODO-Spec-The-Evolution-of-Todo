"""
Reminder Service - Phase V (T038)

FastAPI service that:
1. Subscribes to task events (created, updated, deleted, completed) via Dapr
2. Maintains priority queue of scheduled reminders
3. Triggers reminders and publishes reminder.triggered events
4. Persists reminder state to database

Constitutional Compliance:
- NO direct Kafka client usage (Dapr Pub/Sub only)
- Graceful degradation when dependencies unavailable
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
SERVICE_NAME = "reminder-service"
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3500"))
APP_PORT = int(os.getenv("APP_PORT", "8002"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"{SERVICE_NAME} starting up...")

    # Phase V: Initialize priority queue and load persisted reminders
    try:
        from services.reminder.priority_queue import get_reminder_queue, load_reminders_from_db
        queue = get_reminder_queue()
        await load_reminders_from_db(queue)
        logger.info("Reminder queue initialized and loaded from database")
    except Exception as e:
        logger.warning(f"Failed to initialize reminder queue: {e}")
        logger.info("Service starting without queue - reminders will not be scheduled")

    # Phase V: Start reminder scheduler
    try:
        from services.reminder.scheduler import start_reminder_scheduler, stop_reminder_scheduler
        await start_reminder_scheduler()
        logger.info("Reminder scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start reminder scheduler: {e}")
        logger.info("Service starting without scheduler - reminders will not be triggered")

    yield

    # Shutdown
    logger.info(f"{SERVICE_NAME} shutting down...")

    # Phase V: Stop reminder scheduler
    try:
        from services.reminder.scheduler import stop_reminder_scheduler
        await stop_reminder_scheduler()
        logger.info("Reminder scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop reminder scheduler: {e}")

    # Phase V: Persist reminders to database
    try:
        from services.reminder.priority_queue import get_reminder_queue, save_reminders_to_db
        queue = get_reminder_queue()
        await save_reminders_to_db(queue)
        logger.info("Reminders persisted to database")
    except Exception as e:
        logger.warning(f"Failed to persist reminders: {e}")


# Create FastAPI app
app = FastAPI(
    title="Reminder Service",
    version="1.0.0",
    description="Phase V service for scheduling and triggering task reminders",
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

    Checks if service is ready (queue initialized, scheduler running).
    """
    try:
        from services.reminder.priority_queue import get_reminder_queue
        from services.reminder.scheduler import is_scheduler_running

        queue = get_reminder_queue()
        scheduler_running = is_scheduler_running()

        checks = {
            "queue": {
                "status": "healthy" if queue is not None else "unhealthy",
                "message": f"Queue initialized with {len(queue._queue) if queue else 0} reminders"
            },
            "scheduler": {
                "status": "healthy" if scheduler_running else "unhealthy",
                "message": "Scheduler running" if scheduler_running else "Scheduler not running"
            }
        }

        all_healthy = all(check["status"] == "healthy" for check in checks.values())

        return JSONResponse(
            status_code=200 if all_healthy else 503,
            content={
                "status": "healthy" if all_healthy else "unhealthy",
                "service": SERVICE_NAME,
                "checks": checks,
                "message": "Service ready" if all_healthy else "Service not ready"
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
        },
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "taskflow.tasks.deleted",
            "route": "/dapr/subscribe/task-deleted"
        },
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "taskflow.tasks.completed",
            "route": "/dapr/subscribe/task-completed"
        }
    ]
    logger.info(f"Dapr subscribe endpoint called - returning {len(subscriptions)} subscriptions")
    return subscriptions


@app.post("/dapr/subscribe/task-created")
async def handle_task_created(request: Request):
    """
    Handle task.created events from Dapr Pub/Sub (T040, T041).

    If task has reminder_offset, schedule reminder.
    """
    try:
        from services.reminder.event_consumer import handle_task_created_event
        event_data = await request.json()
        await handle_task_created_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.created event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/dapr/subscribe/task-updated")
async def handle_task_updated(request: Request):
    """
    Handle task.updated events from Dapr Pub/Sub (T040, T041).

    If reminder_offset changed, reschedule reminder.
    """
    try:
        from services.reminder.event_consumer import handle_task_updated_event
        event_data = await request.json()
        await handle_task_updated_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.updated event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/dapr/subscribe/task-deleted")
async def handle_task_deleted(request: Request):
    """
    Handle task.deleted events from Dapr Pub/Sub (T040, T041).

    Cancel reminder if exists.
    """
    try:
        from services.reminder.event_consumer import handle_task_deleted_event
        event_data = await request.json()
        await handle_task_deleted_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.deleted event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/dapr/subscribe/task-completed")
async def handle_task_completed(request: Request):
    """
    Handle task.completed events from Dapr Pub/Sub (T040, T041).

    Cancel reminder if exists.
    """
    try:
        from services.reminder.event_consumer import handle_task_completed_event
        event_data = await request.json()
        await handle_task_completed_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.completed event: {e}", exc_info=True)
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
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=APP_PORT,
        log_level="info",
        reload=False
    )


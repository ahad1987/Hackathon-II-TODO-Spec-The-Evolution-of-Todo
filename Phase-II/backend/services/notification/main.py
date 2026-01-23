"""
Notification Service - Phase V (T048, T052)

FastAPI service that:
1. Manages SSE connections for real-time notifications
2. Subscribes to all task events + reminder.triggered via Dapr
3. Sends notifications to connected users within 2 seconds
4. Health endpoints for Kubernetes liveness/readiness probes

Constitutional Compliance:
- NO direct Kafka client usage (Dapr Pub/Sub only)
- Graceful degradation when dependencies unavailable
- Rate limiting and connection limits enforced
"""

import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_NAME = "notification-service"
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3500"))
APP_PORT = int(os.getenv("APP_PORT", "8003"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"{SERVICE_NAME} starting up...")

    # Phase V: Start notification manager background tasks
    try:
        from services.notification.sse_handler import get_notification_manager
        manager = get_notification_manager()
        await manager.start_background_tasks()
        logger.info("Notification manager started (heartbeat + cleanup tasks)")
    except Exception as e:
        logger.warning(f"Failed to start notification manager: {e}")
        logger.info("Service starting without notification manager")

    yield

    # Shutdown
    logger.info(f"{SERVICE_NAME} shutting down...")

    # Phase V: Stop notification manager background tasks
    try:
        from services.notification.sse_handler import get_notification_manager
        manager = get_notification_manager()
        await manager.stop_background_tasks()
        logger.info("Notification manager stopped")
    except Exception as e:
        logger.warning(f"Failed to stop notification manager: {e}")


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    version="1.0.0",
    description="Phase V service for real-time SSE notifications",
    lifespan=lifespan,
)


# ========== Authentication (Simplified) ==========

async def get_current_user_id(request: Request) -> str:
    """
    Extract user_id from JWT token (simplified for Phase V).

    In production, this would validate JWT token from Authorization header.
    For now, we'll accept user_id from query parameter for testing.

    Args:
        request: FastAPI request

    Returns:
        str: User ID

    Raises:
        HTTPException: If authentication fails
    """
    # Try to get user_id from query parameter (for testing)
    user_id = request.query_params.get("user_id")

    if user_id:
        return user_id

    # In production: Extract from Authorization header and validate JWT
    # auth_header = request.headers.get("Authorization")
    # if not auth_header or not auth_header.startswith("Bearer "):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Missing or invalid Authorization header"
    #     )
    # token = auth_header.split(" ")[1]
    # # Validate token and extract user_id
    # user_id = validate_jwt_token(token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (provide user_id query parameter)"
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

    Checks if service is ready (notification manager running).
    """
    try:
        from services.notification.sse_handler import get_notification_manager

        manager = get_notification_manager()
        connection_count = manager.get_connection_count()

        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": SERVICE_NAME,
                "checks": {
                    "notification_manager": {
                        "status": "healthy",
                        "message": f"{connection_count} active connection(s)"
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


# ========== SSE Endpoint (T052) ==========

@app.get("/api/v1/notifications/stream")
async def notification_stream(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """
    Server-Sent Events (SSE) endpoint for real-time notifications (T052).

    Constitutional Guarantee:
    - Max 3 concurrent connections per user (T053)
    - Rate limiting: 10 notifications/second per connection (T053)
    - Heartbeat every 30 seconds (T054)
    - Automatic stale connection cleanup (T054)

    Usage:
        # JavaScript EventSource
        const eventSource = new EventSource('/api/v1/notifications/stream?user_id=123');
        eventSource.onmessage = (event) => {
            const notification = JSON.parse(event.data);
            console.log('Notification:', notification);
        };

        # curl
        curl -N http://localhost:8003/api/v1/notifications/stream?user_id=123

    Args:
        request: FastAPI request
        user_id: Authenticated user ID (from JWT or query param)

    Returns:
        EventSourceResponse: SSE stream

    Raises:
        HTTPException: If max connections exceeded (429)
    """
    try:
        from services.notification.sse_handler import get_notification_manager

        manager = get_notification_manager()

        # Register connection (enforces max 3 connections per user)
        try:
            connection = await manager.register_connection(user_id)
            logger.info(f"New SSE connection for user {user_id}")
        except ValueError as e:
            # Max connections exceeded
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e)
            )

        async def event_generator():
            """
            Generate SSE events from connection queue.

            Yields:
                dict: SSE event data
            """
            try:
                while True:
                    # Check if client disconnected
                    if await request.is_disconnected():
                        logger.info(f"Client disconnected for user {user_id}")
                        break

                    # Wait for notification (with timeout to check disconnection)
                    try:
                        notification = await asyncio.wait_for(
                            connection.queue.get(),
                            timeout=1.0
                        )

                        # Send notification as SSE event
                        yield notification

                    except asyncio.TimeoutError:
                        # No notification, continue (allows checking disconnection)
                        continue

            except asyncio.CancelledError:
                logger.info(f"Event generator cancelled for user {user_id}")
            except Exception as e:
                logger.error(f"Error in event generator for user {user_id}: {e}", exc_info=True)
            finally:
                # Unregister connection
                await manager.unregister_connection(connection)
                logger.info(f"Unregistered SSE connection for user {user_id}")

        # Return SSE stream
        return EventSourceResponse(event_generator())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SSE stream: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification stream"
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
        },
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "taskflow.tasks.reminder-triggered",
            "route": "/dapr/subscribe/reminder-triggered"
        }
    ]
    logger.info(f"Dapr subscribe endpoint called - returning {len(subscriptions)} subscriptions")
    return subscriptions


@app.post("/dapr/subscribe/task-created")
async def handle_task_created(request: Request):
    """Handle task.created events from Dapr Pub/Sub."""
    try:
        from services.notification.event_consumer import handle_task_created_event
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
        from services.notification.event_consumer import handle_task_updated_event
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
        from services.notification.event_consumer import handle_task_completed_event
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
        from services.notification.event_consumer import handle_task_deleted_event
        event_data = await request.json()
        await handle_task_deleted_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling task.deleted event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/dapr/subscribe/reminder-triggered")
async def handle_reminder_triggered(request: Request):
    """Handle reminder.triggered events from Dapr Pub/Sub."""
    try:
        from services.notification.event_consumer import handle_reminder_triggered_event
        event_data = await request.json()
        await handle_reminder_triggered_event(event_data)
        return JSONResponse(status_code=200, content={"success": True})

    except Exception as e:
        logger.error(f"Error handling reminder.triggered event: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


# ========== Root Endpoint ==========

@app.get("/")
async def root():
    """Service info endpoint."""
    from services.notification.sse_handler import get_notification_manager

    manager = get_notification_manager()
    connection_count = manager.get_connection_count()

    return {
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "active_connections": connection_count,
        "endpoints": {
            "health_live": "/health/live",
            "health_ready": "/health/ready",
            "sse_stream": "/api/v1/notifications/stream",
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

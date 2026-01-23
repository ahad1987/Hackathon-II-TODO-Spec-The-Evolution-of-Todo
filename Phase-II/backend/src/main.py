"""
FastAPI application entry point for the Todo Backend.
Initializes the app with middleware, routes, and configuration.
"""

# Fix Windows event loop issue for psycopg async
import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.config import get_settings
from src.database import init_db
from src.middleware.auth import AuthenticationMiddleware
from src.dapr_integration import get_publisher, close_publisher  # Phase V

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed (continuing with degraded mode): {e}")
        logger.info("Server starting without database - API will be available but database operations will fail")

    # Phase V: Initialize Dapr publisher (graceful degradation if Dapr unavailable)
    if settings.DAPR_ENABLED:
        try:
            publisher = get_publisher()
            logger.info(f"Dapr publisher initialized (pubsub: {settings.PUBSUB_NAME})")
        except Exception as e:
            logger.warning(f"Dapr publisher initialization failed: {e}")
            logger.info("Server starting without Dapr - Phase V event publishing will be unavailable")

    yield

    # Shutdown
    logger.info("Application shutting down...")

    # Phase V: Close Dapr publisher
    if settings.DAPR_ENABLED:
        try:
            close_publisher()
            logger.info("Dapr publisher closed")
        except Exception as e:
            logger.warning(f"Dapr publisher cleanup failed: {e}")


# Create FastAPI app instance
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Phase II Todo Full-Stack Web Application - Backend API",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Add authentication middleware (will be applied to specific routes)
# Note: Middleware is applied in reverse order of addition
app.add_middleware(AuthenticationMiddleware)

# Add trusted host middleware
# Allow all hosts in development (TrustedHostMiddleware is restrictive, can cause issues)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Add CORS middleware - MUST be added last to be executed first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Phase V: /health endpoint moved to src.api.health router for better organization
# Includes /health, /health/live (liveness probe), /health/ready (readiness probe)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    Returns a safe error response without exposing internal details.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint providing API information."""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "api_docs": "/docs",
            "redoc": "/redoc",
            "auth": "/api/v1/auth",
            "tasks": "/api/v1/tasks",
        },
    }


# Import and include API routes
from src.api import auth, tasks, health

app.include_router(health.router, prefix="", tags=["Health"])  # Phase V: Kubernetes probes
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])

# Import chat router with error handling
try:
    from src.chatbot.api.routes.chat import router as chat_router
    app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
    app.state.chat_registered = True
    logger.info("Chat router registered at /api/v1/chat")
except Exception as e:
    app.state.chat_registered = False
    logger.error(f"Failed to import chat router: {e}", exc_info=True)


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )

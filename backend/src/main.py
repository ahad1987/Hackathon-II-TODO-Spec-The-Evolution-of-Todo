"""FastAPI application entry point."""

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database init failed: {e}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Todo API with AI Chatbot",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

app.add_middleware(AuthenticationMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.API_VERSION}


@app.get("/")
async def root():
    return {"name": settings.API_TITLE, "version": settings.API_VERSION, "status": "running",
            "endpoints": {"health": "/health", "docs": "/docs", "auth": "/api/v1/auth", "tasks": "/api/v1/tasks", "chat": "/api/chat"}}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


from src.api import auth, tasks
from src.chatbot.api.routes import chat

app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])

logger.info("Routers registered: auth, tasks, chat (/api/chat)")


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

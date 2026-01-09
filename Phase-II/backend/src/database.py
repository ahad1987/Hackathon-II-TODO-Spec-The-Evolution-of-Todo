"""
Database module for SQLModel and PostgreSQL connection.
Provides session management and database initialization.
"""

from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, create_engine, Session, select
import asyncio

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database URL for async operations
# For PostgreSQL, we need to use psycopg3 with async support
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")

# Create async engine with NullPool for Neon serverless
# NullPool creates new connections each time but avoids connection lifecycle issues
# Neon's serverless model works better with this approach
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,  # NullPool for serverless, no connection reuse
    connect_args={
        "connect_timeout": 10,  # Connection timeout for psycopg v3
    },
)

# Create async session factory
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session for FastAPI endpoints.
    Usage:
        async def my_endpoint(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.
    Called on application startup.
    Continues gracefully if database is unavailable.
    """
    try:
        logger.info("Creating database tables...")

        # Import models to register them with SQLModel
        from src.models.user import User  # noqa: F401
        from src.models.task import Task  # noqa: F401

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Database unavailable - running in read-only mode: {e}")


async def drop_db() -> None:
    """
    Drop all tables from the database.
    WARNING: This is destructive and should only be used in development/testing.
    """
    try:
        logger.warning("Dropping all database tables...")

        from src.models.user import User  # noqa: F401
        from src.models.task import Task  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


async def close_db() -> None:
    """Close database connections. Called on application shutdown."""
    await engine.dispose()


# Synchronous session for non-async operations (if needed)
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)


def get_sync_session() -> Session:
    """Get synchronous database session."""
    return Session(sync_engine)


def init_sync_db() -> None:
    """Initialize database synchronously."""
    try:
        logger.info("Creating database tables (sync)...")

        from src.models.user import User  # noqa: F401
        from src.models.task import Task  # noqa: F401

        SQLModel.metadata.create_all(sync_engine)
        logger.info("Database tables created successfully (sync)")
    except Exception as e:
        logger.error(f"Failed to initialize database (sync): {e}")
        raise

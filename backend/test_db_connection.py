#!/usr/bin/env python
"""
Database connection verification script.
Tests Neon PostgreSQL connection and logs table existence.
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file before importing config
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"Warning: .env file not found at {env_path}")

from sqlalchemy import text, inspect
from src.config import get_settings
from src.database import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection and log results."""

    settings = get_settings()

    logger.info("=" * 80)
    logger.info("DATABASE CONNECTION VERIFICATION")
    logger.info("=" * 80)

    # Log configuration
    logger.info(f"DATABASE_URL loaded: {settings.DATABASE_URL[:50]}...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    logger.info("\n" + "=" * 80)
    logger.info("TESTING NEON CONNECTION")
    logger.info("=" * 80)

    try:
        # Test async connection
        async with engine.begin() as conn:
            logger.info("✅ Successfully connected to Neon PostgreSQL")

            # Get database info
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            logger.info(f"✅ Database version: {version[:80]}...")

            # Get current database
            result = await conn.execute(text("SELECT current_database();"))
            db_name = result.scalar()
            logger.info(f"✅ Current database: {db_name}")

            # Get current user
            result = await conn.execute(text("SELECT current_user;"))
            user = result.scalar()
            logger.info(f"✅ Connected as user: {user}")

            logger.info("\n" + "=" * 80)
            logger.info("CHECKING TABLES")
            logger.info("=" * 80)

            # Get list of tables
            result = await conn.execute(
                text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
            )

            tables = result.fetchall()

            if tables:
                logger.info(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    table_name = table[0]
                    logger.info(f"   - {table_name}")

                    # Get column info for each table
                    col_result = await conn.execute(
                        text(f"""
                            SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns
                            WHERE table_name = '{table_name}'
                            ORDER BY ordinal_position;
                        """)
                    )

                    columns = col_result.fetchall()
                    for col in columns:
                        col_name, col_type, nullable = col
                        null_str = "nullable" if nullable == 'YES' else "not null"
                        logger.info(f"     └─ {col_name}: {col_type} ({null_str})")
            else:
                logger.warning("⚠️  No tables found in public schema")
                logger.info("Tables need to be created via init_db()")

            logger.info("\n" + "=" * 80)
            logger.info("CONNECTION TEST SUCCESSFUL")
            logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Failed to connect to Neon: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

    return True


if __name__ == "__main__":
    # Handle Windows ProactorEventLoop issue
    import sys
    if sys.platform == 'win32':
        import selectors
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    success = asyncio.run(test_database_connection())
    exit(0 if success else 1)

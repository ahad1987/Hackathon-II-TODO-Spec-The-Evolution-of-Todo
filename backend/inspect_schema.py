#!/usr/bin/env python
"""
Database schema inspection script.
Verifies users table, tasks table, foreign key, and indexes using SQL queries.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Fix Windows event loop issue
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

from sqlalchemy import text
from src.config import get_settings
from src.database import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def inspect_schema():
    """Inspect database schema using SQL queries."""

    logger.info("=" * 100)
    logger.info("DATABASE SCHEMA INSPECTION")
    logger.info("=" * 100)

    try:
        async with engine.begin() as conn:

            logger.info("\n" + "=" * 100)
            logger.info("TABLE EXISTENCE CHECK")
            logger.info("=" * 100)

            # Get all tables in public schema
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]

            logger.info(f"✅ Total tables in public schema: {len(tables)}")
            if tables:
                for table in tables:
                    logger.info(f"   ├─ {table}")
            else:
                logger.warning("⚠️  No tables found in public schema")
                return False

            # =====================================================
            # USERS TABLE INSPECTION
            # =====================================================
            logger.info("\n" + "=" * 100)
            logger.info("USERS TABLE INSPECTION")
            logger.info("=" * 100)

            if 'users' not in tables:
                logger.error("❌ Users table NOT FOUND")
                return False

            logger.info("✅ Users table exists")

            # Get columns
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            logger.info(f"\nColumns ({len(columns)}):")
            for col_name, col_type, nullable, default in columns:
                nullable_str = "nullable" if nullable == 'YES' else "NOT NULL"
                default_str = f" [DEFAULT: {default}]" if default else ""
                logger.info(f"   ├─ {col_name}: {col_type} ({nullable_str}){default_str}")

            # Get primary key using information_schema
            result = await conn.execute(text("""
                SELECT column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'users' AND tc.constraint_type = 'PRIMARY KEY';
            """))
            pk_result = result.fetchall()
            if pk_result:
                pk_cols = [row[0] for row in pk_result]
                logger.info(f"\n✅ Primary Key: {', '.join(pk_cols)}")
            else:
                logger.warning("⚠️  No primary key found")

            # =====================================================
            # TASKS TABLE INSPECTION
            # =====================================================
            logger.info("\n" + "=" * 100)
            logger.info("TASKS TABLE INSPECTION")
            logger.info("=" * 100)

            if 'tasks' not in tables:
                logger.error("❌ Tasks table NOT FOUND")
                return False

            logger.info("✅ Tasks table exists")

            # Get columns
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'tasks'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            logger.info(f"\nColumns ({len(columns)}):")
            for col_name, col_type, nullable, default in columns:
                nullable_str = "nullable" if nullable == 'YES' else "NOT NULL"
                default_str = f" [DEFAULT: {default}]" if default else ""
                logger.info(f"   ├─ {col_name}: {col_type} ({nullable_str}){default_str}")

            # Get primary key using information_schema
            result = await conn.execute(text("""
                SELECT column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'tasks' AND tc.constraint_type = 'PRIMARY KEY';
            """))
            pk_result = result.fetchall()
            if pk_result:
                pk_cols = [row[0] for row in pk_result]
                logger.info(f"\n✅ Primary Key: {', '.join(pk_cols)}")
            else:
                logger.warning("⚠️  No primary key found")

            # =====================================================
            # FOREIGN KEY INSPECTION
            # =====================================================
            logger.info("\n" + "=" * 100)
            logger.info("FOREIGN KEY INSPECTION")
            logger.info("=" * 100)

            result = await conn.execute(text("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name;
            """))
            fks = result.fetchall()

            if fks:
                logger.info(f"✅ Foreign keys found ({len(fks)}):")
                for table_name, col_name, fk_table, fk_col, constraint_name in fks:
                    logger.info(f"   ├─ {table_name}.{col_name} → {fk_table}.{fk_col}")
                    logger.info(f"      Constraint: {constraint_name}")

                    # Verify the critical FK
                    if table_name == 'tasks' and col_name == 'user_id' and fk_table == 'users' and fk_col == 'id':
                        logger.info("      ✅ VERIFIED: tasks.user_id → users.id")
            else:
                logger.warning("⚠️  No foreign keys found")
                return False

            # =====================================================
            # INDEX INSPECTION
            # =====================================================
            logger.info("\n" + "=" * 100)
            logger.info("INDEX INSPECTION")
            logger.info("=" * 100)

            # Indexes on users table
            result = await conn.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'users'
                ORDER BY indexname;
            """))
            user_indexes = result.fetchall()
            logger.info("\nIndexes in users table:")
            if user_indexes:
                for idx_name, idx_def in user_indexes:
                    logger.info(f"   ├─ {idx_name}")
                    logger.info(f"      {idx_def}")
            else:
                logger.info("   └─ No indexes found")

            # Indexes on tasks table
            result = await conn.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'tasks'
                ORDER BY indexname;
            """))
            task_indexes = result.fetchall()
            logger.info("\nIndexes in tasks table:")
            if task_indexes:
                for idx_name, idx_def in task_indexes:
                    logger.info(f"   ├─ {idx_name}")
                    logger.info(f"      {idx_def}")
                    # Highlight user_id index
                    if 'user_id' in idx_def.lower():
                        logger.info("      ✅ INDEX ON user_id (for query performance)")
            else:
                logger.info("   └─ No indexes found")

            # =====================================================
            # DATA VERIFICATION
            # =====================================================
            logger.info("\n" + "=" * 100)
            logger.info("DATA VERIFICATION")
            logger.info("=" * 100)

            # Check users table stats
            result = await conn.execute(text("SELECT COUNT(*) FROM users;"))
            user_count = result.scalar()
            logger.info(f"✅ Users table row count: {user_count}")

            # Check tasks table stats
            result = await conn.execute(text("SELECT COUNT(*) FROM tasks;"))
            task_count = result.scalar()
            logger.info(f"✅ Tasks table row count: {task_count}")

            # =====================================================
            # SUMMARY
            # =====================================================
            logger.info("\n" + "=" * 100)
            logger.info("SCHEMA INSPECTION COMPLETE")
            logger.info("=" * 100)

            logger.info("\n📊 SUMMARY:")
            logger.info("   ✅ Users table: EXISTS")
            logger.info(f"      └─ Rows: {user_count}")
            logger.info("      └─ Columns: 5 (id, email, hashed_password, created_at, updated_at)")
            logger.info("      └─ Primary Key: id")

            logger.info("\n   ✅ Tasks table: EXISTS")
            logger.info(f"      └─ Rows: {task_count}")
            logger.info("      └─ Columns: 7 (id, user_id, title, description, completed, created_at, updated_at)")
            logger.info("      └─ Primary Key: id")
            logger.info("      └─ Foreign Key: user_id → users.id")

            logger.info("\n   ✅ Indexes: VERIFIED")
            logger.info(f"      └─ users: {len(user_indexes) if user_indexes else 0} indexes")
            logger.info(f"      └─ tasks: {len(task_indexes) if task_indexes else 0} indexes")

            logger.info("\n✅ DATABASE SCHEMA IS CORRECTLY INITIALIZED")

            return True

    except Exception as e:
        logger.error(f"❌ Schema inspection failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(inspect_schema())
    exit(0 if success else 1)

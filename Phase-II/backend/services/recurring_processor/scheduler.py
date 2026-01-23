"""
Recurring Task Scheduler for Phase V (T031)

Background scheduler using APScheduler that:
1. Runs every 5 minutes
2. Finds recurring tasks due for new instances
3. Generates task instances via task_generator module

Constitutional Compliance:
- Runs as background task (non-blocking)
- Graceful shutdown handling
- Error recovery (continues on failures)
"""

import logging
from datetime import datetime
import asyncio
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None
_scheduler_running = False


async def process_recurring_tasks():
    """
    Process recurring tasks and generate instances.

    This function is called by the scheduler every 5 minutes.
    It delegates to the task_generator module.
    """
    try:
        logger.info("Scheduler triggered - processing recurring tasks...")

        from .task_generator import generate_due_task_instances

        # Generate task instances for all recurring tasks
        instances_created = await generate_due_task_instances()

        logger.info(f"Scheduler completed - created {instances_created} task instances")

    except Exception as e:
        logger.error(f"Error processing recurring tasks: {e}", exc_info=True)
        # Don't re-raise - scheduler should continue running


async def start_scheduler():
    """
    Start the APScheduler background scheduler.

    Constitutional Guarantee:
    - Non-blocking (runs in background)
    - Graceful error handling
    - Idempotent (safe to call multiple times)
    """
    global _scheduler, _scheduler_running

    if _scheduler_running:
        logger.warning("Scheduler already running - skipping start")
        return

    try:
        logger.info("Starting recurring task scheduler...")

        # Create AsyncIOScheduler
        _scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,  # Combine missed runs into one
                "max_instances": 1,  # Only one instance running at a time
                "misfire_grace_time": 300  # 5 minutes grace period for missed runs
            }
        )

        # Schedule recurring task processing every 5 minutes
        _scheduler.add_job(
            func=process_recurring_tasks,
            trigger=IntervalTrigger(minutes=5),
            id="process_recurring_tasks",
            name="Process Recurring Tasks",
            replace_existing=True
        )

        # Start the scheduler
        _scheduler.start()
        _scheduler_running = True

        logger.info("Recurring task scheduler started successfully")
        logger.info("Scheduler will run every 5 minutes to generate task instances")

        # Run immediately on startup (don't wait 5 minutes)
        asyncio.create_task(process_recurring_tasks())

    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
        _scheduler_running = False
        raise


async def stop_scheduler():
    """
    Stop the APScheduler background scheduler.

    Constitutional Guarantee:
    - Graceful shutdown (waits for current jobs to complete)
    - Idempotent (safe to call multiple times)
    """
    global _scheduler, _scheduler_running

    if not _scheduler_running:
        logger.info("Scheduler not running - skipping stop")
        return

    try:
        logger.info("Stopping recurring task scheduler...")

        if _scheduler:
            _scheduler.shutdown(wait=True)  # Wait for running jobs to complete
            _scheduler = None

        _scheduler_running = False
        logger.info("Recurring task scheduler stopped successfully")

    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}", exc_info=True)
        _scheduler_running = False


def is_scheduler_running() -> bool:
    """
    Check if scheduler is currently running.

    Returns:
        bool: True if scheduler is running, False otherwise
    """
    return _scheduler_running


def get_scheduler_info() -> dict:
    """
    Get scheduler status and configuration.

    Returns:
        dict: Scheduler information including status, jobs, next run times
    """
    if not _scheduler_running or not _scheduler:
        return {
            "status": "stopped",
            "jobs": [],
            "next_run": None
        }

    try:
        jobs = _scheduler.get_jobs()
        job_info = []

        for job in jobs:
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return {
            "status": "running",
            "jobs": job_info,
            "next_run": job_info[0]["next_run_time"] if job_info else None
        }

    except Exception as e:
        logger.error(f"Error getting scheduler info: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }

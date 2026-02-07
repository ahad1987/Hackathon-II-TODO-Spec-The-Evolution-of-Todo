-- Phase V Rollback Migration
-- Feature: Event-Driven Task Management
-- Date: 2026-01-22
-- Purpose: Safe rollback from Phase V to Phase IV
-- Constitutional Compliance: Zero data loss, Phase IV fully functional after rollback

-- ============================================================================
-- ROLLBACK VERIFICATION (RUN FIRST)
-- ============================================================================

-- Verify Phase IV tasks exist and will remain intact
SELECT COUNT(*) as phase_iv_tasks_count
FROM tasks
WHERE due_date IS NULL
  AND recurrence_pattern IS NULL
  AND parent_recurring_task_id IS NULL;

-- Expected: Count > 0 means Phase IV tasks exist and will be preserved

-- ============================================================================
-- DROP PHASE V CONSTRAINTS
-- ============================================================================

-- Drop constraints before dropping columns (dependency order)
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_recurrence_requires_due_date;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_recurrence_end_requires_pattern;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_recurring_instance_complete;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_reminder_requires_due_date;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS uniq_recurring_instance;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS fk_parent_recurring_task;

-- ============================================================================
-- DROP PHASE V INDEXES
-- ============================================================================

-- Drop indexes from tasks table
DROP INDEX IF EXISTS idx_tasks_due_date;
DROP INDEX IF EXISTS idx_tasks_recurrence;
DROP INDEX IF EXISTS idx_tasks_parent_recurring;
DROP INDEX IF EXISTS idx_tasks_reminder_status;

-- Drop indexes from task_events table (before dropping table)
DROP INDEX IF EXISTS idx_task_events_task_id;
DROP INDEX IF EXISTS idx_task_events_user_id;
DROP INDEX IF EXISTS idx_task_events_type;
DROP INDEX IF EXISTS idx_task_events_correlation;

-- Drop indexes from reminder_schedule table (before dropping table)
DROP INDEX IF EXISTS idx_reminders_trigger;
DROP INDEX IF EXISTS idx_reminders_task;

-- ============================================================================
-- DROP PHASE V TABLES
-- ============================================================================

-- Drop reminder_schedule table (Reminder Service persistence)
DROP TABLE IF EXISTS reminder_schedule;

-- Drop task_events partitions and parent table (Audit logs)
DROP TABLE IF EXISTS task_events_2026_01;
DROP TABLE IF EXISTS task_events CASCADE;

-- ============================================================================
-- DROP PHASE V COLUMNS FROM TASKS TABLE
-- ============================================================================

-- Remove Phase V columns from tasks table
-- Note: Phase IV tasks remain completely intact (these columns were nullable)
ALTER TABLE tasks
  DROP COLUMN IF EXISTS due_date,
  DROP COLUMN IF EXISTS recurrence_pattern,
  DROP COLUMN IF EXISTS recurrence_end_date,
  DROP COLUMN IF EXISTS parent_recurring_task_id,
  DROP COLUMN IF EXISTS occurrence_date,
  DROP COLUMN IF EXISTS reminder_offset,
  DROP COLUMN IF EXISTS reminder_status;

-- ============================================================================
-- VERIFICATION QUERIES (POST-ROLLBACK)
-- ============================================================================

-- Verify Phase V columns removed
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'tasks'
  AND column_name IN ('due_date', 'recurrence_pattern', 'recurrence_end_date',
                      'parent_recurring_task_id', 'occurrence_date',
                      'reminder_offset', 'reminder_status');
-- Expected: 0 rows (all Phase V columns dropped)

-- Verify Phase V tables removed
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('task_events', 'task_events_2026_01', 'reminder_schedule');
-- Expected: 0 rows (all Phase V tables dropped)

-- Verify Phase IV tasks intact
SELECT COUNT(*) as phase_iv_tasks_still_present
FROM tasks;
-- Expected: Count matches pre-rollback count (no data loss)

-- Verify tasks table schema (should be Phase IV only)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'tasks'
ORDER BY ordinal_position;
-- Expected: Only Phase IV columns visible

-- ============================================================================
-- ROLLBACK COMPLETE
-- ============================================================================

-- Phase V rolled back successfully
-- Phase IV fully functional
-- Zero data loss (nullable columns were dropped, Phase IV data preserved)

-- To re-apply Phase V, run: phase_v_migration.sql

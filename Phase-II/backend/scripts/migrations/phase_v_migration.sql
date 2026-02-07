-- Phase V Database Migration
-- Feature: Event-Driven Task Management
-- Date: 2026-01-22
-- Constitutional Compliance: Additive-only, all Phase V columns NULLABLE

-- ============================================================================
-- PHASE V SCHEMA EXTENSIONS
-- ============================================================================

-- Add Phase V columns to existing tasks table (ALL NULLABLE for backward compatibility)
ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS due_date TIMESTAMP,
  ADD COLUMN IF NOT EXISTS recurrence_pattern TEXT,
  ADD COLUMN IF NOT EXISTS recurrence_end_date TIMESTAMP,
  ADD COLUMN IF NOT EXISTS parent_recurring_task_id UUID,
  ADD COLUMN IF NOT EXISTS occurrence_date DATE,
  ADD COLUMN IF NOT EXISTS reminder_offset INTERVAL,
  ADD COLUMN IF NOT EXISTS reminder_status TEXT;

-- Add Phase V indexes for query performance
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks (user_id, due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_recurrence ON tasks (recurrence_pattern, occurrence_date) WHERE recurrence_pattern IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_parent_recurring ON tasks (parent_recurring_task_id) WHERE parent_recurring_task_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_reminder_status ON tasks (reminder_status, due_date) WHERE reminder_status = 'pending';

-- Add Phase V constraints (ensure data integrity)
ALTER TABLE tasks ADD CONSTRAINT IF NOT EXISTS chk_recurrence_requires_due_date
  CHECK (recurrence_pattern IS NULL OR due_date IS NOT NULL);

ALTER TABLE tasks ADD CONSTRAINT IF NOT EXISTS chk_recurrence_end_requires_pattern
  CHECK (recurrence_end_date IS NULL OR recurrence_pattern IS NOT NULL);

ALTER TABLE tasks ADD CONSTRAINT IF NOT EXISTS chk_recurring_instance_complete
  CHECK ((parent_recurring_task_id IS NULL AND occurrence_date IS NULL) OR
         (parent_recurring_task_id IS NOT NULL AND occurrence_date IS NOT NULL));

ALTER TABLE tasks ADD CONSTRAINT IF NOT EXISTS chk_reminder_requires_due_date
  CHECK (reminder_offset IS NULL OR due_date IS NOT NULL);

ALTER TABLE tasks ADD CONSTRAINT IF NOT EXISTS uniq_recurring_instance
  UNIQUE (parent_recurring_task_id, occurrence_date);

-- Add foreign key for self-referencing recurring tasks
ALTER TABLE tasks ADD CONSTRAINT IF NOT EXISTS fk_parent_recurring_task
  FOREIGN KEY (parent_recurring_task_id) REFERENCES tasks(id) ON DELETE CASCADE;

-- ============================================================================
-- CREATE NEW TABLES FOR PHASE V
-- ============================================================================

-- Create task_events table (partitioned by month for efficient retention policies)
CREATE TABLE IF NOT EXISTS task_events (
  event_id UUID PRIMARY KEY,
  event_type TEXT NOT NULL,
  task_id UUID NOT NULL,
  user_id UUID NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  payload JSONB NOT NULL,
  correlation_id UUID,
  partition_key DATE NOT NULL
) PARTITION BY RANGE (partition_key);

-- Create initial partition for current month
CREATE TABLE IF NOT EXISTS task_events_2026_01 PARTITION OF task_events
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Create indexes on task_events for query performance
CREATE INDEX IF NOT EXISTS idx_task_events_task_id ON task_events (task_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_task_events_user_id ON task_events (user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_task_events_type ON task_events (event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_task_events_correlation ON task_events (correlation_id) WHERE correlation_id IS NOT NULL;

-- Create reminder_schedule table (for Reminder Service persistence)
CREATE TABLE IF NOT EXISTS reminder_schedule (
  reminder_id UUID PRIMARY KEY,
  task_id UUID NOT NULL,
  user_id UUID NOT NULL,
  trigger_at TIMESTAMP NOT NULL,
  reminder_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes on reminder_schedule for efficient reminder processing
CREATE INDEX IF NOT EXISTS idx_reminders_trigger ON reminder_schedule (status, trigger_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_reminders_task ON reminder_schedule (task_id);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify Phase V columns added to tasks table
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'tasks'
  AND column_name IN ('due_date', 'recurrence_pattern', 'recurrence_end_date',
                      'parent_recurring_task_id', 'occurrence_date',
                      'reminder_offset', 'reminder_status')
ORDER BY column_name;

-- Verify Phase V tables created
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('task_events', 'task_events_2026_01', 'reminder_schedule')
ORDER BY table_name;

-- Verify Phase V indexes created
SELECT indexname
FROM pg_indexes
WHERE indexname LIKE 'idx_tasks_%' OR indexname LIKE 'idx_task_events_%' OR indexname LIKE 'idx_reminders_%'
ORDER BY indexname;

-- Count existing Phase IV tasks (should be unchanged)
SELECT COUNT(*) as phase_iv_tasks_count
FROM tasks
WHERE due_date IS NULL
  AND recurrence_pattern IS NULL
  AND parent_recurring_task_id IS NULL;

-- Migration complete - Phase IV data intact, Phase V schema ready

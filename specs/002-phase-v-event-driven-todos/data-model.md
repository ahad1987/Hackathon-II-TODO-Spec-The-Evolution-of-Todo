# Data Model: Phase V - Event-Driven Task Management

**Feature**: Phase V - Event-Driven Task Management
**Branch**: `002-phase-v-event-driven-todos`
**Date**: 2026-01-22

## Overview

This document defines the data entities for Phase V, following constitutional principles:
- **Additive-only**: All Phase V fields are nullable to maintain Phase IV compatibility
- **No breaking changes**: Existing Phase IV tasks remain valid without migration
- **Backward compatible**: Phase IV code ignores new columns; Phase V provides defaults

---

## Entity 1: Task (Extended from Phase IV)

**Purpose**: Represents a user's task, extended with Phase V fields for recurrence, due dates, and reminders.

**Phase IV Fields** (UNCHANGED):
- `id` (UUID, PK): Unique task identifier
- `user_id` (UUID, FK): Owner of the task
- `title` (TEXT, NOT NULL): Task title
- `description` (TEXT, NULLABLE): Task description
- `status` (ENUM, NOT NULL): Task status (pending, completed, deleted)
- `created_at` (TIMESTAMP, NOT NULL): Creation timestamp
- `updated_at` (TIMESTAMP, NOT NULL): Last update timestamp

**Phase V Fields** (NEW, ALL NULLABLE):
- `due_date` (TIMESTAMP, NULLABLE): When task is due (UTC)
- `recurrence_pattern` (TEXT, NULLABLE): Recurrence pattern (daily, weekly, monthly, custom)
- `recurrence_end_date` (TIMESTAMP, NULLABLE): When recurrence stops (optional)
- `parent_recurring_task_id` (UUID, FK, NULLABLE): Reference to parent recurring definition
- `occurrence_date` (DATE, NULLABLE): Specific occurrence date for recurring task instances
- `reminder_offset` (INTERVAL, NULLABLE): Time before due_date to trigger reminder (e.g., '1 day', '1 hour')
- `reminder_status` (ENUM, NULLABLE): Reminder state (pending, sent, acknowledged, cancelled)

**Relationships**:
- `user_id` → `users.id` (existing Phase IV relationship)
- `parent_recurring_task_id` → `tasks.id` (self-referencing for recurring instances)

**Validation Rules**:
- If `recurrence_pattern` is NOT NULL, then `due_date` MUST NOT be NULL
- If `recurrence_end_date` is NOT NULL, then `recurrence_pattern` MUST NOT be NULL
- If `parent_recurring_task_id` is NOT NULL, then `occurrence_date` MUST NOT be NULL
- `reminder_offset` can only be NOT NULL if `due_date` is NOT NULL

**State Transitions**:
```
Phase IV (unchanged):
pending → completed
pending → deleted

Phase V (new):
pending (with due_date) → reminder_status: pending
reminder_status: pending → reminder_status: sent (when reminder triggered)
reminder_status: sent → reminder_status: acknowledged (when user views task)
reminder_status: pending/sent → reminder_status: cancelled (when task completed or deleted)
```

**Indexes** (Phase V additions):
- `idx_tasks_due_date` on (user_id, due_date) WHERE due_date IS NOT NULL
- `idx_tasks_recurrence` on (recurrence_pattern, occurrence_date) WHERE recurrence_pattern IS NOT NULL
- `idx_tasks_parent_recurring` on (parent_recurring_task_id) WHERE parent_recurring_task_id IS NOT NULL
- `idx_tasks_reminder_status` on (reminder_status, due_date) WHERE reminder_status = 'pending'

**Database Constraints**:
```sql
-- Recurrence pattern requires due date
ALTER TABLE tasks ADD CONSTRAINT chk_recurrence_requires_due_date
  CHECK (recurrence_pattern IS NULL OR due_date IS NOT NULL);

-- Recurrence end date requires recurrence pattern
ALTER TABLE tasks ADD CONSTRAINT chk_recurrence_end_requires_pattern
  CHECK (recurrence_end_date IS NULL OR recurrence_pattern IS NOT NULL);

-- Recurring instance requires parent and occurrence date
ALTER TABLE tasks ADD CONSTRAINT chk_recurring_instance_complete
  CHECK ((parent_recurring_task_id IS NULL AND occurrence_date IS NULL) OR
         (parent_recurring_task_id IS NOT NULL AND occurrence_date IS NOT NULL));

-- Reminder offset requires due date
ALTER TABLE tasks ADD CONSTRAINT chk_reminder_requires_due_date
  CHECK (reminder_offset IS NULL OR due_date IS NOT NULL);

-- Unique constraint for recurring instances
ALTER TABLE tasks ADD CONSTRAINT uniq_recurring_instance
  UNIQUE (parent_recurring_task_id, occurrence_date);
```

---

## Entity 2: Task Event (NEW)

**Purpose**: Immutable record of task-related events published to Dapr Pub/Sub and persisted for audit trail.

**Fields**:
- `event_id` (UUID, PK): Unique event identifier
- `event_type` (ENUM, NOT NULL): Event type (task.created, task.updated, task.completed, task.deleted, task.reminder.triggered)
- `task_id` (UUID, NOT NULL): Task this event relates to
- `user_id` (UUID, NOT NULL): User who triggered the event (or system for reminders)
- `timestamp` (TIMESTAMP, NOT NULL): When event occurred (UTC)
- `payload` (JSONB, NOT NULL): Event-specific data
- `correlation_id` (UUID, NULLABLE): For distributed tracing
- `partition_key` (DATE, NOT NULL): Partitioning key (extracted from timestamp)

**Relationships**:
- `task_id` → `tasks.id` (may be soft reference; task could be deleted)
- `user_id` → `users.id` (existing Phase IV relationship)

**Validation Rules**:
- `event_id` MUST be unique (UUID v4)
- `event_type` MUST be one of the defined enum values
- `payload` MUST contain valid JSON matching event type schema
- `partition_key` MUST equal DATE(timestamp)

**Partitioning Strategy**:
```sql
-- Monthly partitions for efficient pruning
CREATE TABLE task_events (
  event_id UUID PRIMARY KEY,
  event_type TEXT NOT NULL,
  task_id UUID NOT NULL,
  user_id UUID NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  payload JSONB NOT NULL,
  correlation_id UUID,
  partition_key DATE NOT NULL
) PARTITION BY RANGE (partition_key);

-- Create partitions (automated via pg_partman or similar)
CREATE TABLE task_events_2026_01 PARTITION OF task_events
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
-- ... (additional monthly partitions created automatically)
```

**Indexes**:
- `idx_task_events_task_id` on (task_id, timestamp DESC)
- `idx_task_events_user_id` on (user_id, timestamp DESC)
- `idx_task_events_type` on (event_type, timestamp DESC)
- `idx_task_events_correlation` on (correlation_id) WHERE correlation_id IS NOT NULL

**Event Payload Schemas** (JSONB content):

**task.created**:
```json
{
  "task": {
    "id": "uuid",
    "title": "string",
    "description": "string (nullable)",
    "due_date": "ISO8601 (nullable)",
    "recurrence_pattern": "string (nullable)",
    "reminder_offset": "interval (nullable)"
  }
}
```

**task.updated**:
```json
{
  "task_id": "uuid",
  "changes": {
    "field_name": {"old": "value", "new": "value"},
    ...
  }
}
```

**task.completed**:
```json
{
  "task_id": "uuid",
  "completed_at": "ISO8601"
}
```

**task.deleted**:
```json
{
  "task_id": "uuid",
  "deleted_at": "ISO8601"
}
```

**task.reminder.triggered**:
```json
{
  "task_id": "uuid",
  "user_id": "uuid",
  "reminder_type": "due_date_reminder",
  "due_date": "ISO8601",
  "offset_triggered": "interval"
}
```

---

## Entity 3: Reminder Schedule (NEW, In-Memory with Persistence)

**Purpose**: Internal state for Reminder Service to track upcoming reminders. Primarily in-memory (priority queue), with periodic snapshots to durable storage.

**Fields** (for snapshot persistence):
- `reminder_id` (UUID, PK): Unique reminder identifier
- `task_id` (UUID, NOT NULL): Task this reminder is for
- `user_id` (UUID, NOT NULL): User to notify
- `trigger_at` (TIMESTAMP, NOT NULL): When to trigger reminder (UTC)
- `reminder_type` (TEXT, NOT NULL): Type of reminder (due_date_reminder)
- `status` (ENUM, NOT NULL): Reminder status (pending, triggered, cancelled)
- `created_at` (TIMESTAMP, NOT NULL): When reminder was scheduled
- `updated_at` (TIMESTAMP, NOT NULL): Last status update

**Relationships**:
- `task_id` → `tasks.id` (may be soft reference if task deleted)
- `user_id` → `users.id`

**Validation Rules**:
- `trigger_at` MUST be in the future when status is 'pending'
- `status` can only transition: pending → triggered OR pending → cancelled
- Once status is 'triggered' or 'cancelled', no further updates allowed

**Indexes**:
- `idx_reminders_trigger` on (status, trigger_at) WHERE status = 'pending'
- `idx_reminders_task` on (task_id)

**Snapshot Strategy**:
- Every 5 minutes, Reminder Service writes all pending reminders to this table
- On service startup, load all pending reminders from snapshot and rebuild priority queue
- After triggering reminder, update status to 'triggered' (for audit trail)

---

## Entity 4: Notification Subscription (NEW, In-Memory)

**Purpose**: Track active SSE connections for each user. Ephemeral (not persisted).

**Fields** (in-memory only):
- `connection_id` (UUID): Unique connection identifier
- `user_id` (UUID): User this connection belongs to
- `connected_at` (TIMESTAMP): When connection established
- `last_heartbeat` (TIMESTAMP): Last heartbeat sent
- `client_ip` (TEXT): Client IP address (for rate limiting)

**Lifecycle**:
- Created when user opens SSE connection
- Deleted when connection closes or heartbeat timeout (60 seconds)
- No database persistence (rebuilt on service restart)

**Rate Limiting**:
- Max 10 notifications per second per connection_id
- Max 3 concurrent connections per user_id

---

## Recurrence Pattern Format

**Format**: `{frequency}:{options}`

**Examples**:
- `daily:` (every day)
- `weekly:MON,WED,FRI` (every Monday, Wednesday, Friday)
- `monthly:15` (15th of each month)
- `custom:3d` (every 3 days)

**Parsing Logic** (application-level, not database):
```
frequency = daily | weekly | monthly | custom
options = comma-separated values specific to frequency
```

**Validation** (application-level):
- `daily` has no options
- `weekly` options: MON, TUE, WED, THU, FRI, SAT, SUN (comma-separated)
- `monthly` options: 1-31 (day of month)
- `custom` options: Nd (every N days)

---

## Migration Strategy (Additive-Only)

**Phase V Migration** (backward-compatible):

```sql
-- Add Phase V columns to existing tasks table
ALTER TABLE tasks
  ADD COLUMN due_date TIMESTAMP,
  ADD COLUMN recurrence_pattern TEXT,
  ADD COLUMN recurrence_end_date TIMESTAMP,
  ADD COLUMN parent_recurring_task_id UUID,
  ADD COLUMN occurrence_date DATE,
  ADD COLUMN reminder_offset INTERVAL,
  ADD COLUMN reminder_status TEXT;

-- Add indexes for Phase V queries
CREATE INDEX idx_tasks_due_date ON tasks (user_id, due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_tasks_recurrence ON tasks (recurrence_pattern, occurrence_date) WHERE recurrence_pattern IS NOT NULL;
CREATE INDEX idx_tasks_parent_recurring ON tasks (parent_recurring_task_id) WHERE parent_recurring_task_id IS NOT NULL;
CREATE INDEX idx_tasks_reminder_status ON tasks (reminder_status, due_date) WHERE reminder_status = 'pending';

-- Add constraints
ALTER TABLE tasks ADD CONSTRAINT chk_recurrence_requires_due_date
  CHECK (recurrence_pattern IS NULL OR due_date IS NOT NULL);
ALTER TABLE tasks ADD CONSTRAINT chk_recurrence_end_requires_pattern
  CHECK (recurrence_end_date IS NULL OR recurrence_pattern IS NOT NULL);
ALTER TABLE tasks ADD CONSTRAINT chk_recurring_instance_complete
  CHECK ((parent_recurring_task_id IS NULL AND occurrence_date IS NULL) OR
         (parent_recurring_task_id IS NOT NULL AND occurrence_date IS NOT NULL));
ALTER TABLE tasks ADD CONSTRAINT chk_reminder_requires_due_date
  CHECK (reminder_offset IS NULL OR due_date IS NOT NULL);
ALTER TABLE tasks ADD CONSTRAINT uniq_recurring_instance
  UNIQUE (parent_recurring_task_id, occurrence_date);

-- Add foreign key for self-referencing recurring tasks
ALTER TABLE tasks ADD CONSTRAINT fk_parent_recurring_task
  FOREIGN KEY (parent_recurring_task_id) REFERENCES tasks(id) ON DELETE CASCADE;

-- Create new task_events table (partitioned)
CREATE TABLE task_events (
  event_id UUID PRIMARY KEY,
  event_type TEXT NOT NULL,
  task_id UUID NOT NULL,
  user_id UUID NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  payload JSONB NOT NULL,
  correlation_id UUID,
  partition_key DATE NOT NULL
) PARTITION BY RANGE (partition_key);

-- Create initial partition
CREATE TABLE task_events_2026_01 PARTITION OF task_events
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Create indexes on task_events
CREATE INDEX idx_task_events_task_id ON task_events (task_id, timestamp DESC);
CREATE INDEX idx_task_events_user_id ON task_events (user_id, timestamp DESC);
CREATE INDEX idx_task_events_type ON task_events (event_type, timestamp DESC);
CREATE INDEX idx_task_events_correlation ON task_events (correlation_id) WHERE correlation_id IS NOT NULL;

-- Create reminder_schedule table
CREATE TABLE reminder_schedule (
  reminder_id UUID PRIMARY KEY,
  task_id UUID NOT NULL,
  user_id UUID NOT NULL,
  trigger_at TIMESTAMP NOT NULL,
  reminder_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes on reminder_schedule
CREATE INDEX idx_reminders_trigger ON reminder_schedule (status, trigger_at) WHERE status = 'pending';
CREATE INDEX idx_reminders_task ON reminder_schedule (task_id);
```

**Rollback Migration** (remove Phase V columns):

```sql
-- Drop Phase V constraints
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_recurrence_requires_due_date;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_recurrence_end_requires_pattern;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_recurring_instance_complete;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_reminder_requires_due_date;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS uniq_recurring_instance;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS fk_parent_recurring_task;

-- Drop Phase V indexes
DROP INDEX IF EXISTS idx_tasks_due_date;
DROP INDEX IF EXISTS idx_tasks_recurrence;
DROP INDEX IF EXISTS idx_tasks_parent_recurring;
DROP INDEX IF EXISTS idx_tasks_reminder_status;

-- Drop Phase V columns
ALTER TABLE tasks
  DROP COLUMN IF EXISTS due_date,
  DROP COLUMN IF EXISTS recurrence_pattern,
  DROP COLUMN IF EXISTS recurrence_end_date,
  DROP COLUMN IF EXISTS parent_recurring_task_id,
  DROP COLUMN IF EXISTS occurrence_date,
  DROP COLUMN IF EXISTS reminder_offset,
  DROP COLUMN IF EXISTS reminder_status;

-- Drop Phase V tables
DROP TABLE IF EXISTS task_events CASCADE;
DROP TABLE IF EXISTS reminder_schedule;

-- Phase IV data remains intact (nullable columns ignored)
```

---

## Data Integrity & Consistency

### Idempotency Guarantees
- **Recurring task instances**: `uniq_recurring_instance` constraint prevents duplicates
- **Event publishing**: `event_id` (UUID) ensures each event published once
- **Reminder scheduling**: `reminder_id` unique per task/trigger time combination

### Cascade Behavior
- **Task deleted** → `parent_recurring_task_id` FK with CASCADE deletes all instances
- **User deleted** (Phase IV) → tasks cascade delete (existing behavior preserved)

### Orphaned Data Prevention
- Reminder Service cleans up cancelled reminders (status='cancelled') older than 7 days
- Audit logs use soft references (task_id may not exist; acceptable for audit trail)

---

## Query Patterns (for Implementation Reference)

### Get Pending Reminders (Reminder Service)
```sql
SELECT reminder_id, task_id, user_id, trigger_at
FROM reminder_schedule
WHERE status = 'pending' AND trigger_at <= NOW()
ORDER BY trigger_at
LIMIT 100;
```

### Get Recurring Tasks Due for Processing (Recurring Task Processor)
```sql
SELECT id, user_id, recurrence_pattern, due_date, recurrence_end_date
FROM tasks
WHERE recurrence_pattern IS NOT NULL
  AND status = 'pending'
  AND (recurrence_end_date IS NULL OR recurrence_end_date > NOW())
  AND NOT EXISTS (
    SELECT 1 FROM tasks child
    WHERE child.parent_recurring_task_id = tasks.id
      AND child.occurrence_date = CURRENT_DATE
  );
```

### Get Audit Trail for Task (Audit Logger Query API)
```sql
SELECT event_id, event_type, timestamp, payload
FROM task_events
WHERE task_id = $1
ORDER BY timestamp DESC;
```

### Get User's Due Today Tasks (Chat API)
```sql
SELECT id, title, due_date, reminder_status
FROM tasks
WHERE user_id = $1
  AND status = 'pending'
  AND due_date::DATE = CURRENT_DATE
ORDER BY due_date;
```

---

## Summary

**Phase IV Compatibility**: ✅ All Phase V fields nullable; no migration required for existing tasks
**Rollback Safety**: ✅ Phase V columns can be dropped without affecting Phase IV data
**Performance**: ✅ Indexes optimized for Phase V queries; partitioning for audit logs
**Data Integrity**: ✅ Constraints prevent invalid states; idempotency keys prevent duplicates
**Constitutional Compliance**: ✅ Additive-only changes; no modifications to existing schema

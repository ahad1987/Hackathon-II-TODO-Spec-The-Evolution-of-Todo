# Feature Specification: Phase V - Event-Driven Task Management

**Feature Branch**: `002-phase-v-event-driven-todos`
**Created**: 2026-01-22
**Status**: Draft
**Input**: User description: "Create the Phase V Specification under Speckit Plus governance with advanced Todo features, event-driven communication, Dapr runtime integration, Kafka-backed pub/sub, and Kubernetes-native deployment"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recurring Task Automation (Priority: P1)

Users need to create tasks that repeat on a schedule (daily, weekly, monthly) without manually recreating them each time. A recurring task should automatically generate new task instances based on the recurrence pattern.

**Why this priority**: Recurring tasks are the most requested feature and provide immediate productivity value. This is the core functionality that distinguishes Phase V from Phase IV.

**Independent Test**: Can be fully tested by creating a recurring task with a daily pattern, verifying the task instance is created, and confirming that a new instance appears the next day. Delivers standalone value without requiring other Phase V features.

**Acceptance Scenarios**:

1. **Given** a user has an active account, **When** they create a task with recurrence pattern "daily" and start date "2026-01-22", **Then** the system creates the first task instance for 2026-01-22
2. **Given** a recurring task exists with pattern "weekly on Monday", **When** the system processes recurring tasks, **Then** a new task instance is created for the next Monday
3. **Given** a recurring task has 3 completed instances, **When** the user views their task list, **Then** they see only active and upcoming instances, not completed ones
4. **Given** a user edits a recurring task pattern from "daily" to "weekly", **When** the change is saved, **Then** future instances follow the new pattern and existing instances remain unchanged

---

### User Story 2 - Due Date Reminders (Priority: P1)

Users need to receive timely reminders before task due dates to help them stay on track. Reminders should be configurable (e.g., 1 day before, 1 hour before) and delivered through a notification mechanism.

**Why this priority**: Due date awareness is critical for task management effectiveness. Without reminders, users miss deadlines. This is equally important as recurring tasks for MVP value.

**Independent Test**: Can be tested by creating a task with a due date and reminder set to "1 hour before", advancing system time, and verifying the reminder is triggered and notification is sent.

**Acceptance Scenarios**:

1. **Given** a task has due date "2026-01-23 14:00" with reminder "1 day before", **When** system time reaches "2026-01-22 14:00", **Then** a reminder notification is generated and sent to the user
2. **Given** a user has multiple tasks with due dates today, **When** they view their dashboard, **Then** they see all due-today tasks highlighted with urgency indicators
3. **Given** a task reminder was sent, **When** the user acknowledges or completes the task, **Then** no further reminders are sent for that task
4. **Given** a task's due date is changed, **When** the update is saved, **Then** reminder schedules are recalculated based on the new due date

---

### User Story 3 - Real-Time Notifications (Priority: P2)

Users need to receive real-time notifications about task events (created, completed, assigned, due soon) through a notification service. Notifications should be delivered in-app and potentially via external channels.

**Why this priority**: Real-time updates enhance collaboration and awareness, but users can manage tasks effectively without them. This is a quality-of-life improvement that builds on P1 functionality.

**Independent Test**: Can be tested by triggering a task event (e.g., task completion) and verifying that connected clients receive a notification within 2 seconds.

**Acceptance Scenarios**:

1. **Given** a user has an active browser session, **When** a new task is created via the Chat API, **Then** the user receives a real-time notification within 2 seconds
2. **Given** a task is marked complete, **When** the completion event is published, **Then** all subscribed clients receive a task update notification
3. **Given** a user's notification preferences set to "critical only", **When** non-critical notifications are triggered, **Then** those notifications are not delivered to that user
4. **Given** the notification service is temporarily unavailable, **When** it recovers, **Then** missed notifications are delivered in chronological order

---

### User Story 4 - Comprehensive Audit Logging (Priority: P3)

System administrators and power users need complete audit trails of all task operations (create, update, delete, complete) for compliance, debugging, and analytics purposes.

**Why this priority**: Audit logging is important for enterprise deployments but not required for core task management functionality. This can be added after core features are stable.

**Independent Test**: Can be tested by performing task operations and verifying that each operation creates a timestamped audit log entry with actor, action, and changes recorded.

**Acceptance Scenarios**:

1. **Given** a user creates a task, **When** the creation succeeds, **Then** an audit log entry is recorded with timestamp, user ID, action "task.created", and task details
2. **Given** a task is updated, **When** the update is saved, **Then** the audit log captures the before/after state of changed fields
3. **Given** an administrator queries audit logs for a specific task, **When** they filter by task ID, **Then** they see a complete chronological history of all operations on that task
4. **Given** audit logs accumulate over time, **When** retention policies are applied, **Then** logs older than the retention period are archived but not deleted

---

### Edge Cases

- What happens when a recurring task's next instance date falls on a day the user account is inactive or deleted?
- How does the system handle due date reminders for tasks scheduled in different timezones?
- What occurs if a notification service is down when a critical reminder should fire?
- How does the system prevent duplicate task instances when recurring task processing runs concurrently?
- What happens when a user modifies a single instance of a recurring task (should it "break" from the series)?
- How are reminders handled when a task's due date is in the past at creation time?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support recurring task patterns including daily, weekly, monthly, and custom intervals
- **FR-002**: System MUST automatically generate task instances based on recurring task definitions
- **FR-003**: System MUST allow users to configure due date reminders with customizable time offsets (e.g., 1 day before, 1 hour before)
- **FR-004**: System MUST trigger reminder notifications at the configured time before task due dates
- **FR-005**: System MUST deliver real-time notifications to connected clients for task events (created, updated, completed, deleted)
- **FR-006**: System MUST log all task operations (create, read, update, delete, complete) with timestamp, actor, and action details
- **FR-007**: System MUST persist audit logs in a queryable format for compliance and debugging
- **FR-008**: All new data fields (recurrence_pattern, due_date, reminder_config, etc.) MUST be optional to maintain backward compatibility with Phase IV tasks
- **FR-009**: Existing Phase IV tasks MUST continue to function identically without requiring migration or updates
- **FR-010**: System MUST expose health and readiness endpoints for Kubernetes liveness/readiness probes
- **FR-011**: System MUST publish task events (task.created, task.updated, task.completed, task.deleted, task.reminder.triggered) to Dapr Pub/Sub
- **FR-012**: Chat API MUST remain the ONLY producer of task events; no other services may publish task events directly
- **FR-013**: Notification service MUST subscribe to task events via Dapr Pub/Sub and deliver notifications to connected clients
- **FR-014**: Reminder service MUST subscribe to task events and schedule reminder notifications based on due dates

### Key Entities

- **Recurring Task Definition**: Represents the template for a recurring task series; includes recurrence pattern (daily/weekly/monthly/custom), start date, end date (optional), and task template (title, description, etc.)
- **Task Instance**: A specific occurrence of a recurring task or a standalone task; includes due date, reminder configuration, completion status, and reference to parent recurring definition (if applicable)
- **Task Event**: An immutable record of a task-related action; includes event type (created/updated/completed/deleted/reminder.triggered), timestamp, actor (user ID), task ID, and event payload
- **Reminder Configuration**: Defines when reminders should fire for a task; includes offset from due date (e.g., "1 day before", "1 hour before"), reminder type (notification/email), and status (pending/sent/acknowledged)
- **Audit Log Entry**: A permanent record of a system operation; includes timestamp, actor, action, resource ID, before/after state (for updates), and correlation ID for distributed tracing

### Event Definitions *(mandatory for Phase V)*

#### Event: task.created

**Producer**: Chat API (ONLY)
**Consumers**: Notification Service, Reminder Service, Audit Logger
**Payload**:
```json
{
  "event_type": "task.created",
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "actor_id": "user_id",
  "task": {
    "id": "task_id",
    "title": "string",
    "description": "string",
    "due_date": "ISO8601 (optional)",
    "recurrence_pattern": "string (optional)",
    "reminder_config": "object (optional)"
  }
}
```

#### Event: task.updated

**Producer**: Chat API (ONLY)
**Consumers**: Notification Service, Reminder Service, Audit Logger
**Payload**:
```json
{
  "event_type": "task.updated",
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "actor_id": "user_id",
  "task_id": "string",
  "changes": {
    "field_name": {"old": "value", "new": "value"}
  }
}
```

#### Event: task.completed

**Producer**: Chat API (ONLY)
**Consumers**: Notification Service, Audit Logger, Analytics Service (future)
**Payload**:
```json
{
  "event_type": "task.completed",
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "actor_id": "user_id",
  "task_id": "string",
  "completed_at": "ISO8601"
}
```

#### Event: task.deleted

**Producer**: Chat API (ONLY)
**Consumers**: Notification Service, Reminder Service, Audit Logger
**Payload**:
```json
{
  "event_type": "task.deleted",
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "actor_id": "user_id",
  "task_id": "string"
}
```

#### Event: task.reminder.triggered

**Producer**: Reminder Service
**Consumers**: Notification Service
**Payload**:
```json
{
  "event_type": "task.reminder.triggered",
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "task_id": "string",
  "user_id": "string",
  "reminder_type": "due_date_reminder",
  "due_date": "ISO8601"
}
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a recurring task and see the first instance appear immediately (within 1 second)
- **SC-002**: Recurring task instances are generated automatically within 5 minutes of the scheduled time
- **SC-003**: Due date reminders are triggered within 1 minute of the configured reminder time
- **SC-004**: Real-time notifications are delivered to connected clients within 2 seconds of the triggering event
- **SC-005**: All Phase IV tasks continue to function identically without any user-visible changes or required migrations
- **SC-006**: System handles 10,000 recurring tasks with daily patterns without performance degradation
- **SC-007**: Audit logs capture 100% of task operations with complete before/after state for updates
- **SC-008**: System maintains 99.9% uptime for task operations during Dapr sidecar restarts or temporary unavailability
- **SC-009**: Task event processing has end-to-end latency under 500ms (event published → notification delivered)
- **SC-010**: Zero direct Kafka client usage in any service; all event publishing and subscription goes through Dapr

### Non-Functional Success Criteria

- **SC-011**: All services start successfully and enter "ready" state even when Dapr sidecar is temporarily unavailable
- **SC-012**: System passes automated smoke tests validating all Phase IV functionality after Phase V deployment
- **SC-013**: Every service exposes Kubernetes-compatible health endpoints (/health/live, /health/ready)
- **SC-014**: All event producers and consumers are clearly documented with ownership and SLAs
- **SC-015**: Rollback from Phase V to Phase IV can be executed in under 5 minutes with zero data loss

## Service Responsibilities *(new for Phase V)*

### Chat API (Producer Service)

**Role**: Authoritative source for all task operations
**Responsibilities**:
- Accept user task operations (create, update, delete, complete) via API endpoints
- Validate and persist task changes to database
- Publish task events (task.created, task.updated, task.completed, task.deleted) to Dapr Pub/Sub
- Remain the ONLY service that publishes task events

**Event Publishing**:
- Topics: `tasks.created`, `tasks.updated`, `tasks.completed`, `tasks.deleted`
- Protocol: Dapr Pub/Sub (NO direct Kafka)

### Notification Service (Consumer Service)

**Role**: Deliver real-time notifications to users
**Responsibilities**:
- Subscribe to task events via Dapr Pub/Sub
- Subscribe to reminder events (task.reminder.triggered)
- Deliver notifications to connected clients (WebSocket, Server-Sent Events, or similar)
- Respect user notification preferences
- Handle offline users gracefully (queue or skip based on notification type)

**Event Subscription**:
- Topics: `tasks.created`, `tasks.updated`, `tasks.completed`, `tasks.deleted`, `tasks.reminder.triggered`
- Protocol: Dapr Pub/Sub (NO direct Kafka)

### Reminder Service (Consumer Service)

**Role**: Schedule and trigger due date reminders
**Responsibilities**:
- Subscribe to task events (created, updated, deleted) to track tasks with due dates
- Maintain an internal schedule of upcoming reminders
- Trigger reminder events (task.reminder.triggered) at configured times
- Cancel reminders when tasks are completed or deleted
- Handle task updates that change due dates (reschedule reminders)

**Event Subscription**:
- Topics: `tasks.created`, `tasks.updated`, `tasks.deleted`, `tasks.completed`

**Event Publishing**:
- Topics: `tasks.reminder.triggered`

### Audit Logger Service (Consumer Service)

**Role**: Capture immutable audit trail of all task operations
**Responsibilities**:
- Subscribe to all task events
- Persist audit log entries with full event details
- Provide query interface for audit log retrieval
- Implement retention policies for long-term storage

**Event Subscription**:
- Topics: `tasks.created`, `tasks.updated`, `tasks.completed`, `tasks.deleted`

### Recurring Task Processor (New Background Service)

**Role**: Generate task instances from recurring task definitions
**Responsibilities**:
- Process recurring task definitions on a schedule (e.g., every hour)
- Generate new task instances when the next occurrence is due
- Invoke Chat API to create task instances (triggering standard task.created events)
- Handle edge cases (account inactive, end date reached, etc.)

**Important**: Does NOT publish events directly; creates tasks via Chat API

## Assumptions

- Users are authenticated via existing Phase IV authentication mechanism (JWT tokens)
- Task due dates and reminders use UTC timezone internally; client applications handle timezone conversion for display
- Recurring task processing runs on a periodic schedule (e.g., hourly or daily); sub-minute precision is not required for recurrence
- Notification delivery is best-effort; if a client is offline, notifications may be queued for a limited time or dropped
- Audit logs are write-only; no updates or deletions are allowed to maintain integrity
- Dapr Pub/Sub is configured with Kafka as the backing store, but services interact only with Dapr abstractions
- Kubernetes cluster has sufficient resources to run Dapr sidecars alongside application containers
- Existing Phase IV database schema remains unchanged; new fields are added as nullable columns or separate tables

## Dependencies

- Dapr runtime (v1.11 or later) deployed as sidecars to all services
- Kafka cluster (or Dapr-compatible pub/sub backend) configured and accessible
- Kubernetes cluster (Minikube for local, GKE/EKS/AKS for production)
- Existing Phase IV backend API and database
- Existing Phase IV authentication and authorization mechanisms

## Out of Scope

- Multi-user task assignments or collaboration features (future phase)
- Email or SMS notification delivery (in-app notifications only for Phase V)
- Task priority, labels, or categories beyond Phase IV capabilities
- Advanced recurrence patterns (e.g., "second Tuesday of each month", "every weekday except holidays")
- Task templates or bulk task creation
- Integration with external calendar systems (Google Calendar, Outlook, etc.)
- Mobile push notifications (in-app only for Phase V)
- Task analytics, reporting, or dashboards (basic list views only)

## Constraints

- NO breaking changes to Phase IV APIs, schemas, or contracts
- NO direct Kafka client usage in any service
- ALL event communication MUST use Dapr Pub/Sub
- Chat API is the ONLY producer of task events (created, updated, completed, deleted)
- All services MUST function (at least in degraded mode) when Dapr sidecar is temporarily unavailable
- Local Kubernetes deployment (Minikube) MUST succeed before any cloud deployment
- Rollback strategy MUST be defined and tested before implementation

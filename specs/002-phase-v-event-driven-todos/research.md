# Phase 0: Research & Technology Decisions

**Feature**: Phase V - Event-Driven Task Management
**Branch**: `002-phase-v-event-driven-todos`
**Date**: 2026-01-22

## Research Questions Resolved

### Q1: How to implement recurring task scheduling in event-driven architecture?

**Decision**: Use a dedicated Recurring Task Processor service with cron-like scheduling that invokes the Chat API to create task instances.

**Rationale**:
- Separates scheduling logic from core task management
- Maintains Chat API as single source of truth for task events
- Allows independent scaling of recurring task processing
- Follows event-driven pattern (processor creates tasks via API, triggering standard events)

**Alternatives Considered**:
- **Database triggers**: Rejected due to tight coupling to database layer and difficulty testing
- **External scheduler (Kubernetes CronJob)**: Rejected due to lack of dynamic scheduling and inability to handle variable recurrence patterns
- **Embedded scheduler in Chat API**: Rejected due to increased complexity and responsibility overload in Chat API

**Best Practices Applied**:
- Idempotency: Use unique identifiers to prevent duplicate task instance creation
- Failure handling: Retry failed task creation with exponential backoff
- Observability: Log all recurring task processing with correlation IDs

---

### Q2: What mechanism should be used for due date reminders?

**Decision**: Dedicated Reminder Service that subscribes to task events and maintains an in-memory priority queue of upcoming reminders, with periodic persistence for durability.

**Rationale**:
- Event-driven: Responds to task.created/updated/deleted events via Dapr Pub/Sub
- Scalable: Priority queue allows efficient O(log n) insertion and O(1) next-reminder lookup
- Fault-tolerant: Periodic snapshots to durable storage prevent reminder loss on restart
- Constitutional compliance: Gracefully degrades if Dapr sidecar unavailable (uses last known state)

**Alternatives Considered**:
- **Database polling**: Rejected due to high database load and poor scalability
- **External service (Twilio, SendGrid)**: Rejected for Phase V scope (in-app only)
- **Scheduled jobs per reminder**: Rejected due to resource overhead (10,000+ reminders)

**Best Practices Applied**:
- Use heap-based priority queue for O(log n) performance
- Snapshot reminder state every 5 minutes to durable storage
- Cancel reminders on task.completed or task.deleted events
- Reschedule on task.updated events with due date changes

---

### Q3: How to deliver real-time notifications to connected clients?

**Decision**: Notification Service using Server-Sent Events (SSE) for browser clients, subscribing to Dapr Pub/Sub for task and reminder events.

**Rationale**:
- SSE is simpler than WebSockets and sufficient for one-way notifications
- Works over HTTP, no special firewall configuration needed
- Browser-native EventSource API available
- Automatic reconnection handling built-in
- No additional protocol complexity (unlike WebSockets)

**Alternatives Considered**:
- **WebSockets**: Rejected due to increased complexity for one-way communication (overkill)
- **Long polling**: Rejected due to inefficiency and scalability concerns
- **Push notifications**: Out of scope for Phase V (in-app only)

**Best Practices Applied**:
- Per-user notification channels with authentication via JWT
- Exponential backoff for event processing failures
- Rate limiting to prevent notification spam (max 10/second per user)
- Heartbeat messages every 30 seconds to keep connections alive

---

### Q4: What storage strategy for audit logs?

**Decision**: Append-only table in existing PostgreSQL database with partitioning by date (monthly partitions).

**Rationale**:
- Reuses existing Phase IV database infrastructure (no new dependencies)
- Append-only semantics match audit log immutability requirement
- PostgreSQL partitioning provides automatic archival and query performance
- JSONB column type allows flexible event payload storage
- Constitutional compliance: Additive-only (new table, existing schema untouched)

**Alternatives Considered**:
- **Separate audit database**: Rejected due to operational complexity and Phase V scope
- **Object storage (S3)**: Rejected due to poor query performance for audit lookups
- **Elasticsearch**: Rejected due to additional infrastructure dependency

**Best Practices Applied**:
- Partition by month for efficient pruning (retention policy)
- Index on task_id, user_id, timestamp for common queries
- JSONB for event payload allows flexible schema evolution
- Write-only; no update or delete operations permitted

---

### Q5: How to ensure Phase IV backward compatibility?

**Decision**: Database schema migration strategy using nullable columns for all Phase V fields, with application-level defaults.

**Rationale**:
- Nullable columns allow Phase IV tasks to remain valid (no migration required)
- Phase V logic checks for null and provides defaults (e.g., no recurrence = one-time task)
- Database-level constraints prevent invalid states (e.g., due_date without reminder_config)
- Rollback-friendly: Phase V columns can be dropped without affecting Phase IV data

**Alternatives Considered**:
- **Separate tables**: Rejected due to query complexity and potential data inconsistency
- **JSON column**: Rejected due to loss of type safety and query performance
- **Required migrations**: Rejected due to constitution violation (Phase IV immutability)

**Best Practices Applied**:
- All Phase V columns nullable (recurrence_pattern, due_date, reminder_config)
- Application logic provides backward-compatible defaults
- Database constraints ensure data integrity (CHECK constraints)
- Reversible migrations for rollback scenarios

---

### Q6: Dapr configuration for Kafka Pub/Sub

**Decision**: Use Dapr Pub/Sub component with Kafka backend, configured with at-least-once delivery semantics and consumer groups per service.

**Rationale**:
- Dapr abstracts Kafka complexity (no Kafka client libraries in services)
- Consumer groups ensure each service instance receives events (load distribution)
- At-least-once delivery with idempotency keys prevents duplicate processing
- Constitutional compliance: Zero direct Kafka access

**Configuration**:
```yaml
# Dapr pubsub component (for reference, not code)
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka:9092"
  - name: consumerGroup
    value: "{service-name}"
  - name: clientId
    value: "{service-name}"
```

**Best Practices Applied**:
- One consumer group per service type (notification-service, reminder-service, audit-logger)
- Idempotency keys (event_id) prevent duplicate event processing
- Dead-letter queue for failed events (retry 3 times, then DLQ)
- Topic naming convention: `taskflow.{entity}.{action}` (e.g., taskflow.tasks.created)

---

### Q7: Kubernetes health check strategy for Dapr unavailability

**Decision**: Separate liveness and readiness probes; services remain "live" even without Dapr, but mark "not ready" if Dapr unavailable.

**Rationale**:
- Liveness: Service process is healthy (prevents unnecessary restarts)
- Readiness: Service can handle traffic (includes Dapr connectivity check)
- Constitutional compliance: Services start without Dapr (graceful degradation)
- Prevents restart loops if Dapr sidecar delayed or fails

**Implementation Pattern**:
- `/health/live`: Always returns 200 if service process running
- `/health/ready`: Returns 200 only if Dapr sidecar accessible AND database reachable
- Startup probe: Allows 60 seconds for Dapr sidecar initialization

**Best Practices Applied**:
- Liveness checks lightweight (no I/O operations)
- Readiness checks include all critical dependencies
- Startup probe with longer timeout for initialization
- HTTP-based probes (no exec overhead)

---

## Technology Stack Summary

### Backend Language & Framework
- **Python 3.11+** (existing Phase IV stack)
- **FastAPI** (existing Phase IV framework)
- **Pydantic** for data validation

### Event Infrastructure
- **Dapr v1.11+** (Pub/Sub abstraction)
- **Kafka 3.x** (backing Pub/Sub store)
- **NO direct Kafka client libraries**

### Data Storage
- **PostgreSQL 14+** (existing Phase IV database)
- **Table partitioning** for audit logs
- **Nullable columns** for Phase V fields

### Real-Time Communication
- **Server-Sent Events (SSE)** for notifications
- **JWT authentication** for SSE channels

### Scheduling & Background Jobs
- **APScheduler** for Reminder Service priority queue processing
- **Cron-style scheduler** for Recurring Task Processor

### Container Orchestration
- **Kubernetes 1.25+**
- **Minikube** for local development
- **GKE/EKS/AKS** for production (TBD)

### Observability
- **Structured logging** (JSON format)
- **Health endpoints** (/health/live, /health/ready)
- **Dapr tracing** integration (future)

---

## Performance & Scalability Considerations

### Recurring Task Processing
- **Batch size**: Process 100 recurring tasks per iteration
- **Schedule interval**: Every 5 minutes (configurable)
- **Concurrency control**: Distributed lock (database-level) prevents duplicate processing

### Reminder Service
- **Priority queue capacity**: 100,000 reminders in-memory
- **Snapshot frequency**: Every 5 minutes to durable storage
- **Event processing rate**: 1,000 events/second per instance

### Notification Service
- **SSE connections**: 10,000 concurrent connections per instance
- **Event processing rate**: 5,000 events/second per instance
- **Backpressure handling**: Drop events if client connection slow (configurable)

### Audit Logger
- **Batch writes**: Buffer 100 events, write every 1 second or on buffer full
- **Partition strategy**: Monthly partitions, auto-prune after 2 years
- **Query performance**: Indexed by task_id, user_id, timestamp

---

## Security Considerations

### Authentication & Authorization
- Reuse existing Phase IV JWT authentication
- SSE connections require valid JWT in query parameter or Authorization header
- Service-to-service communication secured via Dapr mTLS

### Data Privacy
- Audit logs contain only metadata (no sensitive task descriptions in logs beyond necessary)
- Event payloads sanitized before publishing (no PII in event metadata)

### Secrets Management
- Kafka credentials stored in Kubernetes Secrets
- Database credentials in Kubernetes Secrets (existing Phase IV)
- No secrets in code or configuration files

---

## Risk Mitigation Strategies

### Risk 1: Dapr Sidecar Unavailability
- **Mitigation**: Services cache last-known state and operate in degraded mode
- **Detection**: Readiness probe fails, Kubernetes stops routing traffic
- **Recovery**: Automatic retry with exponential backoff

### Risk 2: Kafka Broker Failure
- **Mitigation**: Kafka replication factor 3, Dapr retries failed publishes
- **Detection**: Publish failures logged, alerting on error rate spike
- **Recovery**: Dapr automatic retry (up to 3 attempts with backoff)

### Risk 3: Duplicate Task Instances (Recurring Tasks)
- **Mitigation**: Idempotency keys (task_id + occurrence_date), database unique constraint
- **Detection**: Duplicate key violations logged but non-fatal
- **Recovery**: Graceful failure (log and skip duplicate)

### Risk 4: Notification Delivery Failure
- **Mitigation**: Best-effort delivery, no guarantees for offline users
- **Detection**: Failed SSE writes logged with user_id
- **Recovery**: Next event delivery attempt (no queueing for offline users in Phase V)

### Risk 5: Reminder Skipped Due to Service Restart
- **Mitigation**: Reminder state persisted every 5 minutes, catch-up on startup
- **Detection**: Compare last snapshot timestamp to current time on startup
- **Recovery**: Trigger overdue reminders immediately on service start

---

## Rollback Strategy

### Rollback Procedure (Phase V → Phase IV)

1. **Stop Phase V services** (notification-service, reminder-service, audit-logger, recurring-task-processor)
2. **Verify Chat API still functional** (Phase IV smoke tests)
3. **Disable Dapr Pub/Sub** on Chat API (remove pubsub component)
4. **Database**: NO changes required (Phase V columns nullable, Phase IV ignores them)
5. **Verify Phase IV functionality** (automated smoke tests)

**Time Estimate**: Under 5 minutes
**Data Loss**: Zero (Phase IV data untouched)

### Rollforward Strategy (Rollback Failed)

If rollback fails, proceed forward with fixes:
1. **Isolate failing component** (use Kubernetes labels to target specific service)
2. **Apply hotfix** (patch deployment with fixed image)
3. **Verify fix** (smoke tests pass)
4. **Resume normal operations**

---

## Open Questions (To Be Resolved in Phase 1)

1. What is the exact Phase IV database schema? (Need to review for nullable column additions)
2. What is the existing JWT authentication flow? (Need to integrate SSE authentication)
3. What are the current Phase IV API endpoints? (Need to avoid conflicts)
4. What is the Kubernetes cluster configuration? (Need to plan Dapr deployment)

These questions will be resolved in Phase 1 (Design & Contracts) by examining existing Phase IV code and infrastructure.

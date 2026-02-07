# Implementation Plan: Phase V - Event-Driven Task Management

**Branch**: `002-phase-v-event-driven-todos` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-phase-v-event-driven-todos/spec.md`

## Summary

Phase V extends TaskFlow AI with event-driven task management capabilities while maintaining absolute backward compatibility with Phase IV. The implementation introduces four prioritized user stories: recurring task automation (P1), due date reminders (P1), real-time notifications (P2), and comprehensive audit logging (P3).

**Technical Approach**:
- Event-driven architecture using Dapr Pub/Sub with Kafka backend
- Five services: Chat API (extended), Notification Service, Reminder Service, Audit Logger, Recurring Task Processor
- Additive-only database schema changes (all Phase V columns nullable)
- Server-Sent Events (SSE) for real-time client notifications
- Local-first validation on Minikube before cloud deployment

**Key Constraints**:
- Zero breaking changes to Phase IV functionality
- Chat API remains ONLY producer of task events (created, updated, completed, deleted)
- NO direct Kafka client usage (100% via Dapr abstractions)
- Services MUST function gracefully when Dapr sidecar temporarily unavailable
- Rollback to Phase IV in <5 minutes with zero data loss

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (existing Phase IV), Dapr SDK (Python), APScheduler, asyncpg (PostgreSQL)
**Storage**: PostgreSQL 14+ (existing Phase IV database with additive schema changes)
**Testing**: pytest (existing Phase IV test suite extended)
**Target Platform**: Kubernetes 1.25+ (Minikube for local, GKE/EKS/AKS for cloud)
**Project Type**: Web application (backend services with event-driven communication)
**Performance Goals**: <500ms event latency (publish → notification delivery), 10,000 concurrent SSE connections per Notification Service instance, 10,000 recurring tasks processed without degradation
**Constraints**: Phase IV immutability (SC-005), Dapr-only Kafka access (SC-010), local success before cloud (Principle VI)
**Scale/Scope**: 5 services (1 extended, 4 new), 5 event types, 10+ new database columns (nullable), 4 user stories (2 P1, 1 P2, 1 P3)

---

## Constitution Check

*GATE: Must pass before implementation. Re-checked after design completion.*

### Principle I: Phase IV Immutability
- ✅ **PASS**: All Phase IV fields unchanged; new columns nullable
- ✅ **PASS**: Phase IV smoke tests included in validation (Step 5 in quickstart.md)
- ✅ **PASS**: Existing Phase IV tasks function identically (FR-009, SC-005)

### Principle II: Additive-Only Changes
- ✅ **PASS**: Database schema uses nullable columns only (data-model.md)
- ✅ **PASS**: No modifications to existing APIs (Chat API extended with new endpoints only)
- ✅ **PASS**: Application-level defaults for Phase V fields (no required migrations)

### Principle III: Event-Driven Architecture
- ✅ **PASS**: All inter-service communication via events (events-schema.yaml)
- ✅ **PASS**: No direct service-to-service synchronous calls for state changes

### Principle IV: Dapr Abstraction Layer
- ✅ **PASS**: All event publishing via Dapr SDK (no Kafka client libraries)
- ✅ **PASS**: All event subscription via Dapr SDK
- ✅ **PASS**: Dapr Pub/Sub component configured (research.md, Q6)

### Principle V: Kubernetes Runtime
- ✅ **PASS**: All services containerized with Kubernetes manifests
- ✅ **PASS**: Health endpoints (/health/live, /health/ready) for all services
- ✅ **PASS**: No assumptions of local filesystem persistence

### Principle VI: Local-First Validation
- ✅ **PASS**: Minikube deployment documented (quickstart.md)
- ✅ **PASS**: Complete local validation before cloud promotion

### Principle VII: Human-in-the-Loop Governance
- ✅ **PASS**: Plan requires approval before tasks generation
- ✅ **PASS**: Tasks require approval before implementation

### Deployment & Runtime Requirements: Database & Data Integrity
- ✅ **PASS**: Existing schema remains valid (nullable columns)
- ✅ **PASS**: Migrations reversible (rollback documented)
- ✅ **PASS**: Zero data loss (Phase IV data untouched)

### Deployment & Runtime Requirements: Resilience & Fault Tolerance
- ✅ **PASS**: Services start without Dapr (readiness may fail, liveness passes)
- ✅ **PASS**: Graceful degradation documented (research.md, Q7)
- ✅ **PASS**: Health checks separate liveness/readiness

### Deployment & Runtime Requirements: Verification & Rollback
- ✅ **PASS**: Phase IV regression tests in validation (quickstart.md, Step 5)
- ✅ **PASS**: Rollback strategy defined (research.md, Rollback Strategy; quickstart.md, Step 10)
- ✅ **PASS**: Rollback tested in quickstart validation

**Constitution Check Status**: ✅ **ALL GATES PASS**

---

## Project Structure

### Documentation (this feature)

```text
specs/002-phase-v-event-driven-todos/
├── spec.md                          # Feature specification (approved)
├── plan.md                          # This file (/sp.plan command output)
├── research.md                      # Phase 0 output (technology decisions)
├── data-model.md                    # Phase 1 output (entity definitions)
├── quickstart.md                    # Phase 1 output (local deployment guide)
├── contracts/                       # Phase 1 output
│   └── events-schema.yaml           # Event definitions for Dapr Pub/Sub
├── checklists/                      # Quality validation
│   └── requirements.md              # Specification quality checklist (PASS)
└── tasks.md                         # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root - existing Phase IV structure extended)

```text
backend/                             # Existing Phase IV backend
├── src/
│   ├── api/                         # EXISTING: Phase IV API routes
│   │   ├── auth.py                  # UNCHANGED
│   │   ├── tasks.py                 # EXTENDED: Add Phase V fields to endpoints
│   │   └── health.py                # UNCHANGED
│   ├── models/                      # EXISTING: Phase IV database models
│   │   ├── user.py                  # UNCHANGED
│   │   └── task.py                  # EXTENDED: Add Phase V fields
│   ├── services/                    # EXISTING: Phase IV business logic
│   │   ├── task_service.py          # EXTENDED: Handle Phase V fields, publish events
│   │   └── user_service.py          # UNCHANGED
│   ├── middleware/                  # EXISTING: Phase IV middleware
│   │   └── auth.py                  # UNCHANGED
│   ├── dapr/                        # NEW: Dapr integration
│   │   ├── publisher.py             # NEW: Dapr Pub/Sub event publishing
│   │   └── health.py                # NEW: Dapr connectivity health checks
│   ├── config.py                    # EXTENDED: Add Dapr configuration
│   ├── database.py                  # UNCHANGED
│   └── main.py                      # EXTENDED: Initialize Dapr SDK
│
├── services/                        # NEW: Phase V microservices
│   ├── notification/                # NEW: Notification Service
│   │   ├── main.py                  # Service entry point
│   │   ├── sse_handler.py           # Server-Sent Events handling
│   │   ├── event_consumer.py        # Dapr Pub/Sub event subscription
│   │   └── health.py                # Health endpoints
│   ├── reminder/                    # NEW: Reminder Service
│   │   ├── main.py                  # Service entry point
│   │   ├── priority_queue.py        # Reminder priority queue
│   │   ├── event_consumer.py        # Dapr Pub/Sub event subscription
│   │   ├── scheduler.py             # Reminder triggering logic
│   │   └── health.py                # Health endpoints
│   ├── audit_logger/                # NEW: Audit Logger Service
│   │   ├── main.py                  # Service entry point
│   │   ├── event_consumer.py        # Dapr Pub/Sub event subscription
│   │   ├── storage.py               # Audit log persistence
│   │   └── health.py                # Health endpoints
│   └── recurring_processor/         # NEW: Recurring Task Processor
│       ├── main.py                  # Service entry point
│       ├── scheduler.py             # Cron-like recurring task processing
│       ├── task_generator.py        # Task instance generation logic
│       └── health.py                # Health endpoints
│
└── tests/                           # EXISTING: Phase IV test suite
    ├── phase4/                      # UNCHANGED: Phase IV regression tests
    │   ├── test_auth.py             # UNCHANGED
    │   ├── test_tasks.py            # UNCHANGED
    │   └── test_api.py              # UNCHANGED
    ├── phase5/                      # NEW: Phase V feature tests
    │   ├── test_recurring_tasks.py  # NEW: User Story 1 tests
    │   ├── test_reminders.py        # NEW: User Story 2 tests
    │   ├── test_notifications.py    # NEW: User Story 3 tests
    │   ├── test_audit_logs.py       # NEW: User Story 4 tests
    │   └── test_events.py           # NEW: Event publishing/subscription tests
    └── integration/                 # EXTENDED: Integration tests
        ├── test_event_flow.py       # NEW: End-to-end event flow tests
        └── test_phase4_compat.py    # NEW: Phase IV compatibility tests

k8s/                                 # EXISTING: Kubernetes manifests (Phase IV)
├── infrastructure/                  # EXTENDED: Add Kafka deployment
│   ├── postgres-deployment.yaml     # UNCHANGED
│   └── kafka-deployment.yaml        # NEW: Kafka + Zookeeper
├── dapr/                            # NEW: Dapr components
│   ├── pubsub.yaml                  # NEW: Dapr Pub/Sub component (Kafka backend)
│   └── subscriptions.yaml           # NEW: Dapr subscription configurations
└── services/                        # EXTENDED: Add Phase V service deployments
    ├── chat-api-deployment.yaml     # EXTENDED: Add Dapr annotations
    ├── notification-service.yaml    # NEW: Notification Service deployment
    ├── reminder-service.yaml        # NEW: Reminder Service deployment
    ├── audit-logger.yaml            # NEW: Audit Logger deployment
    └── recurring-processor.yaml     # NEW: Recurring Task Processor deployment

scripts/                             # EXISTING: Utility scripts
├── migrate.py                       # EXTENDED: Add Phase V migration
├── load-test.py                     # NEW: Load testing for Phase V
└── measure-latency.py               # NEW: Event latency measurement
```

**Structure Decision**: Extending existing Phase IV backend structure with new `services/` directory for Phase V microservices. Chat API remains in `backend/src/` as it's an extension of Phase IV, not a new service. All Phase V services are self-contained under `services/` to enable independent deployment and scaling.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected**. All constitution checks PASS. No complexity justification required.

---

## High-Level Architecture

### Overview

Phase V introduces an event-driven architecture where the Chat API (extended from Phase IV) remains the authoritative source for task operations and the ONLY producer of task events. Four new microservices consume these events to provide recurring tasks, reminders, notifications, and audit logging functionality.

**Component Classification**:
- **UNCHANGED**: Phase IV database, authentication, user management, core task CRUD logic
- **EXTENDED**: Chat API (Phase IV) - adds Phase V fields to task endpoints and publishes events to Dapr
- **REUSED**: PostgreSQL database (Phase IV), JWT authentication (Phase IV), FastAPI framework (Phase IV)
- **NEW**: Notification Service, Reminder Service, Audit Logger Service, Recurring Task Processor, Dapr Pub/Sub integration, Kafka cluster, SSE endpoint

---

## Architecture Flow

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER / CLIENT                                  │
│  (Browser, Mobile App, Chat Interface)                                  │
└────────┬────────────────────────────────────────────────────┬───────────┘
         │                                                    │
         │ HTTP/REST (Task CRUD)                            │ SSE (Notifications)
         │                                                    │
┌────────▼────────────────────────────────────────────────────▼───────────┐
│                          CHAT API (Extended Phase IV)                   │
│  - ONLY producer of task events                                         │
│  - Publishes to Dapr Pub/Sub: task.created, .updated, .completed, .deleted │
│  - Extends Phase IV with nullable Phase V fields                        │
└────────┬────────────────────────────────────────────────────┬───────────┘
         │                                                    │
         │ Dapr Pub/Sub                                       │ PostgreSQL
         │ (NO direct Kafka)                                  │ (Phase IV DB)
         │                                                    │
┌────────▼────────────────────────────────────────────────────▼───────────┐
│                          DAPR RUNTIME                                   │
│  - Pub/Sub component (Kafka backend)                                   │
│  - Topics: taskflow.tasks.{created,updated,completed,deleted}           │
│  - At-least-once delivery, idempotency via event_id                    │
└────┬────────┬────────────────────┬─────────────────────────────────────┘
     │        │                    │
     │        │                    └─────────────────────┐
     │        │                                          │
┌────▼────────▼────────┐  ┌─────────────────┐  ┌────────▼────────┐  ┌────────────────┐
│  NOTIFICATION SVC     │  │  REMINDER SVC   │  │  AUDIT LOGGER   │  │  RECURRING     │
│  - Subscribes to all  │  │  - Subscribes   │  │  - Subscribes   │  │  TASK          │
│    task events        │  │    to task      │  │    to all task  │  │  PROCESSOR     │
│  - Subscribes to      │  │    events       │  │    events       │  │  - Cron-style  │
│    reminder events    │  │  - Maintains    │  │  - Writes to    │  │    scheduler   │
│  - Delivers via SSE   │  │    priority     │  │    task_events  │  │  - Invokes     │
│                       │  │    queue        │  │    table        │  │    Chat API    │
│                       │  │  - Publishes:   │  │                 │  │    to create   │
│                       │  │    task.reminder│  │                 │  │    instances   │
│                       │  │    .triggered   │  │                 │  │                │
└───────────────────────┘  └─────────────────┘  └─────────────────┘  └────────────────┘
         │                         │                      │
         └─────────────────────────┴──────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │   POSTGRESQL    │
                          │  (Phase IV DB)  │
                          │  + Phase V cols │
                          │  + task_events  │
                          │  + reminder_    │
                          │    schedule     │
                          └─────────────────┘
```

---

## Service Interactions

### User Story 1: Recurring Task Automation (P1)

**Flow**:
1. User creates recurring task via Chat API: `POST /api/v1/tasks` with `recurrence_pattern: "daily:"`
2. Chat API validates input, creates task in database, publishes `task.created` event to Dapr
3. Notification Service receives event, sends SSE notification to user ("Task created")
4. Recurring Task Processor runs on schedule (every 5 min), queries tasks needing new instances
5. For each recurring task due, Processor invokes Chat API `POST /api/v1/tasks` (with `parent_recurring_task_id`)
6. Chat API creates instance, publishes `task.created` event (same flow as step 2)

**Key Decision**: Recurring Task Processor does NOT publish events directly; it creates tasks via Chat API, maintaining Chat API as the ONLY event producer.

---

### User Story 2: Due Date Reminders (P1)

**Flow**:
1. User creates task with `due_date` and `reminder_offset` via Chat API
2. Chat API publishes `task.created` event with reminder config
3. Reminder Service receives event, calculates trigger time (`due_date - reminder_offset`), adds to priority queue
4. Reminder Service snapshots queue to `reminder_schedule` table every 5 min (durability)
5. At trigger time, Reminder Service publishes `task.reminder.triggered` event to Dapr
6. Notification Service receives reminder event, sends SSE notification to user

**Edge Case Handling**:
- Task updated with new `due_date`: Reminder Service receives `task.updated` event, reschedules reminder
- Task completed/deleted: Reminder Service receives event, cancels reminder (removes from queue)
- Service restart: Loads pending reminders from `reminder_schedule` snapshot, rebuilds priority queue

---

### User Story 3: Real-Time Notifications (P2)

**Flow**:
1. User opens SSE connection: `GET /api/v1/notifications/stream` (authenticated via JWT)
2. Notification Service registers connection (in-memory map: user_id → connection)
3. Any task event occurs (created, updated, completed, deleted) → Chat API publishes event
4. Notification Service receives event, looks up user_id's active connections, sends SSE message
5. Client receives notification within 2 seconds (SC-004)

**Rate Limiting**:
- Max 10 notifications/second per connection
- Max 3 concurrent connections per user

**Heartbeat**:
- Notification Service sends heartbeat every 30 seconds to keep connection alive
- If heartbeat fails, connection closed and removed from registry

---

### User Story 4: Comprehensive Audit Logging (P3)

**Flow**:
1. Any task operation → Chat API publishes event
2. Audit Logger Service receives event, writes to `task_events` table (partitioned by month)
3. Event includes: event_id, event_type, task_id, user_id, timestamp, payload (JSONB)
4. Administrator queries audit logs: `GET /api/v1/audit/tasks/{task_id}` (future endpoint)

**Retention**:
- Monthly partitions (automated via pg_partman or manual partition management)
- Archive partitions older than 2 years (configurable)

---

## Dapr Components

### Pub/Sub Component (Kafka Backend)

**File**: `k8s/dapr/pubsub.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-pubsub
  namespace: default
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka.default.svc.cluster.local:9092"
  - name: authType
    value: "none"  # Phase V: no auth (local/dev); add SASL for prod
  - name: consumerGroup
    value: "{appId}"  # Each service has its own consumer group
  - name: clientId
    value: "{appId}"
  - name: initialOffset
    value: "newest"  # Start from latest on first subscription
  - name: maxMessageBytes
    value: "1048576"  # 1MB max message size
scopes:
- chat-api
- notification-service
- reminder-service
- audit-logger
```

### Topic Subscriptions

**Notification Service Subscriptions**:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: notification-task-events
spec:
  pubsubname: taskflow-pubsub
  topic: taskflow.tasks.created
  route: /events/task-created
  scopes:
  - notification-service
---
# ... (repeat for updated, completed, deleted, reminder-triggered)
```

**Reminder Service Subscriptions**:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: reminder-task-events
spec:
  pubsubname: taskflow-pubsub
  topic: taskflow.tasks.created
  route: /events/task-created
  scopes:
  - reminder-service
---
# ... (repeat for updated, deleted, completed)
```

**Audit Logger Subscriptions**:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: audit-task-events
spec:
  pubsubname: taskflow-pubsub
  topic: taskflow.tasks.created
  route: /events/task-created
  scopes:
  - audit-logger
---
# ... (repeat for updated, completed, deleted)
```

---

## Kafka Topics

### Topic Naming Convention

Format: `taskflow.{entity}.{action}`

**Topics Created**:
1. `taskflow.tasks.created` - Task creation events (Producer: Chat API ONLY)
2. `taskflow.tasks.updated` - Task update events (Producer: Chat API ONLY)
3. `taskflow.tasks.completed` - Task completion events (Producer: Chat API ONLY)
4. `taskflow.tasks.deleted` - Task deletion events (Producer: Chat API ONLY)
5. `taskflow.tasks.reminder-triggered` - Reminder trigger events (Producer: Reminder Service)

**Topic Configuration** (via Kafka admin or Dapr defaults):
- Partitions: 3 (per topic)
- Replication factor: 3 (production); 1 (local Minikube)
- Retention: 7 days (configurable)
- Partition key: `task_id` (ensures ordered events per task)

---

## Kubernetes Deployment Flow

### Local (Minikube) Execution Phases

#### Phase 1: Infrastructure Setup
1. Start Minikube cluster (4 CPU, 8GB RAM)
2. Initialize Dapr control plane (`dapr init --kubernetes`)
3. Deploy PostgreSQL (existing Phase IV deployment)
4. Deploy Kafka + Zookeeper
5. Apply Dapr Pub/Sub component manifest
6. Run database migration (Phase V schema)

**Duration**: ~10 minutes
**Validation**: All infrastructure pods Running, Dapr components registered

---

#### Phase 2: Service Deployment
1. Deploy Chat API with Dapr annotations (extended Phase IV)
2. Deploy Notification Service
3. Deploy Reminder Service
4. Deploy Audit Logger
5. Deploy Recurring Task Processor

**Deployment Order Rationale**: Chat API first (event producer), then consumers

**Duration**: ~5 minutes
**Validation**: All services Running with 2/2 containers (app + daprd sidecar)

---

#### Phase 3: Phase IV Regression Validation
1. Port-forward Chat API
2. Run Phase IV smoke tests (`pytest tests/phase4/`)
3. Manual validation: Create/list/update/delete Phase IV tasks

**Duration**: ~2 minutes
**Validation**: All Phase IV tests PASS

---

#### Phase 4: Phase V Feature Validation
1. Test recurring task creation (User Story 1)
2. Test due date reminder scheduling (User Story 2)
3. Test SSE notifications (User Story 3)
4. Test audit log capture (User Story 4)
5. Verify event flow (Dapr topics, consumer logs)

**Duration**: ~5 minutes
**Validation**: All user stories testable, events flowing

---

#### Phase 5: Performance & Resilience Testing
1. Load test: Create 100 recurring tasks
2. Measure event latency (<500ms target)
3. Test Dapr unavailability (service survives with liveness passing)
4. Health endpoint checks (all services 200 OK)

**Duration**: ~5 minutes
**Validation**: Performance targets met, graceful degradation works

---

#### Phase 6: Rollback Validation
1. Delete Phase V services
2. Remove Dapr from Chat API
3. Run Phase IV smoke tests (verify rollback succeeds)
4. Restore Phase V (verify rollforward works)

**Duration**: ~5 minutes (<5 min rollback target met)
**Validation**: Rollback successful, Phase IV intact, rollforward restores Phase V

**Total Local Validation Time**: ~32 minutes

---

### Cloud Execution Phases

**Prerequisite**: Local validation MUST succeed before proceeding.

#### Phase 1: Cloud Cluster Provisioning
1. Provision managed Kubernetes cluster (GKE/EKS/AKS)
2. Configure kubectl context for cloud cluster
3. Initialize Dapr control plane (`dapr init --kubernetes`)
4. Provision managed PostgreSQL (Cloud SQL / RDS / Azure Database)
5. Provision managed Kafka (Confluent Cloud / Amazon MSK / Azure Event Hubs)

**Duration**: ~30 minutes
**Validation**: Cluster ready, managed services accessible

---

#### Phase 2: Configuration & Secrets
1. Create Kubernetes secrets for database credentials
2. Create Kubernetes secrets for Kafka credentials (SASL)
3. Update Dapr Pub/Sub component with cloud Kafka broker URLs
4. Configure TLS for Dapr mTLS (production security)

**Duration**: ~10 minutes
**Validation**: Secrets created, Dapr component updated

---

#### Phase 3: Service Deployment (Blue-Green)
1. Deploy Phase V services to "green" environment (separate namespace)
2. Run smoke tests against green environment
3. If tests pass, switch traffic to green (update Ingress/LoadBalancer)
4. If tests fail, rollback by routing traffic back to blue (Phase IV)

**Duration**: ~15 minutes
**Validation**: Green environment healthy, traffic routed successfully

---

#### Phase 4: Monitoring & Observability
1. Configure Prometheus for metrics scraping
2. Configure Grafana dashboards for Phase V services
3. Configure alerting rules (event latency, error rates, etc.)
4. Verify Dapr tracing integration (distributed tracing)

**Duration**: ~20 minutes
**Validation**: Dashboards visible, alerts configured

---

#### Phase 5: Production Traffic Validation
1. Monitor Phase IV regression metrics (ensure no degradation)
2. Monitor Phase V feature usage (recurring tasks, reminders, notifications)
3. Monitor event latency (<500ms target)
4. Monitor error rates (<0.1% target)

**Duration**: Ongoing (first 24 hours critical)
**Validation**: SLOs met, no Phase IV regression detected

**Total Cloud Deployment Time**: ~75 minutes (initial), ongoing monitoring

---

## Risk Controls & Safeguards

### Risk 1: Dapr Sidecar Unavailability

**Control**:
- Separate liveness (always pass) and readiness (fail if Dapr unavailable) probes
- Services cache last-known Dapr state and operate in degraded mode
- Kubernetes stops routing traffic to not-ready pods (graceful degradation)

**Detection**:
- Readiness probe failures trigger alerts
- Dapr connectivity errors logged with ERROR level

**Recovery**:
- Automatic: Dapr sidecar restart recovers service readiness
- Manual: Restart service pod if Dapr sidecar stuck

---

### Risk 2: Kafka Broker Failure

**Control**:
- Kafka replication factor 3 (production)
- Dapr retries failed event publishes (up to 3 attempts with exponential backoff)
- Dead-letter queue (DLQ) for events that fail after retries

**Detection**:
- Event publish failures logged
- Alert on high error rate (>1% over 5 min)

**Recovery**:
- Automatic: Dapr retry recovers transient failures
- Manual: Process DLQ events after Kafka recovery

---

### Risk 3: Duplicate Task Instances (Recurring Tasks)

**Control**:
- Database unique constraint: `(parent_recurring_task_id, occurrence_date)`
- Idempotency key in task creation (task_id deterministic from parent + date)

**Detection**:
- Duplicate key violations logged (non-fatal, expected during retries)

**Recovery**:
- Automatic: Graceful failure, log and skip duplicate

---

### Risk 4: Notification Delivery Failure

**Control**:
- Best-effort delivery (no guarantees for offline users in Phase V)
- Rate limiting prevents client overload

**Detection**:
- Failed SSE writes logged with user_id

**Recovery**:
- Next notification delivery attempt (no persistent queue in Phase V)

---

### Risk 5: Reminder Missed Due to Service Restart

**Control**:
- Reminder state persisted every 5 minutes to `reminder_schedule` table
- On startup, load pending reminders and trigger overdue ones immediately

**Detection**:
- Compare last snapshot timestamp to current time on startup
- Log overdue reminders triggered

**Recovery**:
- Automatic: Catch-up mechanism triggers missed reminders

---

### Risk 6: Phase IV Regression

**Control**:
- Automated Phase IV smoke tests run before Phase V validation
- Separate Phase IV test suite (`tests/phase4/`) maintained
- Phase IV functionality monitored separately in production

**Detection**:
- Phase IV smoke tests FAIL
- Phase IV error rate increases in production

**Recovery**:
- Rollback to Phase IV immediately (documented procedure in quickstart.md)
- Zero data loss (Phase V columns nullable, Phase IV ignores them)

---

## Rollback Strategies

### Rollback Scenario 1: Phase V Service Failure

**Trigger**: Phase V service (notification, reminder, audit, recurring) fails startup or has critical bug

**Procedure**:
1. Scale failing service to 0 replicas: `kubectl scale deployment <service> --replicas=0`
2. Verify Chat API still functional (Phase IV operations work)
3. Verify Phase IV smoke tests PASS
4. Fix bug, redeploy service
5. Scale service back up

**Duration**: <2 minutes (to isolate failure), fix time varies
**Data Loss**: None (events queued in Kafka, processed when service recovers)

---

### Rollback Scenario 2: Chat API Event Publishing Bug

**Trigger**: Chat API publishes malformed events, breaking consumers

**Procedure**:
1. Remove Dapr annotations from Chat API deployment
2. Restart Chat API (now Phase IV-only mode, no event publishing)
3. Verify Phase IV smoke tests PASS
4. Fix event publishing bug
5. Redeploy Chat API with Dapr annotations
6. Verify event schema validation

**Duration**: <5 minutes (to disable Dapr), fix time varies
**Data Loss**: Events not published during rollback window (acceptable for Phase V features)

---

### Rollback Scenario 3: Full Phase V Rollback

**Trigger**: Critical Phase V bug affecting Phase IV or multiple Phase V failures

**Procedure** (documented in quickstart.md Step 10):
1. Delete all Phase V services: `kubectl delete deployment notification-service reminder-service audit-logger recurring-task-processor`
2. Remove Dapr annotations from Chat API: `kubectl annotate deployment chat-api dapr.io/enabled-`
3. Restart Chat API: `kubectl rollout restart deployment chat-api`
4. Run Phase IV smoke tests: `pytest tests/phase4/`
5. Verify all tests PASS

**Duration**: <5 minutes
**Data Loss**: Zero (Phase IV data untouched, Phase V columns ignored)

**Rollback Validation**:
- Phase IV tasks still functional
- No errors in Chat API logs
- Database schema intact (Phase V columns remain but unused)

**Rollforward** (after fix):
1. Re-enable Dapr on Chat API
2. Redeploy Phase V services
3. Run full validation (Phase IV + Phase V tests)

**Duration**: <10 minutes (deployment + validation)

---

## 📜 History & Decision Log (Append-Only)

### Entry 0: Plan Created
**Date**: 2026-01-22
**Author**: Claude Sonnet 4.5
**Decision**: Phase V implementation plan created following approved specification (spec.md)
**Context**: Constitutional workflow (Constitution → Spec → Plan → Tasks → Implementation)
**Rationale**: Plan documents architecture, technology decisions, and deployment strategy to ensure Phase IV immutability and Dapr-only Kafka access.

---

### Entry 1: Server-Sent Events (SSE) Chosen for Notifications
**Date**: 2026-01-22
**Decision**: Use SSE instead of WebSockets for real-time notifications
**Rationale**: SSE simpler for one-way communication, browser-native EventSource API, automatic reconnection, no firewall configuration needed
**Alternatives Rejected**: WebSockets (overkill for one-way), Long polling (inefficient)
**Reference**: research.md, Q3

---

### Entry 2: Recurring Task Processor Invokes Chat API (Not Direct Event Publishing)
**Date**: 2026-01-22
**Decision**: Recurring Task Processor creates task instances by calling Chat API, NOT by publishing events directly
**Rationale**: Maintains Chat API as ONLY producer of task events (constitutional constraint, FR-012)
**Impact**: Simpler event model, no special-case event sources, consistent audit trail
**Reference**: Service Responsibilities section, spec.md

---

### Entry 3: Nullable Columns for All Phase V Fields
**Date**: 2026-01-22
**Decision**: All Phase V database columns nullable (due_date, recurrence_pattern, etc.)
**Rationale**: Backward compatibility (Phase IV tasks remain valid without migration), rollback safety (columns can be dropped)
**Constitutional Principle**: Principle II (Additive-Only Changes)
**Reference**: data-model.md, Migration Strategy

---

### Entry 4: At-Least-Once Delivery with Idempotency
**Date**: 2026-01-22
**Decision**: Accept Dapr/Kafka at-least-once delivery semantics; implement idempotency via event_id
**Rationale**: Simpler than exactly-once, industry-standard pattern, acceptable for task management use case
**Implementation**: All events include unique event_id (UUID); services track processed events to detect duplicates
**Reference**: events-schema.yaml, Delivery Guarantees

---

### Entry 5: Monthly Partitioning for Audit Logs
**Date**: 2026-01-22
**Decision**: Partition `task_events` table by month using PostgreSQL RANGE partitioning
**Rationale**: Efficient pruning for retention policies, improved query performance for recent events
**Trade-off**: Additional partition management overhead (mitigated by automation)
**Reference**: data-model.md, Entity 2 (Task Event)

---

### Entry 6: Liveness vs Readiness Probe Split for Dapr Unavailability
**Date**: 2026-01-22
**Decision**: Services always pass liveness probe; readiness probe fails if Dapr unavailable
**Rationale**: Prevents restart loops if Dapr sidecar delayed; allows graceful degradation
**Constitutional Principle**: Principle VIII (Resilience - services start without Dapr)
**Reference**: research.md, Q7; quickstart.md, Step 8

---

### Entry 7: Local-First Validation Enforced
**Date**: 2026-01-22
**Decision**: Minikube validation MUST succeed before cloud deployment
**Rationale**: Constitutional Principle VI (Local-First Validation); reduces cloud costs, faster feedback
**Validation Steps**: Infrastructure setup, service deployment, Phase IV regression, Phase V features, performance, rollback
**Duration**: ~32 minutes (acceptable for thorough validation)
**Reference**: quickstart.md, Kubernetes Deployment Flow

---

**Future entries will be appended below this line**

---

## Next Steps

1. **Human Approval Required**: Review this plan for approval before proceeding
2. **After Approval**: Run `/sp.tasks` to generate task breakdown for implementation
3. **Implementation**: Follow tasks.md in priority order (Setup → Foundational → US1 → US2 → US3 → US4)
4. **Local Validation**: Execute quickstart.md validation before cloud deployment
5. **Cloud Deployment**: Only after local success confirmed

**Remember**: Constitution → Specification → Plan → **Tasks** → Implementation (workflow law)

**STOP** - Awaiting human approval to proceed to `/sp.tasks`.

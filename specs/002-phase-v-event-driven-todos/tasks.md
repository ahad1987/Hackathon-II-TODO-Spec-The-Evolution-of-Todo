# Tasks: Phase V - Event-Driven Task Management

**Input**: Design documents from `/specs/002-phase-v-event-driven-todos/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in specification - focusing on implementation tasks only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend services**: `backend/src/` for Chat API, `backend/services/` for new services
- **Kubernetes manifests**: `k8s/services/`, `k8s/infrastructure/`, `k8s/dapr/`
- **Tests**: `backend/tests/phase5/`
- Paths assume existing Phase IV project structure extended with Phase V additions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for Phase V

- [x] T001 Create Phase V service directory structure in backend/services/ (notification/, reminder/, audit_logger/, recurring_processor/)
- [x] T002 [P] Add Dapr SDK to backend requirements.txt (dapr>=1.11.0, dapr-ext-fastapi>=1.11.0)
- [x] T003 [P] Add APScheduler to backend requirements.txt for Reminder Service (apscheduler>=3.10.0)
- [x] T004 [P] Create Kubernetes manifest directories (k8s/dapr/, k8s/services/phase-v/)
- [x] T005 Create Phase V test directory structure (backend/tests/phase5/ with subdirectories for each user story)

**Verification**: All directories exist, requirements.txt updated
**Rollback**: Remove created directories, revert requirements.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Migration (Additive-Only, Backward Compatible)

- [x] T006 Create Phase V database migration script in backend/scripts/migrations/phase_v_migration.sql
- [x] T007 Add Phase V columns to tasks table (due_date, recurrence_pattern, recurrence_end_date, parent_recurring_task_id, occurrence_date, reminder_offset, reminder_status - ALL NULLABLE)
- [x] T008 [P] Create task_events table with monthly partitioning (event_id, event_type, task_id, user_id, timestamp, payload, correlation_id, partition_key)
- [x] T009 [P] Create reminder_schedule table (reminder_id, task_id, user_id, trigger_at, reminder_type, status, created_at, updated_at)
- [x] T010 Add database constraints for Phase V (chk_recurrence_requires_due_date, chk_reminder_requires_due_date, uniq_recurring_instance)
- [x] T011 Create database indexes for Phase V queries (idx_tasks_due_date, idx_tasks_recurrence, idx_tasks_parent_recurring, idx_tasks_reminder_status, idx_task_events_task_id, idx_reminders_trigger)
- [x] T012 Create rollback migration script in backend/scripts/migrations/phase_v_rollback.sql (drops Phase V columns and tables)

**Verification**: Run migration against local PostgreSQL, verify Phase IV tasks unchanged, verify new tables/columns created
**Rollback**: Run rollback migration, verify Phase IV intact

### Dapr Integration (Chat API Foundation)

- [x] T013 Create Dapr publisher module in backend/src/dapr/publisher.py (DaprEventPublisher class with publish_event method)
- [x] T014 [P] Create Dapr health check module in backend/src/dapr/health.py (check_dapr_connectivity function)
- [x] T015 Extend backend/src/config.py with Dapr configuration (DAPR_HTTP_PORT, DAPR_GRPC_PORT, PUBSUB_NAME)
- [x] T016 Initialize Dapr client in backend/src/main.py (startup event, graceful shutdown handling)

**Verification**: Chat API starts successfully with/without Dapr sidecar, Dapr connectivity check works
**Rollback**: Remove dapr/ directory, revert config.py and main.py changes

### Health Endpoints (All Services)

- [x] T017 Create shared health endpoint module in backend/src/common/health.py (liveness and readiness probe implementations)
- [x] T018 Add /health/live endpoint to Chat API in backend/src/api/health.py (always returns 200 if process alive)
- [x] T019 Add /health/ready endpoint to Chat API in backend/src/api/health.py (checks database and Dapr connectivity)

**Verification**: Liveness always returns 200, readiness returns 200 when dependencies healthy, 503 when not
**Rollback**: Remove health endpoints, revert health.py

### Kubernetes Infrastructure

- [x] T020 Create Kafka deployment manifest in k8s/infrastructure/kafka-deployment.yaml (Kafka + Zookeeper, 1 replica for local)
- [x] T021 [P] Create Dapr Pub/Sub component manifest in k8s/dapr/pubsub.yaml (taskflow-pubsub, type: pubsub.kafka, Kafka brokers configuration)
- [x] T022 [P] Update Chat API deployment manifest in k8s/services/chat-api-deployment.yaml (add Dapr annotations: enabled, app-id, app-port)

**Verification**: Kafka pods running, Dapr component registered, Chat API has Dapr sidecar
**Rollback**: Delete Kafka deployment, remove Dapr component, remove Dapr annotations from Chat API

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Recurring Task Automation (Priority: P1) 🎯 MVP

**Goal**: Users can create tasks with recurrence patterns (daily, weekly, monthly), and the system automatically generates task instances

**Independent Test**: Create a recurring task with "daily:" pattern, verify first instance created immediately, verify new instance appears next day

### Implementation for User Story 1

- [x] T023 [P] [US1] Extend Task model in backend/src/models/task.py (add recurrence_pattern, recurrence_end_date, parent_recurring_task_id, occurrence_date fields with Pydantic validation)
- [x] T024 [P] [US1] Create recurrence pattern parser in backend/src/utils/recurrence.py (parse_recurrence_pattern function, validate_pattern function)
- [x] T025 [US1] Extend TaskService in backend/src/services/task_service.py (handle recurrence_pattern on create, set parent_recurring_task_id for instances)
- [x] T026 [US1] Extend POST /api/v1/tasks endpoint in backend/src/api/tasks.py (accept recurrence_pattern and recurrence_end_date in request body)
- [x] T027 [US1] Add task.created event publishing in backend/src/services/task_service.py (call DaprEventPublisher.publish_event after task creation)
- [x] T028 [US1] Add task.updated event publishing in backend/src/services/task_service.py (publish on task update with changes payload)
- [x] T029 [US1] Add task.deleted event publishing in backend/src/services/task_service.py (publish on task deletion)
- [x] T030 [US1] Create Recurring Task Processor service entrypoint in backend/services/recurring_processor/main.py (FastAPI app with health endpoints)
- [x] T031 [P] [US1] Create scheduler module in backend/services/recurring_processor/scheduler.py (APScheduler cron job, runs every 5 minutes)
- [x] T032 [P] [US1] Create task generator module in backend/services/recurring_processor/task_generator.py (find_due_recurring_tasks, create_task_instance via Chat API)
- [x] T033 [US1] Create Recurring Task Processor Dockerfile in backend/services/recurring_processor/Dockerfile
- [x] T034 [US1] Create Recurring Task Processor Kubernetes manifest in k8s/services/phase-v/recurring-processor-deployment.yaml (with Dapr annotations for service invocation)

**Verification**:
- Create recurring task via Chat API, verify task.created event in Kafka, verify first instance created
- Wait 5 minutes (or trigger scheduler manually), verify new instance created next day
- Query database, verify parent_recurring_task_id and occurrence_date set correctly

**Rollback**: Scale Recurring Task Processor to 0 replicas, existing tasks unchanged, no new instances generated

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Due Date Reminders (Priority: P1)

**Goal**: Users can set due dates with reminder offsets, and the system triggers reminder notifications at the configured time

**Independent Test**: Create task with due_date and reminder_offset "1 hour", advance system time, verify reminder triggered

### Implementation for User Story 2

- [x] T035 [P] [US2] Extend Task model in backend/src/models/task.py (add due_date, reminder_offset, reminder_status fields)
- [x] T036 [US2] Extend POST /api/v1/tasks endpoint in backend/src/api/tasks.py (accept due_date and reminder_offset in request body)
- [x] T037 [US2] Add due_date validation in backend/src/services/task_service.py (parse reminder_offset, validate future dates)
- [x] T038 [US2] Create Reminder Service entrypoint in backend/services/reminder/main.py (FastAPI app with health endpoints and Dapr subscription routes)
- [x] T039 [P] [US2] Create priority queue module in backend/services/reminder/priority_queue.py (ReminderPriorityQueue class using heapq, add/remove/peek operations)
- [x] T040 [P] [US2] Create event consumer module in backend/services/reminder/event_consumer.py (subscribe to task.created, task.updated, task.deleted, task.completed events)
- [x] T041 [US2] Implement event handlers in event_consumer.py (on_task_created: calculate trigger time, add to queue; on_task_updated: reschedule; on_task_deleted/completed: cancel)
- [x] T042 [P] [US2] Create reminder scheduler module in backend/services/reminder/scheduler.py (background task checks queue every 10 seconds, triggers due reminders)
- [x] T043 [US2] Add task.reminder.triggered event publishing in backend/services/reminder/scheduler.py (publish when reminder fires)
- [x] T044 [P] [US2] Implement reminder snapshot persistence in backend/services/reminder/priority_queue.py (save to reminder_schedule table every 5 minutes, load on startup)
- [x] T045 [US2] Create Reminder Service Dockerfile in backend/services/reminder/Dockerfile
- [x] T046 [US2] Create Reminder Service Kubernetes manifest in k8s/services/phase-v/reminder-service-deployment.yaml (with Dapr annotations and pubsub subscriptions)
- [x] T047 [US2] Create Dapr subscription manifest for Reminder Service in k8s/dapr/reminder-subscriptions.yaml (subscribe to taskflow.tasks.created, updated, deleted, completed)

**Verification**:
- Create task with due_date and reminder_offset via Chat API
- Verify Reminder Service receives task.created event and schedules reminder
- Query reminder_schedule table, verify reminder entry exists with correct trigger_at
- Advance time (or wait), verify task.reminder.triggered event published

**Rollback**: Scale Reminder Service to 0 replicas, existing tasks unchanged, reminders not triggered

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Real-Time Notifications (Priority: P2)

**Goal**: Users receive real-time notifications for task events via Server-Sent Events (SSE) within 2 seconds

**Independent Test**: Open SSE connection, create task, verify notification received within 2 seconds

### Implementation for User Story 3

- [x] T048 [US3] Create Notification Service entrypoint in backend/services/notification/main.py (FastAPI app with health endpoints, SSE endpoint, Dapr subscription routes)
- [x] T049 [P] [US3] Create SSE handler module in backend/services/notification/sse_handler.py (NotificationManager class, manage connections per user_id, send_notification method)
- [x] T050 [P] [US3] Create event consumer module in backend/services/notification/event_consumer.py (subscribe to all task events + reminder.triggered events)
- [x] T051 [US3] Implement event handlers in event_consumer.py (on_task_created/updated/completed/deleted: lookup user connections, send SSE; on_reminder_triggered: send SSE)
- [x] T052 [US3] Add GET /api/v1/notifications/stream endpoint in notification/main.py (SSE endpoint with JWT authentication, register connection)
- [x] T053 [P] [US3] Implement rate limiting in sse_handler.py (max 10 notifications/second per connection, max 3 concurrent connections per user)
- [x] T054 [P] [US3] Implement heartbeat mechanism in sse_handler.py (send heartbeat every 30 seconds, close stale connections)
- [x] T055 [US3] Create Notification Service Dockerfile in backend/services/notification/Dockerfile
- [x] T056 [US3] Create Notification Service Kubernetes manifest in k8s/services/phase-v/notification-service-deployment.yaml (with Dapr annotations and pubsub subscriptions)
- [x] T057 [US3] Create Dapr subscription manifest for Notification Service in k8s/dapr/notification-subscriptions.yaml (subscribe to all task topics + reminder-triggered)

**Verification**:
- Open SSE connection via curl or browser EventSource
- Create task via Chat API
- Verify notification received within 2 seconds with correct payload
- Verify heartbeat messages received every 30 seconds

**Rollback**: Scale Notification Service to 0 replicas, existing functionality unchanged, no real-time notifications

**Checkpoint**: All P1 and P2 user stories should now be independently functional

---

## Phase 6: User Story 4 - Comprehensive Audit Logging (Priority: P3)

**Goal**: All task operations are logged immutably to task_events table for compliance and debugging

**Independent Test**: Create/update/delete tasks, query task_events table, verify all operations recorded with complete payloads

### Implementation for User Story 4

- [ ] T058 [US4] Create Audit Logger Service entrypoint in backend/services/audit_logger/main.py (FastAPI app with health endpoints, Dapr subscription routes)
- [ ] T059 [P] [US4] Create event consumer module in backend/services/audit_logger/event_consumer.py (subscribe to all task events: created, updated, completed, deleted)
- [ ] T060 [P] [US4] Create storage module in backend/services/audit_logger/storage.py (AuditLogStorage class, write_event method using asyncpg, batch writes)
- [ ] T061 [US4] Implement event handlers in event_consumer.py (on_task_event: persist to task_events table with partition_key, handle duplicates via event_id check)
- [ ] T062 [P] [US4] Implement batch write optimization in storage.py (buffer 100 events, flush every 1 second or on buffer full)
- [ ] T063 [P] [US4] Add query endpoint GET /api/v1/audit/tasks/{task_id} in audit_logger/main.py (return chronological event history for task)
- [ ] T064 [US4] Create Audit Logger Dockerfile in backend/services/audit_logger/Dockerfile
- [ ] T065 [US4] Create Audit Logger Kubernetes manifest in k8s/services/phase-v/audit-logger-deployment.yaml (with Dapr annotations and pubsub subscriptions)
- [ ] T066 [US4] Create Dapr subscription manifest for Audit Logger in k8s/dapr/audit-subscriptions.yaml (subscribe to all task event topics)

**Verification**:
- Create, update, complete, delete tasks via Chat API
- Query task_events table, verify entries for each operation
- Verify JSONB payload contains complete event data
- Query audit endpoint, verify chronological history returned

**Rollback**: Scale Audit Logger to 0 replicas, existing functionality unchanged, audit logs stop accumulating

**Checkpoint**: All user stories (P1, P2, P3) should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T067 [P] Add Dockerfile for Chat API in backend/Dockerfile (if not already exists from Phase IV)
- [ ] T068 [P] Create Docker Compose file for local development in docker-compose.yml (PostgreSQL, Kafka, all 5 services with Dapr sidecars)
- [ ] T069 [P] Update main README.md with Phase V overview and quickstart reference
- [ ] T070 [P] Create Phase V smoke test script in backend/scripts/test_phase_v.sh (tests all 4 user stories)
- [ ] T071 [P] Add Prometheus metrics endpoints to all services (using prometheus_client library)
- [ ] T072 [P] Create Grafana dashboard JSON for Phase V services in k8s/monitoring/phase-v-dashboard.json
- [ ] T073 [P] Add structured logging to all Phase V services (using structlog, JSON format)
- [ ] T074 [P] Create Phase IV regression test suite in backend/tests/phase4_regression/ (verify Phase IV unchanged)
- [ ] T075 Run quickstart.md validation (full 6-phase local deployment and testing)

**Verification**: Docker Compose works, smoke tests pass, metrics exposed, logging structured, Phase IV regression tests pass
**Rollback**: Revert polish changes, core functionality unchanged

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed) after Foundational complete
  - Or sequentially in priority order (P1 → P1 → P2 → P3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Recurring Tasks)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1 - Reminders)**: Can start after Foundational (Phase 2) - No dependencies on other stories (US1 publishes events it needs)
- **User Story 3 (P2 - Notifications)**: Can start after Foundational (Phase 2) - Depends on event publishing from US1/US2 but independently testable
- **User Story 4 (P3 - Audit Logging)**: Can start after Foundational (Phase 2) - Depends on event publishing from US1 but independently testable

### Critical Path

**Longest dependency chain (blocking tasks only)**:
1. Setup (Phase 1): T001-T005 (~30 min)
2. Foundational (Phase 2): T006-T022 (~2 hours)
3. User Story 1 (Phase 3): T023-T034 (~4 hours) - Most complex story
4. User Story 2 (Phase 4): T035-T047 (~3 hours)
5. User Story 3 (Phase 5): T048-T057 (~2 hours)
6. User Story 4 (Phase 6): T058-T066 (~1.5 hours)
7. Polish (Phase 7): T067-T075 (~2 hours)

**Total Critical Path Time**: ~14.5 hours (single developer, sequential)

### Parallel Opportunities

- **Setup Phase**: T002, T003, T004 can run in parallel
- **Foundational Phase**: T008, T009, T014, T021, T022 can run in parallel after database migration
- **Within Each User Story**:
  - Models and utilities marked [P] can be developed in parallel
  - Dockerfiles and K8s manifests marked [P] can be created in parallel
- **Across User Stories** (after Foundational complete):
  - All 4 user stories can be worked on in parallel by different developers
  - Recommended order if sequential: US1 → US2 → US3 → US4 (by priority)

---

## Parallel Example: User Story 1 (Recurring Tasks)

```bash
# Launch all [P] tasks for US1 together:
# T023 - Extend Task model
# T024 - Create recurrence parser
# T031 - Create scheduler module
# T032 - Create task generator module

# Once those complete, proceed with dependent tasks:
# T025 - Extend TaskService (needs T023, T024)
# T026 - Extend API endpoint (needs T025)
# ... continue sequentially
```

---

## Parallel Example: After Foundational Complete

```bash
# With 4 developers, launch all user stories in parallel:
# Developer A: User Story 1 (T023-T034)
# Developer B: User Story 2 (T035-T047)
# Developer C: User Story 3 (T048-T057)
# Developer D: User Story 4 (T058-T066)

# Each story completes independently and can be tested/deployed separately
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T022) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T023-T034)
4. **STOP and VALIDATE**: Test recurring tasks independently
5. Complete Phase 4: User Story 2 (T035-T047)
6. **STOP and VALIDATE**: Test reminders independently
7. Deploy MVP (both P1 stories functional)

**Rationale**: Both P1 stories provide immediate user value. US1 (recurring tasks) is the headline feature, US2 (reminders) makes task management effective. Together they form a complete MVP.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (~2.5 hours)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP feature!) (~4 hours)
3. Add User Story 2 → Test independently → Deploy/Demo (MVP complete!) (~3 hours)
4. Add User Story 3 → Test independently → Deploy/Demo (~2 hours)
5. Add User Story 4 → Test independently → Deploy/Demo (~1.5 hours)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With 4+ developers:

1. Team completes Setup + Foundational together (~2.5 hours)
2. Once Foundational done:
   - Developer A: User Story 1 (Recurring Tasks) - 4 hours
   - Developer B: User Story 2 (Reminders) - 3 hours
   - Developer C: User Story 3 (Notifications) - 2 hours
   - Developer D: User Story 4 (Audit Logging) - 1.5 hours
3. Stories complete and integrate independently
4. Team converges for Polish phase (~2 hours)

**Total Time (Parallel)**: ~8.5 hours (vs ~14.5 hours sequential)

---

## Task Execution Guidelines

### Before Starting Each Task

1. **Read task description carefully** - note file path and expected output
2. **Check dependencies** - ensure prerequisite tasks completed
3. **Verify rollback strategy** - understand how to undo if needed

### While Executing Each Task

1. **One responsibility** - complete only what task describes, no extra features
2. **Test as you go** - verify task output before marking complete
3. **Commit frequently** - commit after each task or logical group

### After Completing Each Task

1. **Mark checkbox** - update tasks.md with `- [x]` for completed task
2. **Verify output** - run verification steps from task description
3. **Document issues** - if task reveals new requirements, create new task (append to appropriate phase)

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Phase IV Regression**: Run Phase IV tests after Foundational phase and after Phase 7 (Polish) to ensure no breaking changes
- **Constitutional Compliance**: All tasks follow additive-only principle, no Phase IV modifications except extending with nullable fields

---

## Success Criteria Per User Story

### User Story 1 Success
- ✅ Create recurring task with "daily:" pattern via API
- ✅ First task instance created immediately
- ✅ Recurring Task Processor generates new instance next day
- ✅ task.created events published for each instance
- ✅ Database shows parent_recurring_task_id and occurrence_date set correctly

### User Story 2 Success
- ✅ Create task with due_date and reminder_offset via API
- ✅ Reminder Service schedules reminder in priority queue
- ✅ reminder_schedule table has pending reminder entry
- ✅ Reminder fires at correct time, publishes task.reminder.triggered event
- ✅ Reminder cancelled when task completed/deleted

### User Story 3 Success
- ✅ Open SSE connection with GET /api/v1/notifications/stream
- ✅ Create task via API, receive notification within 2 seconds
- ✅ Heartbeat messages received every 30 seconds
- ✅ Rate limiting prevents spam (max 10/sec)
- ✅ Connection closed gracefully on disconnect

### User Story 4 Success
- ✅ Create/update/complete/delete tasks via API
- ✅ task_events table has entries for each operation
- ✅ JSONB payload contains complete event data
- ✅ Query audit endpoint returns chronological history
- ✅ Monthly partitions created automatically

---

## Rollback Plan

### Per-Story Rollback

Each user story can be rolled back independently:

1. **US1 Rollback**: Scale recurring-processor to 0, remove Dapr subscriptions
2. **US2 Rollback**: Scale reminder-service to 0, clear reminder_schedule table
3. **US3 Rollback**: Scale notification-service to 0, close SSE connections
4. **US4 Rollback**: Scale audit-logger to 0, task_events table remains but no new entries

**Data Loss**: None - Phase IV data unchanged, Phase V columns nullable and ignored

### Full Phase V Rollback

If critical failure requires full rollback to Phase IV:

1. Delete all Phase V service deployments (T020-T022, T034, T046, T056, T065)
2. Remove Dapr annotations from Chat API (revert T022)
3. Remove Dapr event publishing from Chat API (revert T027-T029)
4. Run Phase IV regression tests
5. Optionally: Drop Phase V database columns (run rollback migration T012)

**Time**: <5 minutes
**Data Loss**: Zero (Phase IV fully functional)

---

## Next Steps After Tasks Complete

1. **Human approval required** before starting implementation
2. Begin with Phase 1 (Setup) tasks T001-T005
3. Complete Phase 2 (Foundational) fully before user stories
4. Implement user stories in priority order or in parallel (team decision)
5. After each story complete, run independent tests and validate
6. Run full quickstart.md validation before considering Phase V complete
7. Only deploy to cloud after local (Minikube) success

**Remember**: Constitution → Specification → Plan → Tasks → **Implementation**

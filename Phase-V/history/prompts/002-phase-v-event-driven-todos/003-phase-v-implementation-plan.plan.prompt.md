---
id: 003
title: Phase V Event-Driven Implementation Plan
stage: plan
date: 2026-01-22
surface: agent
model: claude-sonnet-4-5
feature: 002-phase-v-event-driven-todos
branch: 002-phase-v-event-driven-todos
user: TaskFlow Deploy
command: /sp.plan
labels: ["phase-v", "architecture", "dapr", "kafka", "kubernetes", "microservices", "event-driven", "implementation-plan"]
links:
  spec: ../specs/002-phase-v-event-driven-todos/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - ../specs/002-phase-v-event-driven-todos/plan.md
 - ../specs/002-phase-v-event-driven-todos/research.md
 - ../specs/002-phase-v-event-driven-todos/data-model.md
 - ../specs/002-phase-v-event-driven-todos/contracts/events-schema.yaml
 - ../specs/002-phase-v-event-driven-todos/quickstart.md
tests:
 - None (planning phase)
---

## Prompt

Using the approved specification, generate the **Phase V Implementation Plan**.

---

## PLAN MUST INCLUDE

1. High-level overview
2. Architecture flow
3. Service interactions
4. Dapr components
5. Kafka topics
6. Kubernetes deployment flow
7. Local (Minikube) execution phases
8. Cloud execution phases
9. Risk controls and safeguards
10. Rollback strategies

---

## COMPONENT CLASSIFICATION

Clearly mark:

* NEW components
* REUSED components
* UNCHANGED components

---

## 📜 HISTORY & DECISION LOG (APPEND-ONLY)

Include a section titled exactly:

**📜 History & Decision Log (Append-Only)**

Rules:

* Start with **Entry 0: Plan Created**
* NEVER delete or edit previous entries
* ONLY append
* Log every major decision, assumption, or fix

---

## FORMAT RULES

* Step-by-step
* NO code
* NO task breakdown yet

Write `/specs/phase-v/plan.md`
STOP after writing.

## Response snapshot

**Phase V Implementation Plan Complete**

### Artifacts Generated

**Plan File**: `../specs/002-phase-v-event-driven-todos/plan.md`
**Supporting Documents**:
- `research.md` (Phase 0: Technology decisions, 7 research questions resolved)
- `data-model.md` (Phase 1: Entity definitions, migration strategy)
- `contracts/events-schema.yaml` (Phase 1: Event schemas for Dapr Pub/Sub)
- `quickstart.md` (Phase 1: Local deployment and validation guide)

### Architecture Summary

**Services** (1 extended, 4 new):
1. **Chat API** (EXTENDED from Phase IV) - ONLY producer of task events
2. **Notification Service** (NEW) - Real-time SSE notifications
3. **Reminder Service** (NEW) - Due date reminder scheduling
4. **Audit Logger** (NEW) - Immutable audit trail
5. **Recurring Task Processor** (NEW) - Task instance generation

**Event Flow**:
- Chat API publishes: `task.created`, `task.updated`, `task.completed`, `task.deleted`
- Reminder Service publishes: `task.reminder.triggered`
- All communication via Dapr Pub/Sub (NO direct Kafka)

**Infrastructure**:
- Dapr v1.11+ for Pub/Sub abstraction
- Kafka 3.x as event backend
- PostgreSQL 14+ (Phase IV database extended)
- Kubernetes 1.25+ (Minikube local, GKE/EKS/AKS cloud)

### Constitution Compliance

**All Constitution Checks PASS**:
- ✅ Phase IV Immutability (nullable columns, smoke tests included)
- ✅ Additive-Only Changes (no schema modifications)
- ✅ Event-Driven Architecture (all async via events)
- ✅ Dapr Abstraction Layer (zero direct Kafka usage)
- ✅ Kubernetes Runtime (containerized, health endpoints)
- ✅ Local-First Validation (Minikube deployment documented)
- ✅ Human-in-the-Loop (plan requires approval)

### Key Architectural Decisions

1. **SSE over WebSockets** for notifications (simpler, browser-native)
2. **Recurring Processor invokes Chat API** (maintains single event producer)
3. **Nullable columns for Phase V fields** (backward compatibility)
4. **At-least-once delivery with idempotency** (event_id deduplication)
5. **Monthly partitioning for audit logs** (efficient retention)
6. **Liveness/Readiness probe split** (graceful Dapr degradation)
7. **Local-first validation enforced** (~32 min Minikube workflow)

### Deployment Phases

**Local (Minikube)**:
1. Infrastructure Setup (~10 min)
2. Service Deployment (~5 min)
3. Phase IV Regression Validation (~2 min)
4. Phase V Feature Validation (~5 min)
5. Performance & Resilience Testing (~5 min)
6. Rollback Validation (~5 min)
**Total**: ~32 minutes

**Cloud**:
1. Cluster Provisioning (~30 min)
2. Configuration & Secrets (~10 min)
3. Blue-Green Deployment (~15 min)
4. Monitoring Setup (~20 min)
5. Production Validation (ongoing)
**Total**: ~75 minutes initial

### Risk Controls

**6 Risk Scenarios Addressed**:
1. Dapr sidecar unavailability → Separate probes, graceful degradation
2. Kafka broker failure → Replication, retries, DLQ
3. Duplicate task instances → DB constraints, idempotency keys
4. Notification delivery failure → Best-effort, rate limiting
5. Reminder missed (restart) → Snapshot persistence, catch-up
6. Phase IV regression → Automated tests, immediate rollback

### Rollback Strategy

**3 Rollback Scenarios Documented**:
1. **Single service failure** → Scale to 0, isolate, fix, redeploy (<2 min)
2. **Chat API event bug** → Remove Dapr annotations, Phase IV mode (<5 min)
3. **Full Phase V rollback** → Delete services, disable Dapr on Chat API (<5 min, zero data loss)

### History & Decision Log

**7 Entries Logged**:
- Entry 0: Plan created
- Entry 1: SSE chosen for notifications
- Entry 2: Recurring processor invokes Chat API
- Entry 3: Nullable columns for Phase V
- Entry 4: At-least-once delivery with idempotency
- Entry 5: Monthly partitioning for audit logs
- Entry 6: Liveness/readiness probe split
- Entry 7: Local-first validation enforced

## Outcome

- ✅ Impact: Comprehensive Phase V implementation plan with architecture flow, service interactions, Dapr/Kafka configuration, Kubernetes deployment phases (local + cloud), 6 risk controls, 3 rollback strategies, and 7 architectural decisions logged
- 🧪 Tests: Planning artifacts include test validation steps (Phase IV regression, Phase V features, performance, rollback)
- 📁 Files: 5 files created (plan.md, research.md, data-model.md, events-schema.yaml, quickstart.md)
- 🔁 Next prompts: /sp.tasks (to generate task breakdown following plan), then implementation after human approval
- 🧠 Reflection: Plan successfully balances constitutional constraints (Phase IV immutability, Dapr-only Kafka, local-first) with Phase V requirements (4 user stories, event-driven architecture, 5 services). All constitution checks PASS. Ready for task generation.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Constitution Check validation PASS (all 11 principles/requirements verified)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Proceed to /sp.tasks to break down implementation into testable, dependency-ordered tasks

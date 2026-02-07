# Quickstart: Phase V - Event-Driven Task Management

**Feature**: Phase V - Event-Driven Task Management
**Branch**: `002-phase-v-event-driven-todos`
**Date**: 2026-01-22

## Overview

This quickstart guide provides step-by-step instructions to deploy and validate Phase V locally using Minikube, following the constitutional requirement for local-first validation.

---

## Prerequisites

### Required Tools
- **Minikube** v1.28+ (local Kubernetes cluster)
- **kubectl** v1.25+ (Kubernetes CLI)
- **Dapr CLI** v1.11+ (Dapr runtime management)
- **Docker** v20.10+ (container runtime)
- **Python** 3.11+ (for backend services)
- **PostgreSQL** 14+ client tools (psql)

### Verification Commands
```bash
minikube version
kubectl version --client
dapr version
docker --version
python --version
psql --version
```

---

## Step 1: Start Minikube with Dapr

### Start Minikube Cluster
```bash
# Start Minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --disk-size=20gb

# Enable Minikube addons
minikube addons enable ingress
minikube addons enable metrics-server

# Verify cluster is running
kubectl get nodes
```

### Initialize Dapr on Kubernetes
```bash
# Initialize Dapr control plane
dapr init --kubernetes --wait

# Verify Dapr installation
kubectl get pods -n dapr-system

# Expected output:
# - dapr-operator
# - dapr-sidecar-injector
# - dapr-sentry
# - dapr-placement-server
```

---

## Step 2: Deploy Infrastructure (Kafka + PostgreSQL)

### Deploy PostgreSQL (Phase IV Database)
```bash
# Apply PostgreSQL deployment manifest
kubectl apply -f k8s/infrastructure/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Verify PostgreSQL is running
kubectl get pods -l app=postgres
```

### Deploy Kafka (Event Backend for Dapr)
```bash
# Apply Kafka deployment manifest (includes Zookeeper)
kubectl apply -f k8s/infrastructure/kafka-deployment.yaml

# Wait for Kafka to be ready
kubectl wait --for=condition=ready pod -l app=kafka --timeout=300s

# Verify Kafka is running
kubectl get pods -l app=kafka
```

### Configure Dapr Pub/Sub Component
```bash
# Apply Dapr Pub/Sub component manifest (Kafka backend)
kubectl apply -f k8s/dapr/pubsub.yaml

# Verify component is registered
kubectl get components -n default
```

---

## Step 3: Database Migration (Phase V Schema)

### Run Migration Script
```bash
# Port-forward PostgreSQL for local access
kubectl port-forward svc/postgres 5432:5432 &

# Run Phase V migration
python scripts/migrate.py --env local --phase v

# Verify migration succeeded
psql -h localhost -U taskflow_user -d taskflow_db -c "\d tasks"

# Expected: Phase V columns added (due_date, recurrence_pattern, etc.)
```

### Verify Phase IV Data Intact
```bash
# Query existing Phase IV tasks (should still work)
psql -h localhost -U taskflow_user -d taskflow_db -c "SELECT id, title, status FROM tasks WHERE due_date IS NULL LIMIT 5;"

# Expected: Existing tasks unchanged, due_date NULL
```

---

## Step 4: Deploy Phase V Services

### Deploy Services in Order

**Note**: Services must be deployed with Dapr annotations to enable sidecar injection.

#### 1. Chat API (existing Phase IV, extended)
```bash
# Apply Chat API deployment with Dapr annotations
kubectl apply -f k8s/services/chat-api-deployment.yaml

# Wait for Chat API to be ready
kubectl wait --for=condition=ready pod -l app=chat-api --timeout=300s

# Verify Dapr sidecar injected
kubectl get pods -l app=chat-api -o jsonpath='{.items[0].spec.containers[*].name}'
# Expected output: chat-api, daprd
```

#### 2. Notification Service (NEW)
```bash
# Apply Notification Service deployment
kubectl apply -f k8s/services/notification-service-deployment.yaml

# Wait for service to be ready
kubectl wait --for=condition=ready pod -l app=notification-service --timeout=300s
```

#### 3. Reminder Service (NEW)
```bash
# Apply Reminder Service deployment
kubectl apply -f k8s/services/reminder-service-deployment.yaml

# Wait for service to be ready
kubectl wait --for=condition=ready pod -l app=reminder-service --timeout=300s
```

#### 4. Audit Logger (NEW)
```bash
# Apply Audit Logger deployment
kubectl apply -f k8s/services/audit-logger-deployment.yaml

# Wait for service to be ready
kubectl wait --for=condition=ready pod -l app=audit-logger --timeout=300s
```

#### 5. Recurring Task Processor (NEW)
```bash
# Apply Recurring Task Processor deployment
kubectl apply -f k8s/services/recurring-task-processor-deployment.yaml

# Wait for service to be ready
kubectl wait --for=condition=ready pod -l app=recurring-task-processor --timeout=300s
```

### Verify All Services Running
```bash
kubectl get pods -l phase=v

# Expected output: All Phase V pods in Running state with 2/2 containers (app + daprd)
```

---

## Step 5: Phase IV Regression Testing

**CRITICAL**: Verify Phase IV functionality still works before testing Phase V features.

### Run Phase IV Smoke Tests
```bash
# Port-forward Chat API
kubectl port-forward svc/chat-api 8000:8000 &

# Run Phase IV test suite
pytest tests/phase4/ -v

# Expected: All Phase IV tests PASS
```

### Manual Phase IV Validation
```bash
# Create Phase IV task (no Phase V fields)
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Phase IV test task", "description": "Verify Phase IV still works"}'

# Expected: Task created successfully, ID returned

# List tasks
curl -X GET http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $JWT_TOKEN"

# Expected: Task appears in list, no errors
```

---

## Step 6: Phase V Feature Validation

### Test 1: Recurring Task Creation (P1)
```bash
# Create daily recurring task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Daily standup",
    "description": "Team standup meeting",
    "recurrence_pattern": "daily:",
    "due_date": "2026-01-23T09:00:00Z"
  }'

# Expected: Task created with first instance

# Verify task event published
kubectl logs -l app=notification-service --tail=20 | grep "task.created"
# Expected: Event received by Notification Service

# Check database for recurring task
psql -h localhost -U taskflow_user -d taskflow_db -c \
  "SELECT id, title, recurrence_pattern, due_date FROM tasks WHERE recurrence_pattern IS NOT NULL;"
```

### Test 2: Due Date Reminder (P1)
```bash
# Create task with reminder
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Submit report",
    "due_date": "2026-01-23T17:00:00Z",
    "reminder_offset": "1 day"
  }'

# Expected: Task created, reminder scheduled

# Verify reminder scheduled
kubectl logs -l app=reminder-service --tail=20 | grep "Scheduled reminder"
# Expected: Log entry confirming reminder scheduled

# Check reminder_schedule table
psql -h localhost -U taskflow_user -d taskflow_db -c \
  "SELECT task_id, trigger_at, status FROM reminder_schedule WHERE status = 'pending';"
```

### Test 3: Real-Time Notifications (P2)
```bash
# Open SSE connection (in separate terminal)
curl -N -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/notifications/stream

# Create task (in original terminal)
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test notification"}'

# Expected: SSE terminal receives notification within 2 seconds
```

### Test 4: Audit Logging (P3)
```bash
# Create and update a task
TASK_ID=$(curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Audit test"}' | jq -r '.id')

curl -X PATCH http://localhost:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Audit test UPDATED"}'

# Query audit logs
psql -h localhost -U taskflow_user -d taskflow_db -c \
  "SELECT event_type, timestamp, payload FROM task_events WHERE task_id = '$TASK_ID' ORDER BY timestamp;"

# Expected: task.created and task.updated events recorded
```

---

## Step 7: Event Flow Verification

### Verify Dapr Pub/Sub Topics
```bash
# List Dapr topics
dapr list -k | grep taskflow

# Expected topics:
# - taskflow.tasks.created
# - taskflow.tasks.updated
# - taskflow.tasks.completed
# - taskflow.tasks.deleted
# - taskflow.tasks.reminder-triggered
```

### Verify Event Consumers
```bash
# Check Notification Service subscriptions
kubectl logs -l app=notification-service --tail=50 | grep "Subscribed to topic"

# Expected output showing subscriptions:
# - taskflow.tasks.created
# - taskflow.tasks.updated
# - taskflow.tasks.completed
# - taskflow.tasks.deleted
# - taskflow.tasks.reminder-triggered
```

---

## Step 8: Health Check Validation

### Verify Liveness Endpoints
```bash
# Check all services' liveness
for svc in chat-api notification-service reminder-service audit-logger recurring-task-processor; do
  echo "Checking $svc liveness..."
  kubectl exec -it $(kubectl get pod -l app=$svc -o name | head -1) -- curl -s http://localhost:8080/health/live || echo "FAIL"
done

# Expected: All services return 200 OK
```

### Verify Readiness Endpoints
```bash
# Check all services' readiness
for svc in chat-api notification-service reminder-service audit-logger recurring-task-processor; do
  echo "Checking $svc readiness..."
  kubectl exec -it $(kubectl get pod -l app=$svc -o name | head -1) -- curl -s http://localhost:8080/health/ready || echo "FAIL"
done

# Expected: All services return 200 OK
```

### Test Dapr Unavailability Graceful Degradation
```bash
# Scale down Dapr sidecar injector (simulates Dapr unavailability)
kubectl scale deployment dapr-sidecar-injector -n dapr-system --replicas=0

# Restart a service pod
kubectl delete pod -l app=notification-service

# Check if service starts (liveness passes, readiness may fail)
kubectl wait --for=condition=ready pod -l app=notification-service --timeout=60s || echo "Expected: not ready without Dapr"

# Verify liveness still passes
kubectl exec -it $(kubectl get pod -l app=notification-service -o name | head -1) -- curl -s http://localhost:8080/health/live
# Expected: 200 OK (service lives, even without Dapr)

# Scale Dapr back up
kubectl scale deployment dapr-sidecar-injector -n dapr-system --replicas=1
```

---

## Step 9: Performance Validation

### Create 100 Recurring Tasks (Scalability Test)
```bash
# Run load test script
python scripts/load-test.py --tasks=100 --pattern=daily --jwt=$JWT_TOKEN

# Expected: All 100 tasks created within 60 seconds

# Verify no errors
kubectl logs -l app=chat-api --tail=100 | grep ERROR
# Expected: No ERROR logs
```

### Measure Event Latency (SC-009: <500ms)
```bash
# Run latency measurement script
python scripts/measure-latency.py --iterations=10 --jwt=$JWT_TOKEN

# Expected output: Average latency < 500ms
```

---

## Step 10: Rollback Validation

### Simulate Rollback to Phase IV
```bash
# Delete Phase V services
kubectl delete deployment notification-service reminder-service audit-logger recurring-task-processor

# Remove Dapr Pub/Sub component from Chat API
kubectl annotate deployment chat-api dapr.io/enabled-

# Restart Chat API
kubectl rollout restart deployment chat-api

# Run Phase IV smoke tests
pytest tests/phase4/ -v

# Expected: All Phase IV tests PASS (Phase V columns ignored)
```

### Restore Phase V (After Rollback Test)
```bash
# Re-enable Dapr on Chat API
kubectl annotate deployment chat-api dapr.io/enabled=true

# Redeploy Phase V services
kubectl apply -f k8s/services/

# Verify Phase V functionality restored
curl -X GET http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '. | length'

# Expected: All tasks (Phase IV + Phase V) accessible
```

---

## Troubleshooting

### Dapr Sidecar Not Injected
```bash
# Check Dapr sidecar injector is running
kubectl get pods -n dapr-system -l app=dapr-sidecar-injector

# Verify Dapr annotations on deployment
kubectl get deployment chat-api -o jsonpath='{.spec.template.metadata.annotations}'

# Expected annotations:
# - dapr.io/enabled: "true"
# - dapr.io/app-id: "chat-api"
# - dapr.io/app-port: "8000"
```

### Events Not Being Received
```bash
# Check Dapr Pub/Sub component
kubectl get components

# Check consumer logs for subscription errors
kubectl logs -l app=notification-service --tail=50 | grep ERROR

# Verify Kafka is reachable
kubectl exec -it $(kubectl get pod -l app=kafka -o name) -- kafka-topics.sh --bootstrap-server localhost:9092 --list
```

### Database Connection Errors
```bash
# Check PostgreSQL is running
kubectl get pods -l app=postgres

# Test database connection
kubectl exec -it $(kubectl get pod -l app=postgres -o name) -- psql -U taskflow_user -d taskflow_db -c "SELECT 1;"

# Check database credentials secret
kubectl get secret postgres-credentials -o yaml
```

---

## Success Criteria Checklist

- [ ] Minikube cluster running with Dapr initialized
- [ ] PostgreSQL and Kafka deployed and healthy
- [ ] Phase V database migration applied successfully
- [ ] All 5 Phase V services deployed with Dapr sidecars
- [ ] Phase IV smoke tests PASS (regression check)
- [ ] Recurring task creation works (User Story 1)
- [ ] Due date reminders scheduled (User Story 2)
- [ ] Real-time notifications delivered <2s (User Story 3)
- [ ] Audit logs captured for all events (User Story 4)
- [ ] Health endpoints return 200 for all services
- [ ] Services survive Dapr unavailability (liveness passes)
- [ ] Event latency <500ms (SC-009)
- [ ] Rollback to Phase IV succeeds with zero data loss

---

## Next Steps

After local validation succeeds:

1. **Run `/sp.tasks`** to generate task breakdown for implementation
2. **Implement services** following tasks.md order
3. **Cloud deployment** (after local success confirmed)

**Remember**: Local success MUST precede cloud deployment (Constitution Principle VI).

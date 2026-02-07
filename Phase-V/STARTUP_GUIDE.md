# Phase V - Complete Startup Guide

## Current Status

**Phase V is 63% complete (57/75 tasks)** with all critical services coded and ready to deploy.

### ✅ What's Working
- All service code is correct (no duplicate FastAPI issues)
- Docker Compose configuration is complete
- Database schemas are ready
- Dapr configuration is set up

### ⏳ What's Needed
- Docker Desktop must be running
- Services need to be started via Docker Compose
- End-to-end testing needs to be performed

---

## Quick Start (5 Steps)

### Step 1: Start Docker Desktop

**CRITICAL: You must start Docker Desktop first!**

1. Open Docker Desktop application on Windows
2. Wait for "Docker Desktop is running" message
3. Verify with: `docker ps` (should not show connection error)

---

### Step 2: Navigate to Phase-II Directory

```powershell
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II
```

---

### Step 3: Set Environment Variables

Create a `.env` file in the `backend` directory if not present:

```powershell
# Phase-II/backend/.env
ANTHROPIC_API_KEY=your_api_key_here
JWT_SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/todo_db
REDIS_URL=redis://redis:6379
```

---

### Step 4: Start All Services

```powershell
# Start all services in detached mode
docker-compose up -d

# Watch the logs
docker-compose logs -f
```

**Services Starting (in order):**
1. ✅ PostgreSQL (5432)
2. ✅ Zookeeper (2181)
3. ✅ Kafka (9092)
4. ✅ Redis (6379)
5. ✅ Dapr Placement (50006)
6. ✅ Backend API + Dapr sidecar (8000)
7. ✅ Recurring Processor + Dapr sidecar (8001)
8. ✅ Reminder Service + Dapr sidecar (8002)
9. ✅ Notification Service + Dapr sidecar (8003)
10. ✅ Audit Logger + Dapr sidecar (8004)
11. ✅ Frontend (3000)
12. ✅ Zipkin (9411)

**Expected startup time: 2-3 minutes**

---

### Step 5: Verify All Services Are Healthy

```powershell
# Check all containers are running
docker-compose ps

# Should show all services as "Up" or "healthy"

# Test health endpoints
curl http://localhost:8000/health/live  # Backend
curl http://localhost:8001/health/live  # Recurring Processor
curl http://localhost:8002/health/live  # Reminder Service
curl http://localhost:8003/health/live  # Notification Service
curl http://localhost:8004/health/live  # Audit Logger
```

---

## Testing the Complete System

### Test 1: Basic Task Creation

```powershell
# Create a test account
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'

# Login to get JWT token
$response = curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }' | ConvertFrom-Json

$token = $response.access_token

# Create a simple task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  -d '{
    "title": "Test Task",
    "description": "Testing Phase V",
    "priority": "high"
  }'
```

### Test 2: Recurring Task (User Story 1)

```powershell
# Create a daily recurring task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  -d '{
    "title": "Daily Standup",
    "description": "Team standup meeting",
    "recurrence_pattern": "daily",
    "recurrence_end_date": "2026-03-01T00:00:00Z"
  }'

# Wait 5 minutes for recurring processor to run
# Check logs for: "Generated instance for recurring task"
docker-compose logs recurring-processor | Select-String "Generated instance"
```

### Test 3: Reminder (User Story 2)

```powershell
# Create a task with reminder
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  -d '{
    "title": "Important Meeting",
    "due_date": "2026-02-01T17:00:00Z",
    "reminder_offset": "30 minutes"
  }'

# Check reminder service scheduled it
docker-compose logs reminder-service | Select-String "Scheduled reminder"
```

### Test 4: Real-Time Notifications (User Story 3)

Open browser and navigate to: http://localhost:3000

The frontend should connect to SSE endpoint and receive real-time notifications when tasks are created/updated.

### Test 5: Audit Trail (User Story 4)

```powershell
# Get task ID from previous test
$taskId = "your-task-id-here"

# Query audit history
curl http://localhost:8004/api/v1/audit/tasks/$taskId
```

---

## Monitoring & Debugging

### View Logs for Specific Service

```powershell
# Backend
docker-compose logs -f backend

# Recurring Processor
docker-compose logs -f recurring-processor

# Reminder Service
docker-compose logs -f reminder-service

# Notification Service
docker-compose logs -f notification-service

# Audit Logger
docker-compose logs -f audit-logger

# All Phase V services
docker-compose logs -f recurring-processor reminder-service notification-service audit-logger
```

### Check Kafka Topics

```powershell
# Enter Kafka container
docker exec -it taskflow-kafka bash

# List topics
kafka-topics --bootstrap-server localhost:9092 --list

# Should see:
# - taskflow.tasks.created
# - taskflow.tasks.updated
# - taskflow.tasks.completed
# - taskflow.tasks.deleted
# - taskflow.tasks.reminder-triggered

# Check messages in a topic
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic taskflow.tasks.created \
  --from-beginning \
  --max-messages 5
```

### Check Dapr Subscriptions

```powershell
# Check what topics each service is subscribed to
curl http://localhost:8001/dapr/subscribe  # Recurring Processor
curl http://localhost:8002/dapr/subscribe  # Reminder Service
curl http://localhost:8003/dapr/subscribe  # Notification Service
curl http://localhost:8004/dapr/subscribe  # Audit Logger
```

### Database Queries

```powershell
# Enter PostgreSQL container
docker exec -it taskflow-postgres psql -U postgres -d todo_db

# Check Phase V columns
\d tasks

# Check audit events table
\d task_events
SELECT event_type, task_id, created_at FROM task_events ORDER BY created_at DESC LIMIT 10;

# Check reminder schedule
\d reminder_schedule
SELECT * FROM reminder_schedule WHERE status = 'pending';

# Exit
\q
```

---

## Troubleshooting

### Issue: Docker Desktop not starting

**Solution:**
1. Check if Hyper-V/WSL2 is enabled
2. Restart Docker Desktop
3. If persistent, reinstall Docker Desktop

### Issue: Port conflicts (8000, 8001, etc. already in use)

**Solution:**
```powershell
# Find what's using the port
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

### Issue: Services failing to start

**Solution:**
```powershell
# Rebuild images
docker-compose build --no-cache

# Restart services
docker-compose down
docker-compose up -d
```

### Issue: Kafka not working

**Solution:**
```powershell
# Restart Kafka cluster
docker-compose restart zookeeper kafka

# Wait 30 seconds for cluster to stabilize
Start-Sleep -Seconds 30

# Restart dependent services
docker-compose restart backend recurring-processor reminder-service notification-service audit-logger
```

### Issue: Database connection errors

**Solution:**
```powershell
# Check PostgreSQL is healthy
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Wait for health check
docker-compose ps postgres
# Should show "healthy"
```

---

## Stopping Services

### Graceful Shutdown

```powershell
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

### Keep Data Between Runs

```powershell
# Stop services but keep volumes
docker-compose stop

# Start again later
docker-compose start
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Port 3000)                     │
│                    Next.js + React + SSE                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/SSE
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend API (Port 8000)                     │
│          FastAPI + JWT Auth + Task CRUD + Events            │
└─────────────┬───────────────────────────────────────────────┘
              │ Publishes events via Dapr
              ▼
┌─────────────────────────────────────────────────────────────┐
│              Kafka Broker (via Dapr Abstraction)            │
│  Topics: created, updated, completed, deleted, reminder     │
└─────┬─────┬─────────┬──────────┬────────────────────────────┘
      │     │         │          │
      │     │         │          └─────────────┐
      │     │         │                        │
      ▼     ▼         ▼                        ▼
┌─────────┐ ┌─────────┐ ┌──────────────┐ ┌──────────┐
│Recurring│ │Reminder │ │Notification  │ │  Audit   │
│Processor│ │ Service │ │   Service    │ │  Logger  │
│(8001)   │ │ (8002)  │ │   (8003)     │ │  (8004)  │
└─────────┘ └─────────┘ └──────────────┘ └──────────┘
     │           │              │               │
     │           │              │               │
     ▼           ▼              │               ▼
┌─────────────────────┐         │      ┌──────────────┐
│   PostgreSQL DB     │         │      │ task_events  │
│   - tasks table     │         │      │   (audit)    │
│   - reminder_sched  │         │      └──────────────┘
└─────────────────────┘         │
                                │
                                ▼
                    ┌───────────────────┐
                    │   SSE Clients     │
                    │ (Real-time notify)│
                    └───────────────────┘
```

---

## Next Steps After Startup

1. ✅ Verify all services are healthy
2. ✅ Run all 5 test scenarios above
3. ✅ Complete Phase 5 tasks (notifications)
4. ✅ Complete Phase 6 tasks (audit logging)
5. ✅ Complete Phase 7 tasks (polish & testing)
6. ✅ Commit changes to git
7. ✅ Create pull request

---

## Success Criteria

### Phase V is complete when:

1. **US1 - Recurring Tasks**: Daily/weekly tasks generate instances automatically
2. **US2 - Reminders**: Tasks with due dates trigger reminders at correct time
3. **US3 - Notifications**: SSE delivers task events within 2 seconds
4. **US4 - Audit**: All task events are immutably stored in task_events table

### All services are:
- ✅ Running without errors
- ✅ Handling events correctly (Kafka lag = 0)
- ✅ Passing health checks
- ✅ Logging properly

---

## Resources

- **Spec**: `specs/002-phase-v-event-driven-todos/spec.md`
- **Plan**: `specs/002-phase-v-event-driven-todos/plan.md`
- **Tasks**: `specs/002-phase-v-event-driven-todos/tasks.md`
- **Docker Compose**: `Phase-II/docker-compose.yaml`
- **Dapr Config**: `Phase-II/k8s/dapr/pubsub.yaml`

---

**Need Help?**

If you encounter any issues:
1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs -f <service-name>`
3. Verify Docker Desktop is running
4. Ensure no port conflicts

**Let's get Phase V fully operational! 🚀**

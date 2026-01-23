# TaskFlow - Event-Driven Task Management System

A modern, cloud-native task management system with AI-powered chatbot assistant, built with FastAPI, React, and event-driven microservices architecture.

## Overview

TaskFlow is a comprehensive task management platform combining traditional CRUD operations with advanced event-driven features:

- **Phase I**: Core Task CRUD with PostgreSQL persistence
- **Phase II**: AI Chatbot Assistant (Claude + MCP integration)
- **Phase III**: Recurring Task Automation
- **Phase IV**: Due Date Reminder System
- **Phase V**: Real-Time Notifications & Comprehensive Audit Logging

## Quick Start

### Local Development with Docker Compose

```bash
# 1. Set environment variables
cat > backend/.env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/todo_db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-api-key
DAPR_HTTP_PORT=3500
PUBSUB_NAME=taskflow-pubsub
EOF

# 2. Start all services
docker-compose up -d

# 3. Verify services
curl http://localhost:8000/health
curl http://localhost:8001/health/live
curl http://localhost:8002/health/live
curl http://localhost:8003/health/live
curl http://localhost:8004/health/live
```

Services started:
- Main Backend API (port 8000)
- Recurring Processor (port 8001)
- Reminder Service (port 8002)
- Notification Service (port 8003)
- Audit Logger (port 8004)
- PostgreSQL, Redis, Kafka, Dapr

## Phase V - Event-Driven Architecture

### Real-Time Notifications
- SSE streaming to browser clients
- Rate limiting: 10 notifications/second per connection
- Max 3 concurrent connections per user
- Heartbeat every 30 seconds
- Auto-cleanup stale connections

### Comprehensive Audit Logging
- Immutable event log in task_events table
- Batch write optimization (100 events or 1 second)
- Deduplication via event_id
- Monthly partitioning
- Query endpoint: GET /api/v1/audit/tasks/{task_id}

### Architecture

```
Client (React) → Main Backend API → Kafka (via Dapr)
                                         ↓
                    ┌────────────────────┼────────────────────┐
                    ↓                    ↓                    ↓
          Recurring Processor    Reminder Service    Notification Service
                    ↓                    ↓                    ↓
              Audit Logger ← Events ← All Services
                    ↓
              PostgreSQL (task_events table)
```

## Technology Stack

**Backend**: FastAPI, PostgreSQL, Redis, Kafka, Dapr, SQLAlchemy 2.0, Anthropic Claude
**Frontend**: React 18, TypeScript, Vite, TailwindCSS
**Infrastructure**: Kubernetes, Docker, Prometheus, Grafana

## API Endpoints

### Main Backend (8000)
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks` - List tasks
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task
- `POST /api/v1/chat` - AI chatbot

### Notification Service (8003)
- `GET /api/v1/notifications/stream` - SSE stream

### Audit Logger (8004)
- `GET /api/v1/audit/tasks/{task_id}` - Event history

## Event Topics

- `taskflow.tasks.created`
- `taskflow.tasks.updated`
- `taskflow.tasks.completed`
- `taskflow.tasks.deleted`
- `taskflow.tasks.reminder-triggered`

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Phase V smoke tests
./scripts/smoke_test_phase5.sh

# Regression tests
pytest backend/tests/test_phase4_regression.py -v
```

## Monitoring

- Metrics: http://localhost:800X/metrics
- Zipkin: http://localhost:9411
- Grafana: See monitoring/grafana-dashboard.json

## Troubleshooting

**Services not receiving events**: Check Dapr sidecar logs, verify subscriptions
**Database issues**: Verify PostgreSQL pod, check DATABASE_URL secret
**SSE not working**: Check CORS, JWT token, browser console

## License

[Your License Here]

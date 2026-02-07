# Phase V Restoration Checkpoint

**Created:** 2026-02-06
**Status:** IN PROGRESS - PHASE 3 (Configuration & Deployment)

## What Has Been Done

### PHASE 1: Clean Cluster Restore - COMPLETED
- Minikube cluster deleted and recreated fresh
- Using: `minikube start --driver=docker --memory=6144 --cpus=4`
- Cluster is running with Kubernetes v1.34.0

### PHASE 2: Docker Image Consistency - COMPLETED
All Docker images are built and available locally:

```
docker images | findstr phase
```

Images available:
- `phase-ii-backend:latest` - Main backend/chat-api
- `phase-ii-frontend:latest` - Next.js frontend
- `phase-ii-audit-logger:latest` - Audit logging service
- `phase-ii-notification-service:latest` - Notification service
- `phase-ii-recurring-processor:latest` - Recurring task processor
- `phase-ii-reminder-service:latest` - Reminder service

Infrastructure images needed (pull from DockerHub):
- `confluentinc/cp-kafka:7.6.1`
- `confluentinc/cp-zookeeper:7.6.1`
- `postgres:15-alpine`
- `redis:7-alpine`

## What Needs To Be Done

### PHASE 3: Configuration First
```powershell
# 1. Create namespaces
kubectl create namespace kafka
kubectl create namespace dapr-system

# 2. Apply secrets
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\secrets.yaml"
```

### PHASE 4: Stateful Dependencies
```powershell
# 1. Deploy Postgres
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\infrastructure\postgres-deployment.yaml"

# 2. Deploy Redis
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\infrastructure\redis-deployment.yaml"

# 3. Deploy Kafka/Zookeeper
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\infrastructure\kafka-deployment.yaml"

# 4. Wait for them to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=180s
kubectl wait --for=condition=ready pod -l app=redis --timeout=180s
kubectl wait --for=condition=ready pod -l app=zookeeper -n kafka --timeout=180s
kubectl wait --for=condition=ready pod -l app=kafka -n kafka --timeout=180s
```

### PHASE 5: Install Dapr
```powershell
# Install Dapr to cluster
dapr init -k --wait

# Apply Dapr pubsub component
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\dapr\pubsub.yaml"
```

### PHASE 6: Load Images Into Minikube
```powershell
# Load images ONE AT A TIME to avoid overloading
minikube image load phase-ii-backend:latest
minikube image load phase-ii-frontend:latest
minikube image load phase-ii-audit-logger:latest
minikube image load phase-ii-notification-service:latest
minikube image load phase-ii-recurring-processor:latest
minikube image load phase-ii-reminder-service:latest

# Also load infrastructure images if pull is slow
minikube image load confluentinc/cp-kafka:7.6.1
minikube image load confluentinc/cp-zookeeper:7.6.1
```

### PHASE 7: Deploy Backend Services
```powershell
# Deploy chat-api
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\services\chat-api-deployment.yaml"

# Deploy Phase V services
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\services\phase-v\audit-logger-deployment.yaml"
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\services\phase-v\notification-service-deployment.yaml"
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\services\phase-v\recurring-processor-deployment.yaml"
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\services\phase-v\reminder-service-deployment.yaml"
```

### PHASE 8: Deploy Frontend
```powershell
kubectl apply -f "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\k8s\services\frontend-deployment.yaml"
```

### PHASE 9: Start Tunnel & Verify
```powershell
# Start minikube tunnel (run in separate terminal)
minikube tunnel

# Then test in browser:
# - Frontend: http://127.0.0.1:3000
# - Backend API: http://127.0.0.1:8000
# - Health check: http://127.0.0.1:8000/health
```

## Key Configuration Files

| File | Purpose |
|------|---------|
| `k8s/secrets.yaml` | Database, Redis, Kafka, JWT, Anthropic API secrets |
| `k8s/infrastructure/postgres-deployment.yaml` | PostgreSQL database |
| `k8s/infrastructure/redis-deployment.yaml` | Redis cache |
| `k8s/infrastructure/kafka-deployment.yaml` | Kafka + Zookeeper |
| `k8s/dapr/pubsub.yaml` | Dapr pub/sub components and subscriptions |
| `k8s/services/chat-api-deployment.yaml` | Main backend API |
| `k8s/services/frontend-deployment.yaml` | Next.js frontend |
| `k8s/services/phase-v/*.yaml` | Phase V microservices |

## Known Issues & Solutions

1. **Minikube registry connectivity**: If external images are slow to pull, use `minikube image load` to pre-load from local Docker.

2. **Image names**: The backend image is `phase-ii-backend:latest`, but may need to be referenced as `phase-ii-chat-api:latest` in deployments. Check deployment files.

3. **Dapr init timeout**: If `dapr init -k` times out, the components may still be deploying. Check with `kubectl get pods -n dapr-system`.

4. **LoadBalancer services**: Need `minikube tunnel` running to access services at 127.0.0.1.

## Quick Resume Command

To resume this restoration, run:
```powershell
cd "C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-V"
# Then ask Claude: "Continue Phase V restoration from RESTORATION_CHECKPOINT.md"
```

## Expected Final State

- All pods Running (no CrashLoopBackOff, no Pending)
- Frontend accessible at http://127.0.0.1:3000
- Login/Signup working
- Manual CRUD operations working
- AI Chatbot CRUD operations working
- System monitoring shows "All Systems Operational"

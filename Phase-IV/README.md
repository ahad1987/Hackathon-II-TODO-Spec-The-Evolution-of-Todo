# Phase IV - Local Kubernetes Deployment

**Project**: TaskFlow AI Chatbot
**Goal**: Deploy existing Phase-II (Todo Web App) and Phase-III (AI Chatbot) to local Kubernetes (Minikube)
**Constitutional Mandate**: Zero application code changes, exact production behavior replication

---

## Overview

This phase containerizes and deploys the TaskFlow AI Chatbot to a local Kubernetes cluster using:
- **Docker** for containerization (backend: Python/FastAPI, frontend: Node.js/Next.js)
- **Minikube** for local Kubernetes cluster
- **Helm** for deployment orchestration

**Critical Constraint**: Phase-II and Phase-III application code is IMMUTABLE. This phase creates ONLY infrastructure artifacts.

---

## Directory Structure

```
Phase-IV/
├── docker/
│   ├── backend.Dockerfile       # FastAPI backend containerization
│   └── frontend.Dockerfile      # Next.js frontend containerization
│
├── helm/
│   ├── taskflow/                # Helm chart
│   │   ├── Chart.yaml           # Chart metadata
│   │   ├── values.yaml          # Default configuration
│   │   └── templates/           # Kubernetes resource templates
│   │       ├── _helpers.tpl     # Template helpers
│   │       ├── backend-configmap.yaml
│   │       ├── backend-secrets.yaml
│   │       ├── backend-deployment.yaml
│   │       ├── backend-service.yaml
│   │       ├── frontend-configmap.yaml
│   │       ├── frontend-secrets.yaml
│   │       ├── frontend-deployment.yaml
│   │       ├── frontend-service.yaml
│   │       └── NOTES.txt        # Post-install instructions
│   │
│   └── values-local.yaml.template  # Secrets template (copy and fill in)
│
├── specs/001-k8s-deployment/   # Planning documentation
│   ├── spec.md                  # Feature specification
│   ├── plan.md                  # Implementation plan
│   ├── tasks.md                 # Task breakdown
│   ├── research.md              # Best practices research
│   ├── data-model.md            # Data entities reference
│   ├── contracts/
│   │   └── api-contracts.md    # API endpoint documentation
│   └── quickstart.md            # Deployment scenarios
│
├── DEPLOYMENT.md                # Step-by-step deployment guide
├── ROLLBACK.md                  # Rollback & troubleshooting guide
└── README.md                    # This file
```

---

## Quick Start

### Prerequisites

- Docker Desktop (running)
- Minikube (v1.28+)
- Helm 3.x
- kubectl
- PostgreSQL database (accessible)
- Anthropic Claude API key

### Deployment (5 Steps)

1. **Start Minikube**:
   ```bash
   minikube start --cpus=4 --memory=8192
   ```

2. **Build and Load Images**:
   ```bash
   # Build backend
   cd Phase-II/backend
   docker build -f ../../Phase-IV/docker/backend.Dockerfile -t taskflow-backend:1.0.0 .

   # Build frontend
   cd ../frontend
   docker build -f ../../Phase-IV/docker/frontend.Dockerfile -t taskflow-frontend:1.0.0 .

   # Load into Minikube
   minikube image load taskflow-backend:1.0.0
   minikube image load taskflow-frontend:1.0.0
   ```

3. **Configure Secrets**:
   ```bash
   cd Phase-IV/helm
   copy values-local.yaml.template values-local.yaml
   # Edit values-local.yaml and fill in:
   # - DATABASE_URL
   # - BETTER_AUTH_SECRET (32+ chars)
   # - ANTHROPIC_API_KEY
   ```

4. **Deploy with Helm**:
   ```bash
   helm install taskflow ./taskflow -f values-local.yaml --wait
   ```

5. **Access Frontend**:
   ```bash
   minikube service taskflow-frontend-service --url
   ```

**Full deployment guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## Architecture

### Canonical Production Deployments

- **Frontend**: https://taskflow-ai-chatbot.vercel.app/ (Next.js on Vercel)
- **Backend**: https://huggingface.co/spaces/Ahad-00/taskflow-ai-backend (FastAPI on HuggingFace)

**Validation Requirement**: Kubernetes deployment MUST behave identically to production.

### Kubernetes Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Minikube Cluster                     │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Frontend (Next.js)                                │ │
│  │  - Port 3000                                       │ │
│  │  - NodePort Service (external access)             │ │
│  │  - Init container waits for backend               │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │ Internal DNS                      │
│                      │ http://taskflow-backend-service:8000
│                      ↓                                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Backend (FastAPI)                                 │ │
│  │  - Port 8000                                       │ │
│  │  - ClusterIP Service (internal only)              │ │
│  │  - Health probes on /health                       │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │                                   │
└──────────────────────┼───────────────────────────────────┘
                       │
                       ↓
              PostgreSQL Database
              (external to cluster)
```

### Backend Container

- **Base Image**: `python:3.11-slim` (Debian for psycopg2 wheel compatibility)
- **Port**: 8000 (IMMUTABLE per API contracts)
- **Startup**: `uvicorn src.main:app --host 0.0.0.0 --port 8000`
- **Health Check**: `/health` endpoint
- **Dependencies**: All from Phase-II `requirements.txt`

### Frontend Container

- **Base Image**: `node:18-alpine`
- **Build**: Multi-stage (dependencies → builder → runner)
- **Output**: Next.js standalone mode
- **Port**: 3000 (IMMUTABLE per API contracts)
- **Startup**: `node server.js`
- **Health Check**: `/` endpoint

---

## API Contracts (IMMUTABLE)

All 11 API endpoints from Phase-II and Phase-III are preserved exactly:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/v1/auth/signup` | POST | User registration |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/logout` | POST | User logout |
| `/api/v1/auth/me` | GET | Current user info |
| `/api/v1/auth/refresh` | POST | Token refresh |
| `/api/v1/tasks` | GET | List tasks |
| `/api/v1/tasks` | POST | Create task |
| `/api/v1/tasks/{id}` | PUT | Update task |
| `/api/v1/tasks/{id}` | DELETE | Delete task |
| `/api/v1/chat` | POST | Chatbot interaction |

**Authentication**: JWT via `Authorization: Bearer <token>` header
**CORS**: Configured to include Minikube NodePort URL

Full API documentation: [specs/001-k8s-deployment/contracts/api-contracts.md](./specs/001-k8s-deployment/contracts/api-contracts.md)

---

## Environment Variables

### Backend (Required)

| Variable | Type | Description |
|----------|------|-------------|
| `DATABASE_URL` | Secret | PostgreSQL connection string |
| `BETTER_AUTH_SECRET` | Secret | JWT signing secret (32+ chars) |
| `ANTHROPIC_API_KEY` | Secret | Claude API key |
| `CORS_ORIGINS` | Secret | Allowed origins (include Minikube URL) |
| `API_PREFIX` | Config | `/api/v1` |
| `ENVIRONMENT` | Config | `development` |
| `DEBUG` | Config | `False` |

### Frontend (Required)

| Variable | Type | Description |
|----------|------|-------------|
| `NEXT_PUBLIC_API_URL` | Config | `http://taskflow-backend-service:8000` |
| `BETTER_AUTH_SECRET` | Secret | Must match backend secret |
| `BETTER_AUTH_URL` | Secret | Frontend URL (Minikube NodePort) |
| `NODE_ENV` | Config | `production` |

---

## Validation & Testing

### Pre-Deployment Validation

- [x] Docker images build successfully
- [x] No application code modified (`git status` clean)
- [x] Helm charts pass lint check
- [x] Secrets configured in `values-local.yaml`

### Post-Deployment Validation

- [x] All pods reach Running state (1/1 Ready)
- [x] Backend health check returns 200 OK
- [x] Frontend loads without JavaScript errors
- [x] No CORS errors in browser console

### End-to-End Testing

- [x] User signup creates account
- [x] User login returns JWT token
- [x] Create task persists to database
- [x] Update task modifies existing task
- [x] Complete task updates status
- [x] Delete task removes from list
- [x] Chatbot responds to messages
- [x] Chatbot executes MCP tools (add_task, list_tasks, etc.)

### Production Comparison

All operations MUST match behavior of:
- Frontend: https://taskflow-ai-chatbot.vercel.app/
- Backend: https://huggingface.co/spaces/Ahad-00/taskflow-ai-backend

**Constitutional Mandate**: Any deviation triggers INVALID status and requires correction.

---

## Rollback & Troubleshooting

**Quick Rollback**:
```bash
helm rollback taskflow
```

**Complete Uninstall**:
```bash
helm uninstall taskflow
```

**Common Issues**:
- Database connection failed → Verify `DATABASE_URL`
- JWT secrets mismatch → Verify frontend/backend secrets identical
- CORS errors → Verify `CORS_ORIGINS` includes Minikube NodePort URL
- Image pull errors → Reload images with `minikube image load`

**Full troubleshooting guide**: [ROLLBACK.md](./ROLLBACK.md)

---

## Constitutional Principles

**This deployment adheres to the Phase IV Constitution:**

### ✅ Immutability of Working Systems
- Phase-II and Phase-III code is UNTOUCHED
- All changes are infrastructure-only (Dockerfiles, Helm charts)

### ✅ Canonical Reference Authority
- Production deployments define CORRECT behavior
- Kubernetes deployment replicates production EXACTLY

### ✅ Infrastructure Adaptation Principle
- Ports preserved: Backend 8000, Frontend 3000
- Routes preserved: All `/api/v1/*` endpoints
- Schemas preserved: All request/response formats

### ✅ Tool Constraints
- Docker Desktop for containerization
- Minikube for local Kubernetes
- Helm for orchestration (NO raw YAML)
- kubectl-ai / kagent for AI-assisted operations (optional)

### ✅ Safety Over Completion
- Validation checkpoints at each phase
- Rollback procedures documented
- STOP on any ambiguity or mismatch

### ✅ Zero Application Modification
- NO frontend code changes
- NO backend code changes
- NO API route modifications
- NO schema changes

---

## Maintenance

### Updating Deployment

To apply configuration changes:
```bash
# Edit values-local.yaml
helm upgrade taskflow ./taskflow -f values-local.yaml
```

### Scaling

Scale backend (independent of frontend):
```bash
kubectl scale deployment taskflow-backend --replicas=2
```

Scale frontend:
```bash
kubectl scale deployment taskflow-frontend --replicas=2
```

### Viewing Logs

```bash
# Backend logs
kubectl logs -f deployment/taskflow-backend

# Frontend logs
kubectl logs -f deployment/taskflow-frontend
```

### Resource Monitoring

```bash
# Pod resource usage
kubectl top pods

# Node resource usage
kubectl top node
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Step-by-step deployment guide (11 steps) |
| [ROLLBACK.md](./ROLLBACK.md) | Rollback procedures & troubleshooting |
| [specs/001-k8s-deployment/spec.md](./specs/001-k8s-deployment/spec.md) | Feature specification with requirements |
| [specs/001-k8s-deployment/plan.md](./specs/001-k8s-deployment/plan.md) | Implementation plan with architecture |
| [specs/001-k8s-deployment/tasks.md](./specs/001-k8s-deployment/tasks.md) | Task breakdown (72 tasks) |
| [specs/001-k8s-deployment/research.md](./specs/001-k8s-deployment/research.md) | Best practices research (480 lines) |
| [specs/001-k8s-deployment/contracts/api-contracts.md](./specs/001-k8s-deployment/contracts/api-contracts.md) | API endpoint documentation |

---

## Success Metrics

Deployment is successful when:

- ✅ All pods Running (1/1 Ready) within 2 minutes
- ✅ Health checks return 200 OK consistently
- ✅ Frontend loads in < 2 seconds
- ✅ API latency < 100ms (local network)
- ✅ Full workflow (signup → tasks → chatbot) works identically to production
- ✅ Zero CORS errors
- ✅ Zero application code changes (`git status` clean)

---

## Getting Help

### Diagnostic Commands

```bash
# Check everything
kubectl get all

# Get recent events
kubectl get events --sort-by='.lastTimestamp'

# Helm status
helm status taskflow

# Helm history
helm history taskflow
```

### Quick Reference

```bash
# Get frontend URL
minikube service taskflow-frontend-service --url

# Port-forward backend
kubectl port-forward deployment/taskflow-backend 8000:8000

# Restart pods
kubectl rollout restart deployment/taskflow-backend
kubectl rollout restart deployment/taskflow-frontend

# Delete everything
helm uninstall taskflow
```

---

## License

This deployment configuration is part of the TaskFlow AI Chatbot project.

---

**Phase IV: Local Kubernetes Deployment Ready!** 🚀

For deployment, start with: [DEPLOYMENT.md](./DEPLOYMENT.md)

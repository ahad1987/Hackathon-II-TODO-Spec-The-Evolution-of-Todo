# Implementation Plan: Phase IV Local Kubernetes Deployment

**Branch**: `001-k8s-deployment` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-k8s-deployment/spec.md`

---

## Summary

Deploy TaskFlow AI Chatbot (Next.js frontend + FastAPI backend) to local Kubernetes (Minikube) using Helm charts while preserving exact API contracts from production deployments at Vercel and HuggingFace. This is a DEPLOYMENT-ONLY project with ZERO application code changes permitted.

**Technical Approach**:
- Containerize frontend and backend using Docker multi-stage builds
- Package deployment using Helm charts (single chart, multiple deployments)
- Deploy backend first with health validation, then frontend
- Use Kubernetes internal DNS for frontend-to-backend communication
- Validate deployment against canonical production references

---

## Technical Context

**Language/Version**: Multi-language deployment project
- Frontend: Node.js 18 (Next.js framework)
- Backend: Python 3.11 (FastAPI framework)
- Infrastructure: Kubernetes via Minikube, Helm 3.x

**Primary Dependencies**:
- Docker Desktop (container runtime)
- Minikube (local Kubernetes cluster)
- Helm 3.x (deployment orchestration)
- kubectl (Kubernetes CLI)
- Optional: Docker AI Agent (Gordon), kubectl-ai, kagent

**Storage**: PostgreSQL database (external to Kubernetes, accessed via DATABASE_URL)

**Testing**: Manual validation against production deployments (no automated tests in scope)

**Target Platform**: Minikube (local Kubernetes) on Windows/macOS/Linux

**Project Type**: Infrastructure deployment (not application development)

**Performance Goals**:
- Pod startup time < 2 minutes
- Health check response < 100ms
- Frontend-to-backend API latency < 100ms (local network)

**Constraints**:
- Application code is IMMUTABLE (Constitutional mandate)
- Helm-only orchestration (no raw Kubernetes YAML)
- Minikube-only deployment (no cloud Kubernetes)
- Production API contracts must be preserved exactly

**Scale/Scope**:
- 2 containerized services (frontend + backend)
- Local development deployment (not production-scale)
- Single-replica initial deployment (scalable to multi-replica)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Immutability of Working Systems
- **Status**: PASS
- **Validation**: No modifications to Phase-II or Phase-III application code planned
- **Evidence**: Plan focuses exclusively on Docker, Kubernetes, and Helm configuration

### ✅ Canonical Reference Authority
- **Status**: PASS
- **Validation**: Production deployments documented as validation criteria
- **Evidence**: spec.md references Vercel and HuggingFace as ground truth

### ✅ Infrastructure Adaptation Principle
- **Status**: PASS
- **Validation**: Kubernetes adapts to application (ports 8000/3000, API routes preserved)
- **Evidence**: data-model.md and api-contracts.md document existing application requirements

### ✅ Tool Constraints
- **Status**: PASS
- **Validation**: Plan uses Docker Desktop, Minikube, Helm, kubectl-ai, kagent as specified
- **Evidence**: research.md evaluates these tools for deployment

### ✅ Safety Over Completion
- **Status**: PASS
- **Validation**: Plan includes pre-deployment validation, rollback procedures, failure checkpoints
- **Evidence**: quickstart.md documents rollback triggers and investigation procedures

### ✅ Zero Application Modification
- **Status**: PASS
- **Validation**: Plan creates only infrastructure artifacts (Dockerfiles, Helm charts, configs)
- **Evidence**: No tasks involve modifying frontend or backend source code

**Gate Result**: ✅ ALL CHECKS PASS - Proceed to Phase 0

---

## Project Structure

### Documentation (this feature)

```text
specs/001-k8s-deployment/
├── plan.md                 # This file (/sp.plan command output)
├── research.md             # Phase 0 output (deployment best practices research)
├── data-model.md           # Phase 1 output (existing data entities reference)
├── quickstart.md           # Phase 1 output (deployment guide)
├── contracts/              # Phase 1 output
│   └── api-contracts.md    # API endpoint documentation
├── checklists/             # Quality validation
│   └── requirements.md     # Spec quality checklist
└── spec.md                 # Feature specification (/sp.specify output)
```

### Source Code (repository root)

**Existing Application Structure** (IMMUTABLE):
```text
Phase-II/
├── backend/
│   ├── src/                    # FastAPI application (existing, immutable)
│   │   ├── main.py             # Application entry point
│   │   ├── config.py           # Environment configuration
│   │   ├── database.py         # PostgreSQL connection
│   │   ├── api/                # API routes
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── tasks.py        # Task CRUD endpoints
│   │   │   └── health.py       # Health check
│   │   ├── chatbot/            # Phase-III chatbot integration
│   │   │   ├── api/routes/chat.py  # Chat endpoint
│   │   │   ├── services/       # Conversation and agent services
│   │   │   ├── mcp/            # MCP tools (task operations)
│   │   │   └── models/         # Conversation and message models
│   │   ├── models/             # Data models (User, Task)
│   │   ├── services/           # Business logic
│   │   └── middleware/         # Authentication middleware
│   └── requirements.txt        # Python dependencies (existing, immutable)
│
└── frontend/
    ├── src/                    # Next.js application (existing, immutable)
    │   ├── app/                # Next.js 13+ app directory
    │   ├── components/         # React components
    │   └── lib/                # Utility functions
    ├── package.json            # Node dependencies (existing, immutable)
    └── next.config.js          # Next.js configuration (existing, immutable)
```

**NEW Infrastructure Artifacts** (Phase IV creates these):
```text
Phase-IV/
├── helm/
│   └── taskflow/               # Helm chart (NEW - created in implementation)
│       ├── Chart.yaml          # Chart metadata
│       ├── values.yaml         # Configuration values
│       └── templates/          # Kubernetes resource templates
│           ├── backend-deployment.yaml
│           ├── backend-service.yaml
│           ├── backend-configmap.yaml
│           ├── backend-secrets.yaml
│           ├── frontend-deployment.yaml
│           ├── frontend-service.yaml
│           ├── frontend-configmap.yaml
│           └── frontend-secrets.yaml
│
├── docker/                     # Dockerfiles (NEW - created in implementation)
│   ├── backend.Dockerfile      # FastAPI containerization
│   └── frontend.Dockerfile     # Next.js containerization
│
└── specs/001-k8s-deployment/   # This planning documentation
```

**Structure Decision**: This is a deployment project overlaying infrastructure on existing application code. The existing application structure (Phase-II/backend, Phase-II/frontend) remains untouched. Phase IV creates NEW infrastructure artifacts (Dockerfiles, Helm charts) in a separate Phase-IV directory to containerize and deploy the existing applications.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. Constitution Check passed all gates.

---

## Phase 0: Research & Best Practices

### Research Completed

**Document**: `research.md` (480 lines)

**Key Findings**:

1. **Docker Base Images**:
   - Frontend: `node:18-alpine` (multi-stage build, standalone mode)
   - Backend: `python:3.11-slim` (Debian, NOT Alpine - critical for psycopg2 wheels)

2. **Helm Architecture**:
   - Single Helm chart with multiple Deployments (not sub-charts)
   - Simpler for tightly-coupled frontend-backend applications
   - Semantic versioning (SemVer 2.0.0) for Chart.yaml

3. **Service Networking**:
   - Backend: ClusterIP (internal-only, secure)
   - Frontend: NodePort (external access for local dev)
   - DNS: `http://taskflow-backend-service:8000`

4. **Configuration Management**:
   - ConfigMaps: Non-sensitive data (API URLs, ports, debug flags)
   - Secrets: Credentials (DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY)
   - Important: Next.js `NEXT_PUBLIC_` variables are build-time only

5. **Health Probes**:
   - Implement Startup, Liveness, Readiness probes
   - Separate endpoints: `/health/live` (lightweight) and `/health/ready` (checks dependencies)
   - Backend already has `/health` endpoint (will serve as liveness probe)

6. **Resource Allocation**:
   - Minikube: 4 CPUs, 8GB RAM
   - Backend: 256Mi/250m requests, 512Mi/500m limits
   - Frontend: 128Mi/250m requests, 256Mi/500m limits

7. **Deployment Ordering**:
   - Backend-first deployment using init containers
   - Frontend waits for backend readiness before starting

8. **CORS Handling**:
   - Handle at FastAPI application level (middleware already configured)
   - Add Minikube NodePort endpoint to CORS_ORIGINS environment variable

**Sources**: 35+ authoritative sources from Kubernetes docs, FastAPI docs, Helm docs, industry best practices (2025-2026)

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

**Existing Entities** (IMMUTABLE):
- User (id, email, password_hash, created_at, updated_at)
- Task (id, user_id, title, description, completed, created_at, updated_at)
- Conversation (id, user_id, created_at, updated_at)
- Message (id, conversation_id, role, content, tool_calls, created_at)

**NEW Kubernetes Entities**:
- ConfigMap data (API_PREFIX, ENVIRONMENT, DEBUG, etc.)
- Secret data (DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY)
- Service discovery metadata (DNS names, ports)

**Database**: PostgreSQL (external to Kubernetes, no PVCs required)

### API Contracts (`contracts/api-contracts.md`)

**11 Documented Endpoints** (IMMUTABLE):
1. `GET /health` - Health check
2. `POST /api/v1/auth/signup` - User registration
3. `POST /api/v1/auth/login` - User login
4. `POST /api/v1/auth/logout` - User logout (stub)
5. `GET /api/v1/auth/me` - Current user info
6. `POST /api/v1/auth/refresh` - Token refresh
7. `GET /api/v1/tasks` - List tasks
8. `POST /api/v1/tasks` - Create task
9. `PUT /api/v1/tasks/{task_id}` - Update task
10. `DELETE /api/v1/tasks/{task_id}` - Delete task
11. `POST /api/v1/chat` - Chatbot interaction

**Authentication**: JWT via Authorization header (HS256, BETTER_AUTH_SECRET)
**CORS**: Configured via CORS_ORIGINS environment variable (must include Minikube endpoint)

### Quickstart Guide (`quickstart.md`)

**10-Step Deployment Process**:
1. Start Minikube (4 CPUs, 8GB RAM)
2. Prepare environment secrets (DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY)
3. Configure CORS origins (add Minikube IP)
4. Build Docker images (backend + frontend)
5. Load images into Minikube
6. Deploy with Helm
7. Verify pod status (Running, 1/1 Ready)
8. Check health endpoints (200 OK)
9. Access frontend (via NodePort)
10. Test full workflow (signup → task creation → chatbot)

**Rollback Procedure**: `helm rollback` or `helm uninstall` on validation failure
**Common Issues**: Database connection, CORS errors, JWT secret mismatch, chatbot API errors

---

## Deployment Strategy

### 1. Live-Contract Verification Strategy

**Pre-Deployment Verification**:
- Compare existing application code routes with api-contracts.md
- Verify ports (backend 8000, frontend 3000) in existing configs
- Validate environment variables match production requirements
- Confirm no application code changes (`git status` clean for src/)

**Post-Deployment Verification**:
- Call each API endpoint from deployed backend
- Compare responses byte-for-byte with production HuggingFace backend
- Test authentication flow (signup → login → JWT validation)
- Test task CRUD operations against production behavior
- Test chatbot interaction and MCP tool execution
- Verify frontend UI matches Vercel production exactly

**Validation Checkpoints**:
1. After backend deployment: Health check returns 200 OK
2. After frontend deployment: UI loads without JavaScript errors
3. After full deployment: End-to-end workflow succeeds
4. Continuous: No CORS errors in browser console

---

### 2. Safe Containerization Approach

**Backend Containerization**:
- Base image: `python:3.11-slim` (Debian-based for psycopg2 wheel compatibility)
- Multi-stage build (if build dependencies required)
- Copy `requirements.txt` first for layer caching
- Install dependencies: `pip install --no-cache-dir --upgrade -r requirements.txt`
- Copy application code AS-IS (no modifications)
- Working directory: `/app`
- Expose port: `8000`
- Run as non-root user for security
- CMD: `fastapi run src/main.py --port 8000 --host 0.0.0.0`

**Frontend Containerization**:
- Base image: `node:18-alpine`
- 3-stage build: dependencies → builder → runner
- Stage 1 (dependencies): Install all dependencies
- Stage 2 (builder): Build Next.js application with `next build`
- Stage 3 (runner): Copy `.next/standalone`, `.next/static`, `public` only
- Enable standalone mode in `next.config.js`: `output: 'standalone'` (if not already set - CHECK FIRST)
- Working directory: `/app`
- Expose port: `3000`
- Run as non-root user
- ENV: `NODE_ENV=production`
- CMD: `node server.js`

**Safety Measures**:
- NO code modifications in Dockerfiles (only COPY commands)
- NO dependency updates (use existing `requirements.txt` and `package.json`)
- NO configuration changes (use existing configs as-is)
- Validate images build without errors before proceeding

---

### 3. Image Build & Tagging Strategy

**Image Naming Convention**:
- Backend: `taskflow-backend:1.0.0`
- Frontend: `taskflow-frontend:1.0.0`

**Versioning**:
- Start at `1.0.0` (initial Kubernetes deployment)
- Increment PATCH for bug fixes (e.g., `1.0.1`)
- Increment MINOR for new features (e.g., `1.1.0`)
- Increment MAJOR for breaking changes (e.g., `2.0.0`)
- Use `latest` tag for development convenience (points to most recent version)

**Build Process**:
- Prefer Docker AI Agent (Gordon) for Dockerfile generation
- Fallback to manual Dockerfiles if Gordon unavailable
- Build locally using Docker Desktop
- Tag with version number AND `latest`
- Load into Minikube: `minikube image load <image>:<tag>`

**Image Registry**:
- Local development: No registry push required (load directly into Minikube)
- Future production: Push to Docker Hub or private registry (out of scope for Phase IV)

---

### 4. Helm Chart Strategy

**Chart Structure**:
```
helm/taskflow/
├── Chart.yaml              # Metadata (name, version, description)
├── values.yaml             # Default configuration values
├── templates/
│   ├── backend-deployment.yaml      # Backend Deployment resource
│   ├── backend-service.yaml         # Backend Service (ClusterIP)
│   ├── backend-configmap.yaml       # Backend non-sensitive config
│   ├── backend-secrets.yaml         # Backend sensitive credentials
│   ├── frontend-deployment.yaml     # Frontend Deployment resource
│   ├── frontend-service.yaml        # Frontend Service (NodePort)
│   ├── frontend-configmap.yaml      # Frontend non-sensitive config
│   ├── frontend-secrets.yaml        # Frontend sensitive credentials
│   ├── _helpers.tpl                 # Template helpers (labels, selectors)
│   └── NOTES.txt                    # Post-install instructions
```

**Chart.yaml**:
```yaml
apiVersion: v2
name: taskflow
description: TaskFlow AI Chatbot - Local Kubernetes Deployment
version: 1.0.0  # Chart version (bump on Helm chart changes)
appVersion: "1.0.0"  # Application version
```

**values.yaml** (structure - NO actual values here):
- Image tags (backend, frontend)
- Replica counts (default 1 for local dev)
- Resource requests/limits
- Service ports (backend 8000, frontend 3000)
- NodePort ranges
- Environment variables (non-sensitive defaults)
- Secrets (placeholders - overridden at install time)

**Port Preservation**:
- Backend container port: `8000` (IMMUTABLE)
- Backend service port: `8000` (IMMUTABLE)
- Frontend container port: `3000` (IMMUTABLE)
- Frontend service port: `3000` (IMMUTABLE)
- Frontend NodePort: Auto-assigned by Kubernetes (30000-32767 range)

**Route Preservation**:
- NO path rewriting in Service definitions
- NO Ingress configuration (using NodePort instead)
- Backend routes exposed exactly as defined (no prefixes added)

---

### 5. Backend-First Deployment Order

**Deployment Sequence**:
1. Deploy backend ConfigMap (environment variables)
2. Deploy backend Secrets (DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY)
3. Deploy backend Deployment (FastAPI pods)
4. Deploy backend Service (ClusterIP on port 8000)
5. **CHECKPOINT**: Wait for backend pods to reach `Running` and pass readiness probe
6. Deploy frontend ConfigMap (NEXT_PUBLIC_API_URL pointing to backend service)
7. Deploy frontend Secrets (BETTER_AUTH_SECRET matching backend)
8. Deploy frontend Deployment (Next.js pods)
9. Deploy frontend Service (NodePort on port 3000)
10. **CHECKPOINT**: Wait for frontend pods to reach `Running` and pass readiness probe

**Dependency Management**:
- Frontend Deployment includes init container that waits for backend Service to be ready
- Init container performs DNS lookup for `taskflow-backend-service`
- Init container performs HTTP GET to `http://taskflow-backend-service:8000/health`
- Frontend main container starts ONLY after init container succeeds

**Helm Orchestration**:
- Helm installs resources in dependency order automatically
- Add `helm.sh/hook` annotations if strict ordering required
- Use `helm install --wait` flag to block until all resources are ready

---

### 6. Internal Service Exposure Strategy

**Backend Service** (`taskflow-backend-service`):
- Type: `ClusterIP` (internal-only, not accessible outside cluster)
- Port: `8000` (maps to container port 8000)
- Selector: `app: taskflow, component: backend`
- DNS: `taskflow-backend-service.default.svc.cluster.local` (full FQDN)
- Simplified DNS: `taskflow-backend-service` (within same namespace)

**Service Discovery Configuration**:
- Frontend ConfigMap includes: `NEXT_PUBLIC_API_URL=http://taskflow-backend-service:8000`
- Frontend code calls backend using this environment variable
- Kubernetes DNS resolves `taskflow-backend-service` to backend pod IPs
- Kubernetes Service load-balances requests across backend pods (if multiple replicas)

**Security**:
- Backend Service is NOT exposed externally (no NodePort or LoadBalancer)
- Only frontend pods can reach backend (via internal cluster network)
- Backend pods are not directly accessible from host machine

---

### 7. Frontend Exposure ONLY After Backend Validation

**Frontend Service** (`taskflow-frontend-service`):
- Type: `NodePort` (external access from host machine)
- Port: `3000` (maps to container port 3000)
- NodePort: Auto-assigned in range 30000-32767 (or specify manually)
- Selector: `app: taskflow, component: frontend`

**Validation Sequence**:
1. Deploy backend (ConfigMap, Secrets, Deployment, Service)
2. **VALIDATE**: Backend pods Running (1/1 Ready)
3. **VALIDATE**: Backend health check returns 200 OK
4. **VALIDATE**: Backend `/api/v1/auth/signup` endpoint responds (test with curl from Minikube)
5. Deploy frontend (ConfigMap, Secrets, Deployment, Service) ONLY after backend validates
6. **VALIDATE**: Frontend pods Running (1/1 Ready)
7. **VALIDATE**: Frontend loads in browser without errors
8. **VALIDATE**: Frontend can call backend (no CORS errors)

**Failure Handling**:
- If backend validation fails, STOP deployment (do not deploy frontend)
- Investigate backend logs (`kubectl logs <backend-pod>`)
- Fix issue (environment variables, database connection, etc.)
- Retry backend deployment
- Proceed to frontend ONLY after backend succeeds

**CORS Validation**:
- After frontend deployment, get NodePort: `kubectl get service taskflow-frontend-service`
- Get Minikube IP: `minikube ip`
- Verify `CORS_ORIGINS` in backend includes `http://<minikube-ip>:<nodeport>`
- If missing, update backend ConfigMap and restart backend pods

---

### 8. AI-Assisted Operations Strategy

**Docker AI Agent (Gordon)**:
- **Use Case**: Dockerfile generation
- **Command**: `gordon dockerfile create --context ./Phase-II/backend --output ./Phase-IV/docker/backend.Dockerfile`
- **Fallback**: Manual Dockerfile creation if Gordon unavailable
- **Validation**: Review generated Dockerfile for correctness before building

**kubectl-ai**:
- **Use Case**: Kubernetes operations (deploy, scale, troubleshoot)
- **Example**: `kubectl-ai scale backend to 2 replicas`
- **Example**: `kubectl-ai why is backend pod crashing?`
- **Fallback**: Standard `kubectl` commands if kubectl-ai unavailable

**kagent**:
- **Use Case**: Cluster health monitoring and optimization
- **Example**: `kagent health check` (analyze pod status, resource usage, network issues)
- **Example**: `kagent optimize resources` (suggest resource limit adjustments)
- **Fallback**: Manual monitoring with `kubectl top pods`, `kubectl describe pod`

**Integration Points**:
1. Dockerfile creation: Gordon or manual
2. Image building: `docker build` (standard)
3. Helm deployment: `helm install` (standard)
4. Post-deployment monitoring: kubectl-ai and kagent
5. Troubleshooting: kubectl-ai for diagnosis, kagent for optimization

**AI Tool Availability**:
- All AI tools are OPTIONAL (plan works without them)
- Use standard tools (docker, helm, kubectl) as primary approach
- Use AI tools for assistance and automation where available

---

### 9. Failure Checkpoints and Rollback Logic

**Checkpoint 1: Pre-Deployment Validation**
- **Check**: Git status clean (no application code changes)
- **Check**: Docker images build successfully
- **Check**: Helm charts pass `helm lint`
- **Check**: Environment secrets file prepared
- **Failure**: STOP - Fix issue before proceeding
- **Rollback**: Not applicable (deployment hasn't started)

**Checkpoint 2: Backend Deployment**
- **Check**: Backend ConfigMap and Secrets created
- **Check**: Backend Deployment created
- **Check**: Backend pods reach `Running` state (within 2 minutes)
- **Check**: Backend readiness probe passes (health check returns 200 OK)
- **Failure**: Backend pods crash or fail health check
- **Rollback**: `helm rollback taskflow` or investigate logs (`kubectl logs <pod>`)

**Checkpoint 3: Backend API Validation**
- **Check**: Call `/health` endpoint from within cluster (returns 200 OK)
- **Check**: Call `/api/v1/auth/signup` with test credentials (returns 201 Created)
- **Check**: Backend logs show no errors
- **Failure**: API returns wrong status code or response format
- **Rollback**: `helm rollback taskflow`, compare responses with production, investigate

**Checkpoint 4: Frontend Deployment**
- **Check**: Frontend ConfigMap and Secrets created
- **Check**: Frontend Deployment created
- **Check**: Frontend pods reach `Running` state (within 2 minutes)
- **Check**: Frontend readiness probe passes
- **Failure**: Frontend pods crash or fail health check
- **Rollback**: `helm rollback taskflow` or investigate logs

**Checkpoint 5: Frontend-Backend Integration**
- **Check**: Frontend can resolve `taskflow-backend-service` DNS
- **Check**: Frontend can call backend `/health` endpoint
- **Check**: No CORS errors in browser console
- **Check**: Frontend UI loads without JavaScript errors
- **Failure**: DNS resolution fails or CORS errors occur
- **Rollback**: `helm rollback taskflow`, check CORS_ORIGINS, check Service configuration

**Checkpoint 6: End-to-End Validation**
- **Check**: User signup works (creates user in database)
- **Check**: User login returns JWT token
- **Check**: Task creation persists to database
- **Check**: Chatbot responds to messages
- **Check**: Chatbot can execute MCP tools (add_task, list_tasks, etc.)
- **Failure**: Any operation fails or behaves differently than production
- **Rollback**: `helm rollback taskflow`, document failure, investigate root cause

**Rollback Procedure**:
```
1. Immediate action: helm rollback taskflow <revision>
   (if no previous revision: helm uninstall taskflow)

2. Document failure:
   - Screenshot error messages
   - Copy pod logs: kubectl logs <pod-name> > logs.txt
   - Copy pod events: kubectl describe pod <pod-name> > events.txt
   - Copy service config: kubectl describe service <service-name> > service.txt

3. Investigation (do NOT proceed without understanding):
   - Compare deployed config with production config
   - Check environment variables in Secrets/ConfigMaps
   - Verify database connectivity
   - Check CORS configuration
   - Test API endpoints individually

4. Fix root cause (NOT symptoms):
   - Update Helm values.yaml if config issue
   - Update Secrets if credentials issue
   - Update ConfigMap if environment variable issue
   - Rebuild images if Dockerfile issue

5. Re-deploy after fix:
   - helm upgrade taskflow ./helm/taskflow -f values-updated.yaml

6. Re-run validation from Checkpoint 1
```

**NEVER**:
- Guess at fixes without understanding root cause
- Modify application code to "fix" deployment issues
- Proceed with partial deployment (backend works but frontend doesn't)
- Skip checkpoints to save time

---

## Implementation Phases (NOT Implementation - Planning ONLY)

### Phase 0: Prerequisites & Environment Setup
- Verify Docker Desktop, Minikube, Helm, kubectl installed
- Start Minikube with 4 CPUs, 8GB RAM
- Prepare environment secrets (DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY)
- Verify PostgreSQL database is accessible

### Phase 1: Dockerfile Creation
- Create `Phase-IV/docker/backend.Dockerfile` (using Gordon or manual)
- Create `Phase-IV/docker/frontend.Dockerfile` (using Gordon or manual)
- Test builds: `docker build -f docker/backend.Dockerfile -t taskflow-backend:1.0.0 ./Phase-II/backend`
- Test builds: `docker build -f docker/frontend.Dockerfile -t taskflow-frontend:1.0.0 ./Phase-II/frontend`

### Phase 2: Helm Chart Scaffold
- Create `Phase-IV/helm/taskflow/` directory structure
- Create `Chart.yaml` with metadata
- Create `values.yaml` with default values (NO secrets)
- Create `templates/_helpers.tpl` with label templates

### Phase 3: Backend Kubernetes Resources
- Create `templates/backend-deployment.yaml`
  - Replicas: 1
  - Image: `taskflow-backend:1.0.0`
  - Container port: 8000
  - Liveness probe: `/health`
  - Readiness probe: `/health`
  - Resources: 256Mi/250m requests, 512Mi/500m limits
- Create `templates/backend-service.yaml`
  - Type: ClusterIP
  - Port: 8000
- Create `templates/backend-configmap.yaml`
  - Non-sensitive environment variables
- Create `templates/backend-secrets.yaml`
  - DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY (from values)

### Phase 4: Frontend Kubernetes Resources
- Create `templates/frontend-deployment.yaml`
  - Replicas: 1
  - Image: `taskflow-frontend:1.0.0`
  - Container port: 3000
  - Init container: wait for backend readiness
  - Liveness probe: `/` (homepage)
  - Readiness probe: `/`
  - Resources: 128Mi/250m requests, 256Mi/500m limits
- Create `templates/frontend-service.yaml`
  - Type: NodePort
  - Port: 3000
- Create `templates/frontend-configmap.yaml`
  - NEXT_PUBLIC_API_URL=http://taskflow-backend-service:8000
- Create `templates/frontend-secrets.yaml`
  - BETTER_AUTH_SECRET (same as backend)

### Phase 5: Helm Values Configuration
- Create `values.yaml` with all configurable parameters
- Create `values-local.yaml` for local development overrides
- Document required secrets in `helm/taskflow/README.md`

### Phase 6: Pre-Deployment Testing
- Run `helm lint ./helm/taskflow`
- Run `helm template ./helm/taskflow` to preview manifests
- Validate no hardcoded secrets in templates
- Check image pull policy (IfNotPresent for local images)

### Phase 7: Deployment Execution
- Load images into Minikube: `minikube image load taskflow-backend:1.0.0`
- Load images into Minikube: `minikube image load taskflow-frontend:1.0.0`
- Deploy: `helm install taskflow ./helm/taskflow -f values-local.yaml`
- Watch pods: `kubectl get pods -w`

### Phase 8: Validation
- Check pod status (Running, 1/1 Ready)
- Test backend health: `kubectl exec <backend-pod> -- curl http://localhost:8000/health`
- Get frontend NodePort: `kubectl get service taskflow-frontend-service`
- Access frontend: `http://$(minikube ip):<nodeport>`
- Run end-to-end test (signup → task creation → chatbot)

---

## Re-Check Constitution After Phase 1

*GATE: Verify no violations introduced during design*

### ✅ Immutability of Working Systems
- **Status**: PASS
- **Evidence**: No application code modified, only infrastructure created

### ✅ Canonical Reference Authority
- **Status**: PASS
- **Evidence**: api-contracts.md documents production behavior as ground truth

### ✅ Infrastructure Adaptation Principle
- **Status**: PASS
- **Evidence**: Ports 8000/3000 preserved, routes preserved, no app changes

### ✅ Tool Constraints
- **Status**: PASS
- **Evidence**: Plan uses Docker, Minikube, Helm exclusively

### ✅ Safety Over Completion
- **Status**: PASS
- **Evidence**: 6 checkpoints defined with rollback procedures

### ✅ Zero Application Modification
- **Status**: PASS
- **Evidence**: All Phase IV artifacts are infrastructure-only

**Final Gate Result**: ✅ ALL CHECKS PASS - Ready for `/sp.tasks`

---

## Next Steps

1. Run `/sp.tasks` to generate implementation tasks from this plan
2. Tasks will break down Helm chart creation, Dockerfile creation, deployment steps
3. Execute tasks in dependency order (backend-first)
4. Validate at each checkpoint
5. Document any issues encountered and resolutions

---

## Summary

This plan provides a comprehensive deployment strategy for Phase IV Local Kubernetes Deployment:
- Research-backed best practices for Docker and Kubernetes
- Data model and API contract documentation (IMMUTABLE)
- Safe containerization approach (no code changes)
- Backend-first deployment with validation checkpoints
- Failure handling and rollback procedures
- Compliance with all constitutional principles

The plan is ready for task generation (`/sp.tasks`) and subsequent implementation.

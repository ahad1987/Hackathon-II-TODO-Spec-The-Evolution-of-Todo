# Tasks: Phase IV Local Kubernetes Deployment

**Input**: Design documents from `/specs/001-k8s-deployment/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api-contracts.md

**Tests**: NOT REQUESTED - This is a deployment project. Validation is manual testing against production.

**Organization**: Tasks are grouped by deployment workflow phases (setup → contract verification → containerization → orchestration → deployment → validation).

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 0: Live Contract Extraction & Freeze

**Purpose**: Capture production API contracts as IMMUTABLE references before any deployment work

- [ ] T001 [P] Extract frontend API calls from production Vercel deployment by inspecting browser network tab, documenting all endpoint URLs, headers (Authorization bearer tokens), request/response payloads for signup, login, task operations, and chatbot interactions
- [ ] T002 [P] Extract backend API routes from production HuggingFace deployment by accessing API documentation at /docs endpoint (FastAPI auto-docs), recording all route paths, HTTP methods, expected status codes, and response schemas
- [ ] T003 [P] Document production port configurations by examining Phase-II/backend/src/main.py (backend port 8000) and Phase-II/frontend configuration (frontend port 3000)
- [ ] T004 [P] Document production base paths by recording backend API prefix (/api/v1) from Phase-II/backend/src/config.py and frontend base URL patterns
- [ ] T005 Freeze immutable contracts by creating contracts-freeze.md document listing all 11 API endpoints with exact paths, methods, ports, and response structures marked as IMMUTABLE per Constitutional mandate

**Validation**: Contracts-freeze.md contains all 11 API endpoints from api-contracts.md with IMMUTABLE designation

**Failure Condition**: Missing any production API endpoint, incorrect port numbers, or ambiguous route paths triggers STOP

---

## Phase 1: Setup & Prerequisites

**Purpose**: Initialize project infrastructure and verify tooling availability

- [ ] T006 Create Phase-IV directory structure by making directories Phase-IV/docker/ and Phase-IV/helm/ for infrastructure artifacts
- [ ] T007 [P] Verify Docker Desktop installation by checking docker version output shows Docker Engine running
- [ ] T008 [P] Verify Minikube installation by checking minikube version output shows v1.28 or later
- [ ] T009 [P] Verify Helm installation by checking helm version output shows v3.x
- [ ] T010 [P] Verify kubectl installation by checking kubectl version --client output shows client version
- [ ] T011 Start Minikube cluster with resource allocation of 4 CPUs and 8GB RAM using minikube start command
- [ ] T012 Verify Minikube is running by checking minikube status shows host, kubelet, and apiserver as Running

**Checkpoint**: All prerequisite tools verified and Minikube cluster running

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prepare environment secrets and validate database connectivity before ANY deployment

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T013 Create secrets.env file template in Phase-IV/ with placeholders for DATABASE_URL, BETTER_AUTH_SECRET (minimum 32 characters), ANTHROPIC_API_KEY, and CORS_ORIGINS
- [ ] T014 Validate BETTER_AUTH_SECRET length by checking it contains at least 32 characters per config.py requirement from Phase-II/backend/src/config.py:78
- [ ] T015 Test PostgreSQL database connectivity by attempting connection using DATABASE_URL value to ensure database is accessible before deployment
- [ ] T016 Document Minikube IP address by running minikube ip command and recording for CORS configuration

**Checkpoint**: Foundation ready - secrets prepared, database accessible, Minikube IP known

---

## Phase 3: User Story 1 - Local Deployment Setup (Priority: P1) 🎯 MVP

**Goal**: Deploy frontend + backend to Minikube with identical behavior to production

**Independent Test**: Access frontend via Minikube NodePort, test signup → task creation → chatbot interaction, compare responses with production

### Containerization

- [ ] T017 [P] [US1] Create backend Dockerfile at Phase-IV/docker/backend.Dockerfile using python:3.11-slim base image (Debian for psycopg2 wheels per research.md), multi-stage build pattern, copying requirements.txt first for layer caching, installing dependencies with pip --no-cache-dir, copying Phase-II/backend/src/ AS-IS (immutable), exposing port 8000, running as non-root user, CMD fastapi run
- [ ] T018 [P] [US1] Create frontend Dockerfile at Phase-IV/docker/frontend.Dockerfile using node:18-alpine base image, 3-stage build (dependencies → builder → runner), enabling standalone mode if not already set in next.config.js, copying .next/standalone output, exposing port 3000, running as non-root user, CMD node server.js
- [ ] T019 [US1] Build backend Docker image by running docker build command with context Phase-II/backend/, tagging as taskflow-backend:1.0.0 and taskflow-backend:latest
- [ ] T020 [US1] Build frontend Docker image by running docker build command with context Phase-II/frontend/, tagging as taskflow-frontend:1.0.0 and taskflow-frontend:latest
- [ ] T021 [P] [US1] Load backend image into Minikube by running minikube image load taskflow-backend:1.0.0
- [ ] T022 [P] [US1] Load frontend image into Minikube by running minikube image load taskflow-frontend:1.0.0

### Helm Chart Structure

- [ ] T023 [US1] Create Helm chart directory structure at Phase-IV/helm/taskflow/ with subdirectories for templates/
- [ ] T024 [US1] Create Chart.yaml at Phase-IV/helm/taskflow/Chart.yaml with apiVersion v2, name taskflow, description, version 1.0.0, appVersion 1.0.0
- [ ] T025 [US1] Create values.yaml at Phase-IV/helm/taskflow/values.yaml with default configuration for images (tags, pull policy IfNotPresent), replicas (1), resources (backend 256Mi/250m requests, 512Mi/500m limits; frontend 128Mi/250m requests, 256Mi/500m limits), ports (backend 8000, frontend 3000)
- [ ] T026 [US1] Create _helpers.tpl at Phase-IV/helm/taskflow/templates/_helpers.tpl with label templates for app taskflow, component backend/frontend selectors

### Backend Kubernetes Resources

- [ ] T027 [US1] Create backend ConfigMap template at Phase-IV/helm/taskflow/templates/backend-configmap.yaml defining non-sensitive environment variables API_PREFIX=/api/v1, API_TITLE=Todo API, API_VERSION=0.1.0, ENVIRONMENT=development, DEBUG=False, JWT_ALGORITHM=HS256, JWT_EXPIRY=86400
- [ ] T028 [US1] Create backend Secrets template at Phase-IV/helm/taskflow/templates/backend-secrets.yaml defining sensitive values DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY, CORS_ORIGINS (from values.yaml)
- [ ] T029 [US1] Create backend Deployment template at Phase-IV/helm/taskflow/templates/backend-deployment.yaml with replicas 1, image taskflow-backend from values, container port 8000, liveness probe /health, readiness probe /health with initialDelaySeconds 30, resource requests/limits from values, envFrom referencing backend-configmap and backend-secrets
- [ ] T030 [US1] Create backend Service template at Phase-IV/helm/taskflow/templates/backend-service.yaml with type ClusterIP (internal-only), name taskflow-backend-service, port 8000 mapping to container port 8000, selector matching backend deployment labels

### Frontend Kubernetes Resources

- [ ] T031 [US1] Create frontend ConfigMap template at Phase-IV/helm/taskflow/templates/frontend-configmap.yaml defining NEXT_PUBLIC_API_URL=http://taskflow-backend-service:8000, NODE_ENV=production
- [ ] T032 [US1] Create frontend Secrets template at Phase-IV/helm/taskflow/templates/frontend-secrets.yaml defining BETTER_AUTH_SECRET matching backend secret, BETTER_AUTH_URL using Minikube IP and NodePort
- [ ] T033 [US1] Create frontend init container specification in frontend-deployment.yaml that waits for backend Service by performing nslookup taskflow-backend-service and curl http://taskflow-backend-service:8000/health with retries
- [ ] T034 [US1] Create frontend Deployment template at Phase-IV/helm/taskflow/templates/frontend-deployment.yaml with replicas 1, image taskflow-frontend from values, init container from T033, container port 3000, liveness probe /, readiness probe / with initialDelaySeconds 30, resource requests/limits from values, envFrom referencing frontend-configmap and frontend-secrets
- [ ] T035 [US1] Create frontend Service template at Phase-IV/helm/taskflow/templates/frontend-service.yaml with type NodePort (external access), name taskflow-frontend-service, port 3000 mapping to container port 3000, selector matching frontend deployment labels

### Pre-Deployment Validation

- [ ] T036 [US1] Run helm lint on Phase-IV/helm/taskflow/ chart to validate template syntax and structure with no errors
- [ ] T037 [US1] Run helm template command on Phase-IV/helm/taskflow/ to preview rendered Kubernetes manifests and verify no hardcoded secrets present
- [ ] T038 [US1] Verify git status shows no changes in Phase-II/backend/src/ and Phase-II/frontend/src/ directories confirming application code immutability

### Backend Deployment & Validation

- [ ] T039 [US1] Create values-local.yaml at Phase-IV/helm/ with secret overrides from secrets.env (DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY, CORS_ORIGINS including Minikube IP)
- [ ] T040 [US1] Deploy Helm chart by running helm install taskflow Phase-IV/helm/taskflow/ -f Phase-IV/helm/values-local.yaml --wait --timeout 5m
- [ ] T041 [US1] Verify backend pod reaches Running state by checking kubectl get pods shows taskflow-backend-* with STATUS Running and READY 1/1 within 2 minutes
- [ ] T042 [US1] Verify backend health check by running kubectl exec on backend pod to curl http://localhost:8000/health expecting 200 OK response with status healthy
- [ ] T043 [US1] Verify backend API endpoint accessibility by running kubectl exec to curl http://localhost:8000/api/v1/auth/signup with test payload expecting 201 Created or 400 Bad Request (both indicate endpoint is functional)

**CHECKPOINT 1**: Backend deployment successful - pods Running, health check passing, API responding

### Frontend Deployment & Validation

- [ ] T044 [US1] Verify frontend pod reaches Running state by checking kubectl get pods shows taskflow-frontend-* with STATUS Running and READY 1/1 within 2 minutes
- [ ] T045 [US1] Get frontend NodePort by running kubectl get service taskflow-frontend-service and recording nodePort value from output
- [ ] T046 [US1] Access frontend in browser at http://\<minikube-ip\>:\<nodeport\> and verify TaskFlow UI loads without JavaScript console errors
- [ ] T047 [US1] Verify frontend can resolve backend DNS by checking kubectl logs on frontend pod for successful API calls to taskflow-backend-service (no DNS resolution errors)

**CHECKPOINT 2**: Frontend deployment successful - pods Running, UI accessible, backend connectivity established

### End-to-End Validation

- [ ] T048 [US1] Test user signup flow by creating new account through frontend UI and verifying 201 Created response in browser network tab
- [ ] T049 [US1] Test user login flow by authenticating with created credentials and verifying JWT token is returned and stored
- [ ] T050 [US1] Test task creation by adding task through frontend UI and verifying task appears in task list with correct title and description
- [ ] T051 [US1] Test task retrieval by refreshing page and verifying previously created task persists from database
- [ ] T052 [US1] Test task update by modifying task title and verifying change persists after page refresh
- [ ] T053 [US1] Test task completion by marking task as completed and verifying completed status shows in UI
- [ ] T054 [US1] Test task deletion by removing task and verifying it no longer appears in task list
- [ ] T055 [US1] Test chatbot interaction by sending message "Hello" and verifying assistant responds without errors
- [ ] T056 [US1] Test chatbot tool execution by asking "Create a task to test deployment" and verifying new task appears in task list demonstrating add_task MCP tool works

**CHECKPOINT 3**: End-to-end workflow validated - all operations match production behavior

---

## Phase 4: User Story 2 - Environment Configuration Management (Priority: P2)

**Goal**: Verify environment variables are correctly injected and match production requirements

**Independent Test**: Check pod environment variables, test database connectivity, validate JWT generation

- [ ] T057 [US2] Verify backend environment variables by running kubectl exec on backend pod to printenv and confirming all required variables present (DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY, CORS_ORIGINS, API_PREFIX, ENVIRONMENT, DEBUG)
- [ ] T058 [US2] Verify frontend environment variables by running kubectl exec on frontend pod to printenv and confirming NEXT_PUBLIC_API_URL=http://taskflow-backend-service:8000, BETTER_AUTH_SECRET matches backend
- [ ] T059 [US2] Test database connectivity from backend pod by checking kubectl logs for successful PostgreSQL connection message on startup
- [ ] T060 [US2] Validate JWT token generation by logging in and decoding token to verify it contains user_id (sub claim), email, exp (expiry), and iat (issued at) fields
- [ ] T061 [US2] Verify CORS configuration allows Minikube frontend by checking browser network tab shows no CORS errors when making API calls from frontend to backend

**Checkpoint**: Environment configuration validated - all variables present, database connected, JWT working, CORS passing

---

## Phase 5: User Story 3 - Service Discovery and Internal Communication (Priority: P3)

**Goal**: Validate Kubernetes DNS-based service discovery works correctly

**Independent Test**: Verify frontend resolves backend DNS, test API calls succeed, check load balancing (if multiple replicas)

- [ ] T062 [US3] Verify backend Service DNS resolution by running kubectl exec on frontend pod to nslookup taskflow-backend-service expecting successful resolution to ClusterIP
- [ ] T063 [US3] Verify backend Service reachability by running kubectl exec on frontend pod to curl http://taskflow-backend-service:8000/health expecting 200 OK response
- [ ] T064 [US3] Measure API latency by timing frontend-to-backend API calls in browser network tab and confirming response times under 100ms (local network)
- [ ] T065 [US3] Test backend scaling by running kubectl scale deployment taskflow-backend --replicas=2 and verifying both pods reach Running state
- [ ] T066 [US3] Verify load balancing across backend replicas by making multiple API calls and checking kubectl logs on both backend pods show distributed request handling
- [ ] T067 [US3] Scale backend back to 1 replica by running kubectl scale deployment taskflow-backend --replicas=1 for consistent state

**Checkpoint**: Service discovery validated - DNS works, API calls succeed, load balancing functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validations and documentation updates

- [ ] T068 [P] Document deployment by creating Phase-IV/DEPLOYMENT.md with step-by-step instructions, prerequisites checklist, common issues and solutions from quickstart.md
- [ ] T069 [P] Create rollback procedure document at Phase-IV/ROLLBACK.md with helm rollback commands, troubleshooting steps, and failure investigation checklist
- [ ] T070 [P] Update Phase-IV/README.md with project overview, directory structure explanation, and links to deployment and rollback docs
- [ ] T071 Validate all tasks completed by reviewing this tasks.md file and confirming all checkboxes are marked with [x]
- [ ] T072 Compare deployed system with production by running parallel tests against Vercel frontend and HuggingFace backend to confirm identical behavior per Constitutional mandate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - Core deployment
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) - Validates configuration of deployed system
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 3) - Validates networking of deployed system
- **Polish (Phase 6)**: Depends on all user stories (Phases 3, 4, 5) complete

### User Story Dependencies

- **User Story 1 (P1)**: Core deployment - no dependencies on other stories
- **User Story 2 (P2)**: Validates User Story 1 deployment - depends on US1
- **User Story 3 (P3)**: Validates User Story 1 networking - depends on US1

### Within Each User Story

**User Story 1 Sequence**:
1. Containerization (T017-T022): Build and load images FIRST
2. Helm Chart Structure (T023-T026): Create chart scaffold
3. Backend Resources (T027-T030): Define backend Kubernetes resources
4. Frontend Resources (T031-T035): Define frontend Kubernetes resources (includes init container dependency on backend)
5. Pre-Deployment Validation (T036-T038): Validate before deploying
6. Backend Deployment (T039-T043): Deploy and validate backend BEFORE frontend
7. Frontend Deployment (T044-T047): Deploy frontend ONLY after backend validated
8. End-to-End Validation (T048-T056): Test full workflow

**User Story 2 Sequence**:
- All tasks (T057-T061) validate deployed system - can run in sequence or parallel

**User Story 3 Sequence**:
- T062-T064: Basic DNS and connectivity tests
- T065-T067: Scaling and load balancing tests (sequential)

### Parallel Opportunities

- **Phase 0**: T001, T002, T003, T004 can run in parallel (independent contract extraction)
- **Phase 1**: T007, T008, T009, T010 can run in parallel (independent tool checks)
- **Phase 2**: T013 and T016 can run in parallel (secret prep and Minikube IP)
- **User Story 1 Containerization**: T017 and T018 can run in parallel (different Dockerfiles)
- **User Story 1 Containerization**: T021 and T022 can run in parallel (independent image loads)
- **User Story 1 Helm**: T027-T035 backend and frontend resources can be created in parallel (different files)
- **User Story 1 Pre-Deploy**: T036, T037, T038 can run in parallel (independent validations)
- **Phase 6**: T068, T069, T070 can run in parallel (different documentation files)

---

## Parallel Example: User Story 1 Containerization

**Launch together** (different files, no dependencies):
```
- Task T017: Create backend Dockerfile
- Task T018: Create frontend Dockerfile
```

**Then build sequentially** (depend on Dockerfiles):
```
- Task T019: Build backend image
- Task T020: Build frontend image
```

**Then load in parallel** (independent):
```
- Task T021: Load backend image to Minikube
- Task T022: Load frontend image to Minikube
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Live Contract Extraction (T001-T005)
2. Complete Phase 1: Setup (T006-T012)
3. Complete Phase 2: Foundational (T013-T016) - **CRITICAL BLOCKING PHASE**
4. Complete Phase 3: User Story 1 (T017-T056) - Full deployment
5. **STOP and VALIDATE**: Test entire workflow end-to-end
6. If successful: Proceed to User Story 2 for deeper validation
7. If failed: Rollback using helm rollback, investigate, fix, retry

### Incremental Delivery

1. Complete Setup + Foundational (Phases 0, 1, 2) → Foundation ready
2. Add User Story 1 (Phase 3) → Test independently → MVP deployed!
3. Add User Story 2 (Phase 4) → Validate environment configuration
4. Add User Story 3 (Phase 5) → Validate service networking
5. Complete Polish (Phase 6) → Documentation complete

### Failure Handling

**At any checkpoint, if validation fails**:
1. **STOP immediately** - do NOT proceed to next phase
2. **Document failure**: Capture screenshots, logs (kubectl logs), pod events (kubectl describe pod)
3. **Investigate root cause**: Check environment variables, database connectivity, CORS config, image builds
4. **Rollback**: Execute `helm rollback taskflow` or `helm uninstall taskflow` if needed
5. **Fix issue**: Update Helm values, rebuild images, or correct configuration
6. **Retry from failed checkpoint**: Re-run validation before proceeding

**NEVER**:
- Guess at fixes without understanding root cause
- Modify application code to workaround deployment issues (Constitutional violation)
- Skip checkpoints to save time
- Proceed with partial deployment (e.g., backend works but frontend doesn't)

---

## Notes

- All tasks are infrastructure-only - NO application code modifications permitted
- Git status MUST remain clean for Phase-II/backend/src/ and Phase-II/frontend/src/ throughout
- Canonical production deployments (Vercel, HuggingFace) define CORRECT behavior
- Any deviation from production triggers rollback per Constitutional mandate
- Use kubectl-ai and kagent for AI-assisted operations where available (optional)
- All validation is manual testing against production - no automated test frameworks in scope

**Total Tasks**: 72
- Phase 0 (Contract Extraction): 5 tasks
- Phase 1 (Setup): 7 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (User Story 1 - Deployment): 40 tasks
- Phase 4 (User Story 2 - Environment): 5 tasks
- Phase 5 (User Story 3 - Networking): 6 tasks
- Phase 6 (Polish): 5 tasks

**Parallel Opportunities**: 15 tasks can run in parallel across different phases

**MVP Scope**: Phases 0, 1, 2, 3 (56 tasks) deliver fully functional local Kubernetes deployment

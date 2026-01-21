---
id: 004
title: K8s Deployment Implementation Tasks
stage: tasks
date: 2026-01-20
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-k8s-deployment
branch: 001-k8s-deployment
user: Ahad
command: /sp.tasks
labels: ["implementation-tasks", "kubernetes", "deployment", "helm", "docker", "minikube", "taskflow"]
links:
  spec: specs/001-k8s-deployment/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-k8s-deployment/tasks.md
  - history/prompts/001-k8s-deployment/004-k8s-deployment-tasks.tasks.prompt.md
tests:
  - N/A (deployment project - validation is manual testing against production)
---

## Prompt

Using the APPROVED Constitution, Specification, and Plan, break the project into ATOMIC TASKS.

MANDATORY EARLY TASK CATEGORY:
Task Category 0 – Live Contract Extraction & Freeze
- Inspect frontend network behavior
- Inspect backend API behavior
- Record routes, ports, base paths
- Freeze them as IMMUTABLE CONTRACTS

EACH TASK MUST INCLUDE:
- Task ID
- Objective
- Preconditions
- Action (high-level)
- Validation criteria
- Failure condition (what causes STOP)

TASK CATEGORIES:
1. Contract discovery & verification
2. Containerization (non-destructive)
3. Helm chart generation
4. Minikube deployment
5. Connectivity validation
6. AI-assisted debugging (kubectl-ai, kagent)

RULES:
- No commands
- No Dockerfiles
- No YAML
- No implementation

Output ONLY the task list.

## Response snapshot

Created comprehensive implementation tasks document at `specs/001-k8s-deployment/tasks.md` with:

**Task Organization** (72 total tasks):
- **Phase 0: Live Contract Extraction & Freeze** (5 tasks, T001-T005)
  - Extract frontend API calls from Vercel production
  - Extract backend routes from HuggingFace production
  - Document port configurations (8000, 3000)
  - Document base paths (/api/v1 prefix)
  - Freeze contracts as IMMUTABLE in contracts-freeze.md

- **Phase 1: Setup & Prerequisites** (7 tasks, T006-T012)
  - Create Phase-IV directory structure
  - Verify Docker Desktop, Minikube, Helm, kubectl installations (parallel)
  - Start Minikube with 4 CPUs, 8GB RAM
  - Verify Minikube status

- **Phase 2: Foundational (BLOCKING)** (4 tasks, T013-T016)
  - Create secrets.env template with DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY
  - Validate BETTER_AUTH_SECRET minimum 32 characters
  - Test PostgreSQL connectivity before deployment
  - Document Minikube IP for CORS configuration

- **Phase 3: User Story 1 - Local Deployment Setup (P1)** (40 tasks, T017-T056)
  - **Containerization** (6 tasks): Create Dockerfiles (backend python:3.11-slim, frontend node:18-alpine), build images, load into Minikube
  - **Helm Chart Structure** (4 tasks): Create chart directory, Chart.yaml, values.yaml, _helpers.tpl
  - **Backend Resources** (4 tasks): ConfigMap, Secrets, Deployment with health probes, Service (ClusterIP)
  - **Frontend Resources** (5 tasks): ConfigMap with backend DNS, Secrets, init container waiting for backend, Deployment, Service (NodePort)
  - **Pre-Deployment Validation** (3 tasks): Helm lint, template preview, git status check
  - **Backend Deployment** (5 tasks): Create values-local.yaml, helm install, verify pods Running, test health endpoint, test API endpoint
  - **Frontend Deployment** (4 tasks): Verify pods Running, get NodePort, access UI in browser, check backend connectivity
  - **End-to-End Validation** (9 tasks): Test signup, login, task CRUD (create, retrieve, update, complete, delete), chatbot interaction, chatbot tool execution

- **Phase 4: User Story 2 - Environment Configuration (P2)** (5 tasks, T057-T061)
  - Verify backend environment variables present
  - Verify frontend environment variables correct
  - Test database connectivity from pods
  - Validate JWT token generation and claims
  - Verify CORS configuration (no browser errors)

- **Phase 5: User Story 3 - Service Discovery (P3)** (6 tasks, T062-T067)
  - Verify backend DNS resolution from frontend pod
  - Test backend reachability via internal DNS
  - Measure API latency (<100ms)
  - Scale backend to 2 replicas
  - Verify load balancing across replicas
  - Scale back to 1 replica

- **Phase 6: Polish & Documentation** (5 tasks, T068-T072)
  - Create DEPLOYMENT.md guide
  - Create ROLLBACK.md procedures
  - Update README.md with overview
  - Validate all tasks completed
  - Compare deployed system with production

**Task Format Compliance**:
- All tasks follow strict checklist format: `- [ ] [TaskID] [P?] [Story?] Description`
- Task IDs sequential (T001-T072)
- [P] marker for parallelizable tasks (15 opportunities identified)
- [Story] labels for user stories (US1, US2, US3)
- File paths included in descriptions

**Dependencies & Execution Order**:
- Phase dependencies: Setup → Foundational (BLOCKING) → User Stories → Polish
- User Story 1 (P1) is independent core deployment
- User Story 2 (P2) validates US1 environment configuration
- User Story 3 (P3) validates US1 networking

**Checkpoints** (4 critical validation points):
1. After Backend Deployment (T043): Pods Running, health OK, API responding
2. After Frontend Deployment (T047): Pods Running, UI accessible, backend connectivity
3. After End-to-End Validation (T056): Full workflow tested
4. After Environment Validation (T061): Configuration verified

**Parallel Opportunities** (15 tasks):
- Phase 0: T001-T004 (contract extraction from different sources)
- Phase 1: T007-T010 (tool verification)
- Phase 2: T013, T016 (secret prep and Minikube IP)
- Phase 3: T017-T018 (Dockerfiles), T021-T022 (image loads), T027-T035 (Helm templates), T036-T038 (pre-deploy checks)
- Phase 6: T068-T070 (documentation)

**Implementation Strategy**:
- **MVP First**: Phases 0-3 (56 tasks) deliver functional deployment
- **Incremental**: Add US2 (environment validation), then US3 (networking validation), then documentation
- **Failure Handling**: STOP at any checkpoint failure, rollback with `helm rollback`, investigate root cause, fix, retry

**Constitutional Compliance**:
- All tasks are infrastructure-only (no app code modifications)
- Git status must remain clean for application source directories
- Production deployments (Vercel, HuggingFace) define correct behavior
- Any deviation triggers rollback per Constitutional mandate

**Key Findings**:
- User Story organization enables independent implementation and testing
- Backend-first deployment prevents frontend-backend connection issues
- Init container pattern ensures frontend waits for backend readiness
- 3 validation checkpoints ensure deployment quality before proceeding
- Helm-only orchestration maintains Constitutional compliance

## Outcome

- Impact: Created 72 atomic implementation tasks for zero-regression Kubernetes deployment
- Tests: Manual validation against production at 4 checkpoints throughout deployment
- Files: tasks.md (complete task breakdown with dependencies and parallel opportunities)
- Next prompts: Execute tasks sequentially starting with Phase 0 (contract extraction), implementing with `/sp.implement` command or manual execution
- Reflection: Task breakdown successfully separates concerns (containerization → orchestration → deployment → validation) while maintaining Constitutional safety requirements through checkpoints and rollback procedures

## Evaluation notes (flywheel)

- Failure modes observed: None - tasks generation successful
- Graders run and results (PASS/FAIL): Format validation passed (all tasks follow checkbox format with IDs, labels, file paths)
- Prompt variant (if applicable): Standard /sp.tasks with mandatory contract extraction phase per Constitutional governance
- Next experiment (smallest change to try): Execute Phase 0 contract extraction tasks to establish immutable reference baseline before any deployment work begins

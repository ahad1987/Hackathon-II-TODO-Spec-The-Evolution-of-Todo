---
id: 003
title: K8s Deployment Implementation Plan
stage: plan
date: 2026-01-20
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-k8s-deployment
branch: 001-k8s-deployment
user: Ahad
command: /sp.plan
labels: ["implementation-plan", "kubernetes", "deployment", "helm", "docker", "minikube"]
links:
  spec: specs/001-k8s-deployment/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-k8s-deployment/plan.md
  - specs/001-k8s-deployment/research.md
  - specs/001-k8s-deployment/data-model.md
  - specs/001-k8s-deployment/contracts/api-contracts.md
  - specs/001-k8s-deployment/quickstart.md
  - history/prompts/001-k8s-deployment/003-k8s-deployment-plan.plan.prompt.md
tests:
  - N/A (planning document, implementation tests will be defined in tasks phase)
---

## Prompt

Using the APPROVED Constitution and Specification, generate a DEPLOYMENT PLAN.

PLAN GOALS:
- Zero regression
- Zero API mismatch
- Zero routing errors
- Zero frontend/backend disconnect

PLAN MUST INCLUDE:
1. Live-contract verification strategy
2. Safe containerization approach (no code changes)
3. Image build & tagging strategy
4. Helm chart strategy (preserving ports & routes)
5. Backend-first deployment order
6. Internal service exposure strategy
7. Frontend exposure ONLY after backend validation
8. AI-assisted operations strategy (kubectl-ai, kagent)
9. Failure checkpoints and rollback logic

CONSTRAINTS:
- No implementation
- No CLI commands
- No YAML
- No file contents

Output ONLY the Plan.

## Response snapshot

Created comprehensive implementation plan at `specs/001-k8s-deployment/plan.md` with:

**Phase 0: Research & Best Practices**
- Generated 480-line research document using general-purpose agent
- Documented 8 key findings (Docker base images, Helm architecture, service networking, configuration management, health probes, resource allocation, deployment ordering, CORS handling)
- 35+ authoritative sources from Kubernetes docs, FastAPI docs, Helm docs (2025-2026)
- Critical finding: Use `python:3.11-slim` NOT Alpine for FastAPI (psycopg2 wheel compatibility)

**Phase 1: Design & Contracts**
- `data-model.md`: Documented existing entities (User, Task, Conversation, Message) as IMMUTABLE, plus NEW Kubernetes entities (ConfigMaps, Secrets, Service discovery)
- `contracts/api-contracts.md`: Documented 11 API endpoints with exact request/response schemas, authentication mechanism (JWT), CORS configuration, error formats
- `quickstart.md`: 10-step deployment guide with verification checklist, rollback procedures, common issues and solutions

**Technical Context**:
- Multi-language: Node.js 18 (Next.js frontend), Python 3.11 (FastAPI backend)
- Infrastructure: Docker Desktop, Minikube, Helm 3.x, kubectl
- Storage: PostgreSQL (external to Kubernetes)
- Performance goals: Pod startup < 2min, health check < 100ms, API latency < 100ms
- Constraints: IMMUTABLE application code, Helm-only, Minikube-only, production API contracts preserved

**Constitution Check**: ✅ ALL 6 PRINCIPLES PASS (Immutability, Canonical Authority, Infrastructure Adaptation, Tool Constraints, Safety, Zero Modification)

**Project Structure**:
- Existing apps (Phase-II/backend, Phase-II/frontend) remain UNTOUCHED
- NEW infrastructure (Phase-IV/helm/taskflow/, Phase-IV/docker/) for deployment

**Deployment Strategy** (9 components as requested):

1. **Live-Contract Verification**:
   - Pre-deployment: Compare code routes with api-contracts.md, verify ports, validate env vars, check git status
   - Post-deployment: Compare API responses byte-for-byte with production, test auth flow, test task CRUD, test chatbot, verify frontend UI
   - Validation checkpoints at 6 stages

2. **Safe Containerization**:
   - Backend: `python:3.11-slim`, multi-stage if needed, copy requirements.txt first, install dependencies, copy app AS-IS, expose 8000, non-root user
   - Frontend: `node:18-alpine`, 3-stage build (dependencies → builder → runner), standalone mode, copy `.next/standalone`, expose 3000, non-root user
   - Safety: NO code mods, NO dependency updates, NO config changes

3. **Image Build & Tagging**:
   - Naming: `taskflow-backend:1.0.0`, `taskflow-frontend:1.0.0`
   - Versioning: SemVer (start 1.0.0, PATCH for fixes, MINOR for features, MAJOR for breaking)
   - Process: Gordon (Docker AI) preferred, fallback manual Dockerfiles, build locally, tag version + latest, load into Minikube

4. **Helm Chart Strategy**:
   - Single chart with multiple Deployments (not sub-charts)
   - Structure: Chart.yaml, values.yaml, templates/ (8 files: backend/frontend x deployment/service/configmap/secrets)
   - Port preservation: Backend 8000, Frontend 3000 (IMMUTABLE)
   - Route preservation: NO path rewriting, NO Ingress (using NodePort)

5. **Backend-First Deployment Order**:
   - Sequence: Backend ConfigMap → Secrets → Deployment → Service → CHECKPOINT → Frontend ConfigMap → Secrets → Deployment → Service
   - Dependency: Frontend init container waits for backend Service readiness
   - Helm orchestration: `--wait` flag blocks until resources ready

6. **Internal Service Exposure**:
   - Backend Service: ClusterIP (internal-only), port 8000, DNS `taskflow-backend-service`
   - Frontend config: `NEXT_PUBLIC_API_URL=http://taskflow-backend-service:8000`
   - Security: Backend NOT exposed externally

7. **Frontend Exposure After Backend Validation**:
   - Frontend Service: NodePort (external access), port 3000, auto-assigned NodePort 30000-32767
   - Validation sequence: Backend pods Running → health 200 OK → signup endpoint works → THEN deploy frontend
   - Failure handling: STOP if backend fails, investigate, fix, retry

8. **AI-Assisted Operations**:
   - Docker AI (Gordon): Dockerfile generation (fallback manual)
   - kubectl-ai: Kubernetes operations (scale, troubleshoot)
   - kagent: Cluster health monitoring, optimization
   - All AI tools OPTIONAL (plan works with standard tools)

9. **Failure Checkpoints & Rollback**:
   - Checkpoint 1 (Pre-Deployment): Git clean, images build, Helm lint, secrets prepared
   - Checkpoint 2 (Backend Deployment): Pods Running, readiness passes
   - Checkpoint 3 (Backend API): `/health` returns 200, `/api/v1/auth/signup` returns 201
   - Checkpoint 4 (Frontend Deployment): Pods Running, readiness passes
   - Checkpoint 5 (Integration): DNS resolves, CORS passes, UI loads
   - Checkpoint 6 (End-to-End): Signup, login, tasks, chatbot all work
   - Rollback: `helm rollback` or `helm uninstall`, document failure, investigate root cause, fix, re-deploy

**Implementation Phases Outlined** (8 phases):
0. Prerequisites & Environment Setup
1. Dockerfile Creation
2. Helm Chart Scaffold
3. Backend Kubernetes Resources
4. Frontend Kubernetes Resources
5. Helm Values Configuration
6. Pre-Deployment Testing
7. Deployment Execution
8. Validation

**Re-Check Constitution**: ✅ ALL 6 PRINCIPLES PASS (no violations after Phase 1 design)

## Outcome

- Impact: Created comprehensive deployment plan with zero-regression strategy for Phase IV Kubernetes deployment
- Tests: Validation strategy defined with 6 checkpoints and rollback procedures
- Files: plan.md (implementation plan), research.md (best practices), data-model.md (entities), api-contracts.md (11 endpoints), quickstart.md (deployment guide)
- Next prompts: `/sp.tasks` to generate implementation tasks breaking down Helm chart creation, Dockerfile creation, deployment steps
- Reflection: Plan successfully balances constitutional safety requirements (immutability, canonical authority) with practical Kubernetes deployment practices (health probes, resource limits, init containers)

## Evaluation notes (flywheel)

- Failure modes observed: None - planning successful with research agent completing all 8 topics
- Graders run and results (PASS/FAIL): Constitution Check passed all 6 principles (pre-Phase 0 and post-Phase 1)
- Prompt variant (if applicable): Standard /sp.plan with constitutional governance for deployment project
- Next experiment (smallest change to try): Execute `/sp.tasks` to break plan into actionable implementation tasks with dependency ordering

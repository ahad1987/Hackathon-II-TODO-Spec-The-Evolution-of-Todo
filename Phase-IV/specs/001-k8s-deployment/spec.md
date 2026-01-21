# Feature Specification: Phase IV Local Kubernetes Deployment

**Feature Branch**: `001-k8s-deployment`
**Created**: 2026-01-20
**Status**: Draft
**Input**: User description: "Phase IV – Local Kubernetes Deployment - Cloud Native Todo Chatbot (Basic Functionality)"

## User Scenarios & Testing

### User Story 1 - Local Deployment Setup (Priority: P1)

Deploy the TaskFlow AI Chatbot (frontend + backend) to local Kubernetes (Minikube) with identical behavior to production deployments on Vercel and HuggingFace.

**Why this priority**: This is the core requirement - establishing a working local Kubernetes deployment that exactly replicates production behavior.

**Independent Test**: The deployment can be fully tested by accessing the frontend via Minikube ingress/NodePort, creating tasks, using the AI chatbot, and comparing all responses against the canonical production deployments at https://taskflow-ai-chatbot.vercel.app/ and https://huggingface.co/spaces/Ahad-00/taskflow-ai-backend.

**Acceptance Scenarios**:

1. **Given** Phase-II (Todo Web App) and Phase-III (AI Chatbot) are working in production, **When** I deploy to Minikube using Helm, **Then** both frontend and backend containers start successfully and pass health checks
2. **Given** the Kubernetes deployment is running, **When** I access the frontend via the configured service endpoint, **Then** I see the TaskFlow interface identical to https://taskflow-ai-chatbot.vercel.app/
3. **Given** a user authenticates via the frontend, **When** the frontend calls backend API endpoints, **Then** all API routes respond identically to the HuggingFace backend deployment
4. **Given** the deployment is complete, **When** I create a task via the UI, **Then** the task is created, stored, and retrievable exactly as in production
5. **Given** the chatbot integration is deployed, **When** I send a message to the chatbot, **Then** the chatbot responds and can execute task operations (add, list, update, delete, complete) identically to production

---

### User Story 2 - Environment Configuration Management (Priority: P2)

Configure environment variables and secrets for local Kubernetes deployment matching production configuration requirements.

**Why this priority**: Without proper environment configuration, the application cannot connect to databases, authenticate users, or function correctly.

**Independent Test**: Verify environment variables are correctly injected into containers by checking application logs, testing database connectivity, and validating JWT token generation/validation works identically to production.

**Acceptance Scenarios**:

1. **Given** production uses specific environment variables, **When** I deploy to Kubernetes, **Then** all required environment variables are available to containers via ConfigMaps and Secrets
2. **Given** the backend requires DATABASE_URL, **When** the backend pod starts, **Then** it successfully connects to the database using the configured URL
3. **Given** authentication requires BETTER_AUTH_SECRET, **When** a user logs in, **Then** JWT tokens are generated and validated using the secret from Kubernetes Secrets
4. **Given** CORS is configured for specific origins, **When** the frontend makes API calls, **Then** CORS headers match production behavior

---

### User Story 3 - Service Discovery and Internal Communication (Priority: P3)

Establish Kubernetes service networking so frontend can discover and communicate with backend using internal DNS.

**Why this priority**: This enables the frontend to reach the backend within the cluster, critical for the application's client-server architecture.

**Independent Test**: Verify frontend can resolve backend service DNS names and successfully make API calls by checking network traces and API response logs.

**Acceptance Scenarios**:

1. **Given** frontend and backend are deployed as separate services, **When** the frontend needs to call the backend, **Then** it resolves the backend service via Kubernetes DNS (e.g., `backend-service.default.svc.cluster.local`)
2. **Given** the backend service is exposed internally on port 8000, **When** the frontend makes an API call, **Then** the request reaches the backend and returns the expected response
3. **Given** multiple backend replicas exist (if scaled), **When** the frontend makes requests, **Then** Kubernetes load balances requests across backend pods

---

### Edge Cases

- What happens when the backend database is not accessible during deployment?
  - Backend should start but log connection failures; health checks should fail gracefully
- What happens when invalid environment variables are provided?
  - Containers should fail to start with clear error messages in logs
- What happens when frontend cannot reach backend service?
  - Frontend should display connection errors consistent with production behavior
- What happens when JWT secrets differ between frontend and backend?
  - Authentication should fail with 401 errors, identical to production mismatch behavior
- What happens when Minikube runs out of resources?
  - Pods should enter pending or crash-loop states with resource constraint errors

## Requirements

### Functional Requirements

**Canonical Reference Preservation**
- **FR-001**: System MUST preserve exact API route paths from production (no path modifications)
- **FR-002**: System MUST preserve exact port configurations (backend port 8000, frontend port 3000)
- **FR-003**: System MUST preserve exact request/response schemas for all API endpoints
- **FR-004**: System MUST preserve authentication mechanism (JWT with Authorization header)
- **FR-005**: System MUST preserve CORS configuration matching production allowed origins

**Application Components (AS-IS)**
- **FR-006**: Frontend MUST be containerized without modifying any frontend code
- **FR-007**: Backend MUST be containerized without modifying any backend code
- **FR-008**: System MUST include Phase-II functionality: user authentication, task CRUD operations
- **FR-009**: System MUST include Phase-III functionality: AI chatbot integration with MCP tools

**Backend API Preservation**
- **FR-010**: Backend MUST expose `/health` endpoint returning status, version, environment
- **FR-011**: Backend MUST expose `/api/v1/auth/signup` (POST) for user registration
- **FR-012**: Backend MUST expose `/api/v1/auth/login` (POST) for user authentication
- **FR-013**: Backend MUST expose `/api/v1/auth/logout` (POST) for user logout
- **FR-014**: Backend MUST expose `/api/v1/auth/me` (GET) for retrieving current user info
- **FR-015**: Backend MUST expose `/api/v1/auth/refresh` (POST) for token refresh
- **FR-016**: Backend MUST expose `/api/v1/tasks` (GET) to list all user tasks
- **FR-017**: Backend MUST expose `/api/v1/tasks` (POST) to create a new task
- **FR-018**: Backend MUST expose `/api/v1/tasks/{task_id}` (PUT) to update a task
- **FR-019**: Backend MUST expose `/api/v1/tasks/{task_id}` (DELETE) to delete a task
- **FR-020**: Backend MUST expose `/api/v1/chat` (POST) for chatbot interactions

**Container Boundaries**
- **FR-021**: System MUST deploy frontend as a separate container
- **FR-022**: System MUST deploy backend as a separate container
- **FR-023**: Frontend container MUST be built from Next.js application (as-is)
- **FR-024**: Backend container MUST be built from FastAPI application (as-is)

**Kubernetes Service Mapping**
- **FR-025**: System MUST create a Kubernetes Service for frontend with stable endpoint
- **FR-026**: System MUST create a Kubernetes Service for backend with stable endpoint
- **FR-027**: System MUST expose frontend externally via NodePort or Ingress
- **FR-028**: Backend Service MUST be accessible to frontend via internal Kubernetes DNS

**Internal DNS/Service Naming**
- **FR-029**: Backend service MUST be discoverable via `backend-service` or `taskflow-backend-service` DNS name
- **FR-030**: Frontend MUST be configured to call backend using Kubernetes service DNS name

**Environment Variables**
- **FR-031**: Backend MUST receive `DATABASE_URL` environment variable for PostgreSQL connection
- **FR-032**: Backend MUST receive `BETTER_AUTH_SECRET` environment variable for JWT signing (minimum 32 characters)
- **FR-033**: Backend MUST receive `CORS_ORIGINS` environment variable matching allowed frontend origins
- **FR-034**: Backend MUST receive `ANTHROPIC_API_KEY` for AI chatbot functionality
- **FR-035**: Frontend MUST receive `NEXT_PUBLIC_API_URL` pointing to backend service endpoint
- **FR-036**: Frontend MUST receive `BETTER_AUTH_SECRET` matching backend secret
- **FR-037**: Frontend MUST receive `BETTER_AUTH_URL` for authentication callback URLs

**Deployment Target**
- **FR-038**: System MUST deploy to Minikube (local Kubernetes) ONLY
- **FR-039**: System MUST use Helm charts for deployment orchestration (no raw YAML)
- **FR-040**: System MUST use Docker Desktop for container builds
- **FR-041**: System MUST support AI-assisted operations via Gordon (Docker AI), kubectl-ai, kagent

**Observability & Validation**
- **FR-042**: System MUST implement health check endpoints for both frontend and backend
- **FR-043**: System MUST implement readiness probes to ensure containers are ready before receiving traffic
- **FR-044**: System MUST implement liveness probes to restart unhealthy containers
- **FR-045**: System MUST log all application errors consistently with production logging
- **FR-046**: System MUST expose logs via `kubectl logs` for debugging

### Key Entities

**Frontend Container**
- Next.js application (Phase-II + Phase-III integrated)
- Serves static assets and dynamic pages
- Communicates with backend via REST API
- Handles authentication state and JWT tokens
- Provides ChatWidget UI for AI interactions

**Backend Container**
- FastAPI application with async PostgreSQL support
- Exposes REST API endpoints for auth, tasks, and chat
- Validates JWT tokens via AuthenticationMiddleware
- Integrates with Anthropic Claude API for chatbot
- Uses MCP (Model Context Protocol) for task tool orchestration

**Database**
- PostgreSQL database (separate from Kubernetes - uses existing connection)
- Stores users, tasks, conversations, messages
- Accessed by backend via DATABASE_URL

**Kubernetes Services**
- `taskflow-frontend-service`: Exposes frontend pods externally
- `taskflow-backend-service`: Exposes backend pods internally to frontend

**ConfigMaps & Secrets**
- `taskflow-backend-config`: Non-sensitive backend environment variables
- `taskflow-backend-secrets`: Sensitive credentials (DATABASE_URL, BETTER_AUTH_SECRET, ANTHROPIC_API_KEY)
- `taskflow-frontend-config`: Frontend environment variables
- `taskflow-frontend-secrets`: Sensitive frontend credentials (BETTER_AUTH_SECRET)

## Success Criteria

### Measurable Outcomes

**Deployment Success**
- **SC-001**: Deployment completes successfully with `helm install` command completing without errors
- **SC-002**: All pods reach `Running` state within 2 minutes of deployment
- **SC-003**: Health checks pass for both frontend and backend within 30 seconds of pod startup

**Functional Equivalence to Production**
- **SC-004**: 100% of API endpoints return identical response structures to production HuggingFace backend
- **SC-005**: User authentication flow (signup, login, token validation) works identically to Vercel frontend
- **SC-006**: Task CRUD operations produce identical database records and API responses as production
- **SC-007**: Chatbot responses and tool executions match production behavior exactly

**Network and Service Discovery**
- **SC-008**: Frontend successfully resolves backend service DNS name in 100% of API calls
- **SC-009**: API call latency from frontend to backend is under 100ms (local network)
- **SC-010**: CORS validation passes for frontend-to-backend requests with no console errors

**Environment Configuration**
- **SC-011**: All required environment variables are present in container environments (verified via logs)
- **SC-012**: JWT tokens generated locally are valid and work for authenticated API calls
- **SC-013**: Database connectivity succeeds from backend container to PostgreSQL

**Observability and Reliability**
- **SC-014**: Application logs are accessible via `kubectl logs` commands with no missing log entries
- **SC-015**: Health check endpoints return `200 OK` consistently during normal operation
- **SC-016**: Readiness probes prevent traffic to pods that haven't completed initialization

**User Experience Parity**
- **SC-017**: Users can complete the full workflow (signup → create task → chatbot interaction) locally with identical UX to production
- **SC-018**: Page load times for frontend are under 2 seconds (comparable to Vercel)
- **SC-019**: No JavaScript console errors occur that aren't also present in production

## Non-Goals (Out of Scope)

- Cloud Kubernetes deployment (AWS EKS, Google GKE, Azure AKS)
- Horizontal pod autoscaling or advanced scaling strategies
- Persistent volume claims for stateful storage
- Ingress controller with TLS/SSL certificates
- Monitoring stack (Prometheus, Grafana)
- Service mesh (Istio, Linkerd)
- CI/CD pipeline integration
- Multi-environment configuration (staging, production)
- Database migrations or schema changes
- Performance optimization or code refactoring
- New features or bug fixes to application code
- API versioning or breaking changes

## Assumptions

1. **Database Availability**: PostgreSQL database is already running and accessible (either locally or remote) via DATABASE_URL
2. **Environment Secrets**: User will provide valid BETTER_AUTH_SECRET, ANTHROPIC_API_KEY, and DATABASE_URL values
3. **Docker Desktop**: Docker Desktop is installed and running on the host machine
4. **Minikube Installation**: Minikube is installed and initialized on the host machine
5. **Helm Installation**: Helm 3.x is installed and available in PATH
6. **Network Access**: Host machine can access external networks for pulling Docker base images
7. **Resource Availability**: Host machine has sufficient resources (minimum 4GB RAM, 2 CPU cores) for Minikube
8. **Production Stability**: Canonical production deployments remain stable and accessible for validation
9. **No Code Changes**: Phase-II and Phase-III application code is immutable and cannot be modified
10. **Local Development**: This deployment is intended for local development/testing, not production use

## Dependencies

**External Dependencies**
- Docker Desktop (container runtime)
- Minikube (local Kubernetes cluster)
- Helm 3.x (deployment orchestration)
- kubectl (Kubernetes CLI)
- PostgreSQL database (accessible via network)
- Anthropic Claude API (for chatbot functionality)

**Optional AI Tools**
- Docker AI Agent (Gordon) for Dockerfile generation
- kubectl-ai for Kubernetes operations
- kagent for cluster health monitoring

**Application Dependencies**
- Phase-II Frontend: Next.js application (Vercel deployment)
- Phase-II Backend: FastAPI application (HuggingFace deployment)
- Phase-III Chatbot Integration: MCP tools and Claude integration

## Risks & Constraints

**Constitutional Constraints**
- **IMMUTABILITY**: No modifications to Phase-II or Phase-III application code permitted
- **CANONICAL AUTHORITY**: Production deployments at Vercel and HuggingFace define correct behavior
- **INFRASTRUCTURE ADAPTATION**: Kubernetes must adapt to application requirements, not vice versa
- **SAFETY FIRST**: Any ambiguity or mismatch triggers immediate stop - no guessing permitted

**Technical Risks**
- **Risk**: Environment variable mismatch between containers causes authentication failures
  - **Mitigation**: Validate all environment variables against production configuration before deployment
- **Risk**: CORS configuration prevents frontend-backend communication
  - **Mitigation**: Ensure CORS_ORIGINS includes Minikube service endpoint
- **Risk**: Database connection fails due to network isolation
  - **Mitigation**: Test database connectivity before deploying backend pods
- **Risk**: Resource constraints on host machine cause pod crashes
  - **Mitigation**: Document minimum resource requirements and validate before deployment

**Operational Constraints**
- Minikube-only deployment (no cloud providers)
- Helm-only orchestration (no raw Kubernetes YAML)
- Local networking only (no external ingress beyond NodePort)
- Manual validation required (no automated regression tests in scope)

## Validation Approach

**Pre-Deployment Validation**
1. Verify Docker images build successfully without code modifications
2. Verify git status shows no changes in frontend/backend source directories
3. Verify Helm charts pass `helm lint` validation
4. Verify environment variables match production configuration

**Post-Deployment Validation**
1. Compare API responses from local backend against HuggingFace production backend
2. Verify frontend UI renders identically to Vercel production frontend
3. Execute full user workflow (signup → login → create task → chatbot interaction) and compare results
4. Verify authentication flows work identically (JWT generation, validation, expiry)
5. Verify chatbot tool calls (add_task, list_tasks, update_task, delete_task, complete_task) produce identical results

**Rollback Criteria**
- Any API endpoint returns different response structure than production
- Authentication behavior differs from production
- Frontend displays errors not present in production
- Backend health checks fail consistently
- Any violation of immutability principle (code changes detected)

## Feature Branch & Version

- **Branch Name**: `001-k8s-deployment`
- **Parent Branch**: `main`
- **Target Kubernetes Version**: Minikube with Kubernetes v1.28+ (latest stable)
- **Helm Chart Version**: 3.x compatible
- **Docker Base Images**:
  - Frontend: `node:18-alpine` (or as defined in existing Dockerfile)
  - Backend: `python:3.11-slim` (or as defined in existing Dockerfile)

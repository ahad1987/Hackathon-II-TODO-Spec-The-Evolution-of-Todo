# Phase IV Kubernetes Deployment Best Practices Research

**Date**: 2026-01-20
**Context**: Local Kubernetes deployment (Minikube) for Next.js frontend + FastAPI backend
**Constraint**: Application code is IMMUTABLE - best practices apply to containerization and deployment only

---

## Executive Summary

This document provides research-backed best practices for deploying a Next.js frontend and FastAPI backend to local Kubernetes (Minikube) using Helm charts. Each recommendation includes the decision, rationale, alternatives considered, and implementation guidance.

---

## 1. Dockerfile Best Practices for Next.js

### Decision: Use `node:18-alpine` with Multi-Stage Build and Standalone Output Mode

**Rationale:**
- **Alpine reduces image size**: Alpine Linux is lightweight and provides minimal attack surface
- **Multi-stage builds optimize production images**: Separate build stage from runtime stage, keeping final image lean
- **Standalone mode minimizes dependencies**: Next.js standalone output (`.next/standalone`) eliminates need for full `node_modules` in production
- **Production-ready**: Industry standard approach for Next.js deployments in 2026

**Alternatives Considered:**
1. **node:18-slim (Debian-based)**
   - Pros: Better compatibility with some npm packages, faster builds (no compilation)
   - Cons: Larger image size (~100MB vs ~40MB for Alpine)
   - When to use: If you encounter musl libc compatibility issues with native dependencies

2. **Single-stage build**
   - Pros: Simpler Dockerfile
   - Cons: Includes build dependencies in production, much larger image
   - Verdict: Not recommended for production

**Implementation Guidance:**
- Use 3-stage build: dependencies → builder → runner
- Enable standalone output in `next.config.js`: `output: 'standalone'`
- Copy only essential files to final stage: `.next/standalone`, `.next/static`, `public`
- Create `.dockerignore` to exclude: `node_modules`, `.git`, `.next` (except in builder), test files
- Run as non-root user for security
- Set `NODE_ENV=production` environment variable
- Working directory: `/app`

---

## 2. Dockerfile Best Practices for FastAPI (Python)

### Decision: Use `python:3.11-slim` (Debian-based) Over Alpine

**Rationale:**
- **Better wheel compatibility**: psycopg2, psycopg3 (async PostgreSQL drivers) have pre-built wheels for Debian
- **Avoid compilation overhead**: Alpine's musl libc requires compiling packages even when PyPI wheels exist
- **Faster builds**: No need to install build dependencies (gcc, postgresql-dev, musl-dev)
- **Production stability**: Debian-based images are the FastAPI official recommendation (2026)
- **Minimal size difference in practice**: After adding build dependencies to Alpine, size advantage disappears

**Alternatives Considered:**
1. **python:3.11-alpine**
   - Pros: Smallest base image (~50MB vs ~120MB for slim)
   - Cons:
     - Requires installing `apk add postgresql-dev musl-dev gcc zlib-dev` for psycopg2
     - Longer build times due to compilation
     - Potential runtime issues with C-extension libraries
   - When to use: Pure-Python apps with zero C-extension dependencies

2. **python:3.11 (full Debian)**
   - Pros: All system libraries included
   - Cons: Very large image (~900MB)
   - Verdict: Unnecessary bloat for containerized deployments

**Implementation Guidance:**
- Use multi-stage build if you have build-time-only dependencies (e.g., compilers)
- Copy `requirements.txt` first for layer caching optimization
- Use `pip install --no-cache-dir --upgrade` to avoid caching pip packages
- Specify exact Python version tag (e.g., `python:3.11.8-slim`) for reproducibility
- Run as non-root user
- Add `--proxy-headers` flag if behind load balancer/ingress
- Use `CMD ["fastapi", "run", "app/main.py", "--port", "8000"]` for production server

---

## 3. Helm Chart Structure for Multi-Container Application

### Decision: Single Helm Chart with Multiple Deployments (Not Sub-Charts)

**Rationale:**
- **Simpler for tightly-coupled services**: Frontend-backend in same application should deploy together
- **Shared configuration**: Both services share namespace, secrets, ConfigMaps
- **Single release lifecycle**: Deploy, upgrade, rollback as one unit
- **Easier dependency management**: Backend must be ready before frontend can connect
- **Better for Minikube**: Less overhead than managing parent chart + sub-charts

**Alternatives Considered:**
1. **Sub-Charts Approach (Parent + Backend + Frontend sub-charts)**
   - Pros: Maximum modularity, can version independently, reusable sub-charts
   - Cons: Over-engineered for single application, complex values.yaml hierarchy, harder to manage dependencies
   - When to use: Microservices with independent lifecycles, or sharing charts across teams

2. **Separate Helm Releases (Two independent charts)**
   - Pros: Fully independent deployments
   - Cons: Manual coordination required, no guaranteed deployment order, separate values files
   - Verdict: Not recommended for frontend-backend pair

**Implementation Guidance:**

**Directory Structure:**
```
helm-chart/
├── Chart.yaml                 # Chart metadata
├── values.yaml                # Default configuration values
├── templates/
│   ├── _helpers.tpl           # Template helpers
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── configmap.yaml         # Shared ConfigMap
│   ├── secret.yaml            # Shared Secrets
│   └── NOTES.txt              # Post-install instructions
└── .helmignore
```

**Chart.yaml Best Practices:**
- Use semantic versioning (SemVer 2.0.0): `MAJOR.MINOR.PATCH`
- Quote version strings: `version: "1.0.0"`
- Increment MAJOR for breaking changes, MINOR for features, PATCH for bug fixes
- `appVersion` tracks application version (informational, doesn't affect Helm)
- Include `description`, `maintainers`, `keywords`

**values.yaml Organization:**
```yaml
backend:
  replicaCount: 1
  image:
    repository: backend-image
    tag: latest
    pullPolicy: IfNotPresent
  service:
    type: ClusterIP
    port: 8000
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

frontend:
  replicaCount: 1
  image:
    repository: frontend-image
    tag: latest
    pullPolicy: IfNotPresent
  service:
    type: NodePort
    port: 3000
    nodePort: 30080
  resources:
    requests:
      memory: "128Mi"
      cpu: "250m"
    limits:
      memory: "256Mi"
      cpu: "500m"
```

**Template Patterns:**
- Use `{{ .Release.Name }}-backend` naming convention
- Use `{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}` for images
- Include labels: `app.kubernetes.io/name`, `app.kubernetes.io/instance`, `app.kubernetes.io/version`

---

## 4. Kubernetes Service Networking

### Decision: ClusterIP for Backend, NodePort for Frontend

**Rationale:**
- **ClusterIP for backend**: Internal-only service, not exposed outside cluster
  - Only frontend needs to communicate with backend
  - Automatic DNS: `backend-service.default.svc.cluster.local`
  - More secure (no external access)

- **NodePort for frontend**: External access for local development
  - Minikube doesn't have LoadBalancer support by default
  - Accessible via `minikube ip`:`<nodePort>`
  - Port range: 30000-32767

**Alternatives Considered:**
1. **NodePort for both services**
   - Pros: Both externally accessible for debugging
   - Cons: Exposes backend unnecessarily, reduces security
   - Verdict: Not recommended unless debugging backend directly

2. **Ingress Controller (NGINX Ingress)**
   - Pros: Production-like setup, path-based routing, SSL termination
   - Cons: Adds complexity for local dev, requires `minikube addons enable ingress`
   - When to use: For production-like local testing or multiple applications

3. **LoadBalancer type**
   - Pros: Production-standard approach
   - Cons: Requires `minikube tunnel` running in separate terminal
   - Verdict: Adds friction for local development

**Service Discovery Patterns:**

**DNS-Based Discovery (Recommended):**
- Frontend connects to backend via DNS: `http://backend-service:8000`
- Full FQDN: `http://backend-service.default.svc.cluster.local:8000`
- Works automatically within same namespace
- Kubernetes DNS resolves service name to ClusterIP

**Environment Variable Injection:**
- Inject backend URL as environment variable in frontend pod:
  ```yaml
  env:
    - name: NEXT_PUBLIC_API_URL
      value: "http://backend-service:8000"
  ```

**Implementation Guidance:**
- Backend service type: `ClusterIP` (default)
- Frontend service type: `NodePort` with `nodePort: 30080`
- Port naming convention: `name: http` for HTTP ports
- Use `targetPort` to match container port (e.g., `targetPort: 8000` for FastAPI)
- Selector must match deployment labels exactly

---

## 5. Environment Variable Management

### Decision: Use ConfigMaps for Non-Sensitive Data, Secrets for Credentials

**Rationale:**
- **Security separation**: Secrets are base64-encoded and can be encrypted at rest (etcd)
- **RBAC compatibility**: Different access policies for Secrets vs ConfigMaps
- **Clear intent**: Explicit distinction between config and secrets
- **Kubernetes best practice**: Industry standard approach

**Decision Criteria:**

**Use ConfigMaps for:**
- API endpoints (e.g., `BACKEND_URL`)
- Feature flags
- Port numbers
- Non-sensitive configuration

**Use Secrets for:**
- Database passwords
- API keys
- JWT secret keys
- OAuth client secrets
- Any credential or token

**Alternatives Considered:**
1. **All environment variables in Secrets**
   - Pros: Maximum security
   - Cons: Harder to debug, overkill for non-sensitive data
   - Verdict: Over-engineering

2. **All environment variables in ConfigMaps**
   - Pros: Simpler management
   - Cons: Insecure for credentials, fails security audits
   - Verdict: Security risk

3. **External secret management (HashiCorp Vault, AWS Secrets Manager)**
   - Pros: Enterprise-grade security, secret rotation
   - Cons: Overkill for local Minikube, adds external dependencies
   - When to use: Production environments with compliance requirements

**Implementation Guidance:**

**ConfigMap Creation:**
- Define in `templates/configmap.yaml`
- Reference in deployment: `envFrom: - configMapRef: name: app-config`
- Or individual variables: `env: - name: API_URL valueFrom: configMapKeyRef: ...`

**Secret Creation:**
- Define in `templates/secret.yaml`
- Values must be base64-encoded in YAML
- Reference similarly to ConfigMaps: `envFrom: - secretRef: name: app-secrets`

**Environment Variable Precedence:**
1. Container `env` (highest priority)
2. `envFrom` ConfigMap
3. `envFrom` Secret
4. Later entries override earlier ones

**Important Caveats:**
- **Pods cache environment variables**: Changes to ConfigMap/Secret require pod restart
- **Next.js NEXT_PUBLIC_ variables**: Baked in at build time (see Topic 1)
  - Server-side variables: Can use runtime ConfigMap/Secret injection
  - Client-side variables: Must use workarounds (entrypoint script or placeholder replacement)

---

## 6. Health Checks and Probes

### Decision: Implement All Three Probe Types (Startup, Liveness, Readiness)

**Rationale:**
- **Startup probes prevent premature kills**: Protect slow-starting applications (Next.js build, FastAPI imports)
- **Liveness probes detect deadlocks**: Restart containers stuck in unrecoverable state
- **Readiness probes manage traffic**: Only route requests to pods ready to handle them
- **Production reliability**: Kubernetes best practice for web applications

**Probe Configurations:**

### FastAPI Backend Probes

**Endpoints to Implement:**
- `/health/live` - Liveness probe (extremely lightweight)
- `/health/ready` - Readiness probe (checks database, dependencies)

**Liveness Probe:**
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3
```
- **Implementation**: Simple endpoint returning `{"status": "alive"}`
- **Purpose**: Detect if FastAPI process is responsive (not deadlocked)
- **Keep it lightweight**: No database checks, no external calls

**Readiness Probe:**
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```
- **Implementation**: Check database connection, Redis, critical dependencies
- **Purpose**: Ensure backend can handle requests before receiving traffic
- **Use async checks**: `asyncio.gather()` for parallel dependency validation

**Startup Probe:**
```yaml
startupProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 5
  failureThreshold: 12  # 60 seconds max startup time
```
- **Purpose**: Give FastAPI time to import modules, establish DB connections
- **Disables liveness/readiness**: Until startup probe succeeds

### Next.js Frontend Probes

**Liveness Probe:**
```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3
```
- **Implementation**: Next.js API route `/api/health.ts` returning 200 OK
- **Purpose**: Ensure Node.js process hasn't crashed

**Readiness Probe:**
```yaml
readinessProbe:
  httpGet:
    path: /api/health
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 2
```
- **Implementation**: Same endpoint, or check backend connectivity
- **Purpose**: Verify frontend can serve requests

**Startup Probe:**
```yaml
startupProbe:
  httpGet:
    path: /api/health
    port: 3000
  initialDelaySeconds: 0
  periodSeconds: 5
  failureThreshold: 20  # 100 seconds for slow Next.js startup
```

**Alternatives Considered:**
1. **TCP probes instead of HTTP**
   - Pros: Works without implementing health endpoints
   - Cons: Only checks port open, doesn't verify application health
   - Verdict: Less informative than HTTP probes

2. **Exec probes (command execution)**
   - Pros: Custom health check logic
   - Cons: Performance overhead, container must have shell/tools
   - Verdict: HTTP probes preferred for web apps

3. **Only liveness probes**
   - Pros: Simpler configuration
   - Cons: Pods receive traffic before ready, slow startups cause restarts
   - Verdict: Insufficient for production reliability

**Implementation Guidance:**
- **Separate endpoints**: Use different paths for liveness vs readiness
- **Timing recommendations**:
  - `initialDelaySeconds`: Time before first probe (estimate startup time)
  - `periodSeconds`: How often to probe (5-10 seconds typical)
  - `failureThreshold`: Consecutive failures before action (3 typical)
- **FastAPI library**: Use `fastapi-healthchecks` PyPI package for standardized implementation
- **Async checks**: Always use `async def` for FastAPI health endpoints
- **Avoid cascading failures**: Readiness should fail fast, not wait for timeouts

---

## 7. Resource Allocation for Minikube

### Decision: Modest Resource Requests with Realistic Limits

**Rationale:**
- **Minikube constraints**: Runs on developer workstation, limited resources
- **Quality of Service**: Defining requests + limits ensures Guaranteed/Burstable QoS
- **Prevent resource starvation**: Limits prevent one pod from consuming all resources
- **Realistic for local dev**: Matches production patterns without excessive overhead

**Recommended Allocations:**

### Minikube Cluster Resources
```bash
minikube start --cpus=4 --memory=8192
```
- **CPUs**: Minimum 3, recommended 4 for frontend + backend + system pods
- **Memory**: Minimum 4GB, recommended 8GB for comfortable operation
- **Disk**: Default 20GB sufficient for images and volumes

### FastAPI Backend Container
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"      # 0.25 CPU cores
  limits:
    memory: "512Mi"
    cpu: "500m"      # 0.5 CPU cores
```
- **Rationale**: FastAPI is lightweight, async I/O-bound
- **Memory**: 256Mi baseline, 512Mi for burst traffic
- **CPU**: 250m handles typical async requests, 500m for compute-heavy endpoints

### Next.js Frontend Container
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "250m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```
- **Rationale**: Next.js SSR/SSG can be memory-intensive during rendering
- **Memory**: 128Mi baseline (standalone mode is lean), 256Mi for page rendering
- **CPU**: 250m for serving static pages, 500m for SSR/API routes

### PostgreSQL (if deployed in Minikube)
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "250m"
```
- **Note**: For local dev, consider external database to save Minikube resources

**Alternatives Considered:**
1. **No resource limits**
   - Pros: Maximum flexibility
   - Cons: Pods can consume all node resources, not production-like
   - Verdict: Bad practice, avoid

2. **Very high limits (1GB+ memory, 1+ CPU)**
   - Pros: Never hits limits
   - Cons: Can't run on modest developer machines, unrealistic for production
   - Verdict: Over-provisioning wastes resources

3. **Requests = Limits (Guaranteed QoS)**
   - Pros: Predictable performance, highest priority pods
   - Cons: Inflexible, can't burst, wasteful if requests are too high
   - When to use: Critical production services with known resource needs

**Implementation Guidance:**
- **Start conservative**: Use recommended values, then adjust based on monitoring
- **Monitor actual usage**: `kubectl top pods` to see real consumption
- **Quality of Service classes**:
  - Guaranteed: requests == limits (highest priority)
  - Burstable: requests < limits (recommended for most apps)
  - BestEffort: no requests/limits (lowest priority, avoid)
- **CPU units**: `1000m = 1 CPU core`, `250m = 0.25 cores`
- **Memory units**: Use `Mi` (mebibytes) not `MB` (megabytes)
- **Horizontal scaling**: If hitting limits frequently, increase replicas not resources

---

## 8. Deployment Order and Dependencies

### Decision: Backend-First Deployment with Init Containers for Readiness

**Rationale:**
- **Frontend depends on backend**: Frontend needs backend API to function
- **Avoid connection errors**: Frontend shouldn't start before backend is ready
- **Init containers enforce order**: Block frontend pod startup until backend is reachable
- **Kubernetes-native approach**: No external orchestration needed

**Deployment Strategy:**

### Phase 1: Backend Deployment
1. Deploy backend Deployment + Service
2. Wait for backend readiness probes to pass
3. Backend service DNS becomes resolvable

### Phase 2: Frontend Deployment with Init Container
1. Init container checks backend availability
2. Only after backend responds, main frontend container starts
3. Frontend connects to backend via service DNS

**Init Container Implementation:**

**Frontend Deployment with Init Container:**
```yaml
spec:
  initContainers:
    - name: wait-for-backend
      image: busybox:1.36
      command:
        - 'sh'
        - '-c'
        - |
          until wget --spider -q http://backend-service:8000/health/ready; do
            echo "Waiting for backend to be ready..."
            sleep 5
          done
          echo "Backend is ready!"
```

**How It Works:**
- Init container runs before main containers
- Polls backend readiness endpoint
- Exits successfully only when backend responds
- Main frontend container starts only after init container succeeds
- If init container fails, Kubernetes retries based on pod `restartPolicy`

**Alternatives Considered:**

1. **Manual deployment order (kubectl apply backend, then frontend)**
   - Pros: Simple, no extra configuration
   - Cons: Manual coordination, error-prone, race conditions on restart
   - Verdict: Not reliable for automated deployments

2. **Helm hooks (pre-install/post-install)**
   - Pros: Declarative ordering
   - Cons: Complex for simple dependency, doesn't handle restarts well
   - Verdict: Over-engineered for this use case

3. **Parallel deployment with retry logic in frontend**
   - Pros: Faster initial deployment
   - Cons: Frontend pods crash-loop until backend ready, noisy logs
   - Verdict: Works but less clean than init containers

4. **Readiness gates**
   - Pros: Advanced pod lifecycle control
   - Cons: Requires external controller to set gate status
   - When to use: Complex multi-service dependencies with custom orchestration

**Implementation Guidance:**

**Helm Deployment Order:**
```bash
# Single command installs both, init container handles ordering
helm install myapp ./helm-chart
```

**Init Container Best Practices:**
- Use lightweight image (busybox, alpine)
- Set reasonable timeout (5-10 minute overall)
- Check readiness endpoint, not just liveness
- Log progress for debugging
- Use `wget`, `curl`, or `nc` for HTTP checks

**Database Dependencies:**
- If backend depends on database, add init container to backend deployment too
- Check database port connectivity: `nc -zv postgres-service 5432`
- Or check readiness: `pg_isready -h postgres-service -p 5432`

**Handling Failures:**
- Init container failures trigger pod restart (based on `restartPolicy: Always`)
- Kubernetes backs off exponentially (10s, 20s, 40s, ...)
- Max backoff typically 5 minutes

**Advanced: Dependency Graph Orchestration:**
- For complex dependencies (3+ services), consider tools:
  - **Argo CD App-of-Apps**: Manages deployment order across multiple Helm charts
  - **Flux Kustomization dependencies**: Define depends-on relationships
  - **Custom Kubernetes operators**: For very complex orchestration
- **For this project**: Init containers are sufficient

---

## Cross-Cutting Concerns

### CORS Configuration

**Decision: Handle CORS at Backend Application Level, Not Ingress**

**Rationale:**
- No ingress controller in basic Minikube setup (using NodePort)
- FastAPI has built-in CORS middleware
- More control over allowed origins, methods, headers
- Easier to test and debug

**FastAPI CORS Setup:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend-service:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**If using Ingress (future enhancement):**
- Add annotations to Ingress resource:
  ```yaml
  annotations:
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://example.com"
    nginx.ingress.kubernetes.io/cors-allow-credentials: "true"
  ```

### Next.js Environment Variables (NEXT_PUBLIC_)

**Challenge:** NEXT_PUBLIC_ variables are baked at build time, not runtime

**Solutions:**
1. **Build separate images per environment** (not applicable - code is immutable)
2. **Entrypoint script with placeholder replacement**:
   - Build with placeholder: `NEXT_PUBLIC_API_URL=__API_URL_PLACEHOLDER__`
   - Entrypoint script replaces placeholder with env var at runtime
3. **Use server-side API proxy** (recommended):
   - Frontend calls Next.js API route `/api/backend/*`
   - API route proxies to backend using server-side env var
   - Only server-side vars are runtime-configurable

**Recommendation:** Use server-side env vars only, avoid NEXT_PUBLIC_ for dynamic config

---

## Summary Decision Matrix

| Topic | Decision | Key Benefit |
|-------|----------|-------------|
| Next.js Base Image | `node:18-alpine` + multi-stage | Smallest image, fastest startup |
| FastAPI Base Image | `python:3.11-slim` | Better compatibility, faster builds |
| Helm Structure | Single chart, multiple deployments | Simpler management, shared config |
| Backend Service | ClusterIP | Internal-only, secure |
| Frontend Service | NodePort | External access for local dev |
| Config Management | ConfigMap + Secrets | Security + clarity |
| Probes | Startup + Liveness + Readiness | Maximum reliability |
| Resource Requests | Backend: 256Mi/250m, Frontend: 128Mi/250m | Balanced for Minikube |
| Deployment Order | Init containers in frontend | Enforces backend-first |
| CORS | FastAPI middleware | Simplicity, no ingress needed |

---

## References

### Next.js & Docker
- [Dockerize a Next.js app using multi-stage builds | Johnny Metz](https://johnnymetz.com/posts/dockerize-nextjs-app/)
- [NextJs Deployment with Docker: Complete Guide for 2025 - DEV Community](https://dev.to/codeparrot/nextjs-deployment-with-docker-complete-guide-for-2025-3oe8)
- [Next.js multi-stage Dockerfile example - GitHub](https://github.com/johnnymetz/docker-nextjs)

### FastAPI & Docker
- [FastAPI in Containers - Docker - FastAPI](https://fastapi.tiangolo.com/deployment/docker/)
- [FastAPI Docker Best Practices | Better Stack Community](https://betterstack.com/community/guides/scaling-python/fastapi-docker-best-practices/)
- [Slimmer FastAPI Docker Images with Multi-Stage Builds](https://davidmuraya.com/blog/slimmer-fastapi-docker-images-multistage-builds/)
- [Alpine Based Docker Images Make a Difference in Real World Apps](https://www.cloudbees.com/blog/alpine-based-docker-images-make-difference-real-world-apps)

### Helm Charts
- [Building a Helm Chart for Multi-App Deployments | Medium](https://medium.com/@nsalexamy/building-a-helm-chart-for-multi-app-deployments-ffbd3593be50)
- [Using Helm to deploy a Frontend and backend Application - DEV Community](https://dev.to/adesoji1/using-helm-to-deploy-a-frontend-and-backend-application-2j2p)
- [Charts | Helm](https://helm.sh/docs/topics/charts/)
- [General Conventions | Helm](https://helm.sh/docs/chart_best_practices/conventions/)

### Kubernetes Networking
- [Service | Kubernetes](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Understanding Kubernetes Services: ClusterIP and NodePort | Medium](https://medium.com/@jeetanshu/understanding-kubernetes-services-clusterip-and-nodeport-0f9e0066a78a)
- [Kubernetes Service Discovery: What You Must Know](https://www.plural.sh/blog/kubernetes-service-discovery-guide/)

### ConfigMaps & Secrets
- [In-Depth Guide to Kubernetes ConfigMap & Secret Management Strategies](https://www.gravitee.io/blog/kubernetes-configurations-secrets-configmaps)
- [Kubernetes ConfigMap: Examples, Usage & Best Practices Guide](https://devtron.ai/blog/kubernetes-configmaps-secrets/)
- [Difference between Kubernetes ConfigMaps and Secrets | CloudTruth](https://cloudtruth.com/blog/whats-the-difference-between-configmaps-and-secrets/)

### Health Checks & Probes
- [Configure Liveness, Readiness and Startup Probes | Kubernetes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Guide to Understanding Your Kubernetes Liveness Probes Best Practices](https://www.fairwinds.com/blog/a-guide-to-understanding-kubernetes-liveness-probes-best-practices)
- [FastAPI Health Check Endpoint Example: Python Code & Best Practices | Index.dev](https://www.index.dev/blog/how-to-implement-health-check-in-python)
- [fastapi-healthchecks · PyPI](https://pypi.org/project/fastapi-healthchecks/)

### Resource Allocation
- [Kubernetes Minikube: A Pragmatic 2026 Playbook – TheLinuxCode](https://thelinuxcode.com/kubernetes-minikube-a-pragmatic-2026-playbook/)
- [Deploying FastAPI and PostgreSQL Microservices to Kubernetes using Minikube | EKS Developers Workshop](https://developers.eksworkshop.com/docs/python/kubernetes/deploy-app/)
- [A Guide to Local Kubernetes Development with Minikube | Better Stack Community](https://betterstack.com/community/guides/scaling-docker/minikube/)

### Deployment Dependencies
- [Init Containers | Kubernetes](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Configure the Order of Kubernetes Pod Initialization | Baeldung on Ops](https://www.baeldung.com/ops/kubernetes-configure-order-pod-initialization)
- [Kubernetes Demystified: Solving Service Dependencies - Alibaba Cloud Community](https://www.alibabacloud.com/blog/kubernetes-demystified-solving-service-dependencies_594110)

### Environment Variables & CORS
- [Dynamic Environment Variables in Dockerized Next.js: A Flexible Multi-Environment Solution](https://www.abgeo.dev/blog/dynamic-environment-variables-dockerized-nextjs/)
- [Configuring CORS settings on kubernetes NGINX ingress | Antti Viitala](https://aviitala.com/posts/aks-nginx-ingress-cors/)
- [CORS on Kubernetes Ingress Nginx - IMTI](https://imti.co/kubernetes-ingress-nginx-cors/)

### Python Dependencies (psycopg2)
- [Install psycopg2-binary With Docker | rockyourcode](https://www.rockyourcode.com/install-psycopg2-binary-with-docker/)
- [python-alpine and Postgres issues | Varun Kruthiventi](https://www.varunk.me/blog/python-alpine-and-postgres-issues)

---

## Next Steps

1. **Create Dockerfiles**: Implement multi-stage builds for both services following guidelines above
2. **Create Helm Chart**: Structure chart with separate deployments, services, ConfigMaps, Secrets
3. **Implement Health Endpoints**: Add `/health/live` and `/health/ready` to FastAPI backend
4. **Configure Probes**: Add startup, liveness, readiness probes to deployment manifests
5. **Test Locally**: Deploy to Minikube and verify service discovery, health checks, resource usage
6. **Document Access**: Provide `minikube ip` and NodePort for frontend access

---

**Research Completed**: 2026-01-20
**Next Phase**: Implementation (Dockerfile creation, Helm chart development)

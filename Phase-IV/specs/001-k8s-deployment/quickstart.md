# Quickstart Guide: Phase IV Local Kubernetes Deployment

**Date**: 2026-01-20
**Context**: Deploy TaskFlow AI Chatbot to local Kubernetes (Minikube)
**Prerequisites**: Docker Desktop, Minikube, Helm 3.x, kubectl

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Docker Desktop installed and running
- [ ] Minikube installed (`minikube version` works)
- [ ] Helm 3.x installed (`helm version` shows v3.x)
- [ ] kubectl installed (`kubectl version --client` works)
- [ ] PostgreSQL database accessible (local or remote)
- [ ] Anthropic Claude API key (for chatbot functionality)
- [ ] Minimum 4GB RAM and 2 CPU cores available for Minikube

---

## Step 1: Start Minikube

Start Minikube with sufficient resources:

**Purpose**: Initialize local Kubernetes cluster with adequate resources for frontend + backend

**Resource Allocation**:
- CPUs: 4
- Memory: 8GB
- Driver: Docker (recommended)

**Expected Outcome**: Minikube starts successfully and kubectl can connect to cluster

---

## Step 2: Prepare Environment Secrets

Create a file `secrets.env` with the following values (DO NOT commit to git):

```env
DATABASE_URL=postgresql://user:password@host:5432/database
BETTER_AUTH_SECRET=your-32-character-or-longer-secret-here
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**Critical Requirements**:
- `BETTER_AUTH_SECRET` MUST be at least 32 characters
- `BETTER_AUTH_SECRET` MUST be identical for frontend and backend
- `DATABASE_URL` MUST point to an accessible PostgreSQL database
- `ANTHROPIC_API_KEY` MUST be a valid Claude API key

**Expected Outcome**: All required secrets are documented and ready for Helm values file

---

## Step 3: Configure CORS Origins

Determine your Minikube IP address:

**Command**: `minikube ip`

**Expected Output**: IP address like `192.168.49.2`

Update the `CORS_ORIGINS` value in Helm values to include:
`http://<minikube-ip>:<frontend-nodeport>`

**Example**: `http://192.168.49.2:30080`

**Purpose**: Allow frontend to call backend without CORS errors

**Expected Outcome**: CORS configuration includes Minikube endpoint

---

## Step 4: Build Docker Images

Navigate to the repository root and build both images:

**Backend Image**:
- Location: `Phase-II/backend/`
- Tag: `taskflow-backend:latest`

**Frontend Image**:
- Location: `Phase-II/frontend/`
- Tag: `taskflow-frontend:latest`

**Build Strategy**: Use Docker AI Agent (Gordon) if available, otherwise use standard Dockerfiles

**Expected Outcome**: Both images build successfully without errors and are available in local Docker registry

**Validation**: Images appear in Docker Desktop or `docker images` output

---

## Step 5: Load Images into Minikube

Load the built images into Minikube's Docker daemon:

**Purpose**: Make local Docker images available to Kubernetes without pushing to remote registry

**Expected Outcome**: Images are available inside Minikube cluster

**Validation**: Images are visible when running docker commands inside Minikube

---

## Step 6: Deploy with Helm

Navigate to the Helm chart directory and install:

**Chart Location**: `Phase-IV/helm/taskflow/`

**Release Name**: `taskflow`

**Values Override**: Use custom values file with secrets from Step 2

**Expected Outcome**:
- Helm install completes successfully
- Backend deployment creates pods
- Frontend deployment creates pods
- Services are created (backend ClusterIP, frontend NodePort)
- ConfigMaps and Secrets are created

**Validation**: `helm list` shows `taskflow` release with status `deployed`

---

## Step 7: Verify Pod Status

Check that all pods are running:

**Expected Output**:
- `taskflow-backend-<hash>`: STATUS `Running`, READY `1/1`
- `taskflow-frontend-<hash>`: STATUS `Running`, READY `1/1`

**Timeframe**: Pods should reach Running state within 2 minutes

**Troubleshooting**:
- If pods are `Pending`: Check resource availability (`kubectl describe node`)
- If pods are `CrashLoopBackOff`: Check logs (`kubectl logs <pod-name>`)
- If pods are `ErrImagePull`: Verify images were loaded into Minikube

---

## Step 8: Check Health Endpoints

Verify backend health check:

**Purpose**: Confirm backend container started successfully and can respond to requests

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "chat_registered": true
}
```

**Validation**: Status code `200 OK` and `"status": "healthy"`

---

## Step 9: Access Frontend

Get the frontend service NodePort:

**Expected Output**: NodePort in range `30000-32767`

Access frontend in browser:

**URL**: `http://<minikube-ip>:<nodeport>`

**Expected Outcome**:
- Frontend loads without errors
- TaskFlow UI appears identical to production (https://taskflow-ai-chatbot.vercel.app/)
- No JavaScript console errors

---

## Step 10: Test Full Workflow

Execute end-to-end test:

1. **Signup**: Create a new user account
2. **Login**: Authenticate with created credentials
3. **Create Task**: Add a task via UI
4. **List Tasks**: Verify task appears in task list
5. **Chatbot Interaction**: Send message to AI chatbot
6. **Tool Execution**: Ask chatbot to create/list/update tasks
7. **Task Completion**: Mark task as completed
8. **Delete Task**: Remove task from list

**Expected Outcome**: All operations succeed identically to production behavior

**Validation**:
- API responses match production format
- JWT authentication works correctly
- Tasks persist to database
- Chatbot executes MCP tools successfully

---

## Verification Checklist

After deployment, verify:

- [ ] Backend pod is Running (1/1 Ready)
- [ ] Frontend pod is Running (1/1 Ready)
- [ ] Backend health endpoint returns `200 OK`
- [ ] Frontend loads in browser without errors
- [ ] User signup works (creates user in database)
- [ ] User login returns JWT token
- [ ] Task creation persists to database
- [ ] Task list retrieves user's tasks only
- [ ] Task update modifies existing task
- [ ] Task deletion removes task
- [ ] Chatbot responds to messages
- [ ] Chatbot can execute task tools (add_task, list_tasks, etc.)
- [ ] Authentication persists across page refreshes
- [ ] CORS errors do NOT appear in browser console
- [ ] No unexpected errors in pod logs

---

## Rollback Procedure

If deployment fails validation:

**Immediate Actions**:
1. Document the failure (screenshots, logs, error messages)
2. Run `helm rollback taskflow` if previous release exists
3. If no previous release, run `helm uninstall taskflow`
4. Stop Minikube if needed: `minikube stop`

**Investigation**:
1. Check pod logs: `kubectl logs <pod-name>`
2. Check pod events: `kubectl describe pod <pod-name>`
3. Check service configuration: `kubectl describe service <service-name>`
4. Check ConfigMaps/Secrets: `kubectl get configmap`, `kubectl get secret`

**Do NOT**:
- Attempt fixes without understanding root cause
- Modify application code to "fix" deployment issues
- Guess or assume what went wrong

---

## Common Issues and Solutions

### Issue: Backend Pod CrashLoopBackOff

**Possible Causes**:
- Invalid `DATABASE_URL` (cannot connect to PostgreSQL)
- `BETTER_AUTH_SECRET` too short (< 32 characters)
- Missing `ANTHROPIC_API_KEY`

**Solution**: Check pod logs (`kubectl logs`), verify environment variables in Secret, ensure database is accessible

---

### Issue: Frontend Cannot Reach Backend

**Possible Causes**:
- `NEXT_PUBLIC_API_URL` points to wrong service name
- Backend service not created or wrong port
- CORS configuration missing Minikube endpoint

**Solution**: Verify service exists (`kubectl get services`), check CORS_ORIGINS includes Minikube IP, test backend health endpoint directly

---

### Issue: Authentication Fails (401 Errors)

**Possible Causes**:
- `BETTER_AUTH_SECRET` mismatch between frontend and backend
- JWT token not included in Authorization header
- Token expired

**Solution**: Verify both frontend and backend use IDENTICAL `BETTER_AUTH_SECRET`, check browser network tab for Authorization header, try fresh login

---

### Issue: Chatbot Returns 500 Error

**Possible Causes**:
- Invalid `ANTHROPIC_API_KEY`
- Anthropic API rate limit exceeded
- Database connection lost (cannot save conversation)

**Solution**: Check backend logs for Anthropic API errors, verify API key is valid and has credits, test database connectivity

---

## Success Criteria

Deployment is successful when:

1. All pods reach `Running` state within 2 minutes
2. Health checks return `200 OK`
3. Frontend loads without JavaScript errors
4. Full user workflow (signup → task creation → chatbot) works identically to production
5. API responses match production format exactly
6. No CORS errors in browser console
7. Application behavior is indistinguishable from Vercel/HuggingFace deployments

---

## Next Steps

After successful deployment:

1. **Test Edge Cases**: Try invalid credentials, database disconnect, network failures
2. **Monitor Logs**: Watch pod logs for unexpected errors
3. **Performance Testing**: Measure response times compared to production
4. **Resource Monitoring**: Use `kubectl top pods` to check CPU/memory usage
5. **Scale Testing**: Try scaling backend to 2 replicas (`kubectl scale deployment`)

---

## Getting Help

If you encounter issues:

1. **Check Pod Logs**: `kubectl logs <pod-name>` for application errors
2. **Check Events**: `kubectl get events --sort-by='.lastTimestamp'` for cluster events
3. **Describe Resources**: `kubectl describe <resource-type> <resource-name>` for detailed info
4. **Helm Status**: `helm status taskflow` for release information

**Do NOT proceed with fixes until root cause is identified**

---

## Summary

This quickstart guide walks through:
1. Starting Minikube with appropriate resources
2. Preparing environment secrets
3. Configuring CORS for local access
4. Building and loading Docker images
5. Deploying with Helm
6. Verifying deployment success
7. Testing full application workflow
8. Handling common issues

Follow each step in order and verify outcomes before proceeding. If any step fails, stop and investigate before continuing.

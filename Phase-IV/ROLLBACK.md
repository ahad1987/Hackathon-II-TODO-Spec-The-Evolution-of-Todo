# Phase IV - Rollback & Troubleshooting Guide

**Constitutional Mandate**: If deployment does NOT behave identically to production, it is INVALID and must be corrected.

---

## When to Rollback

**IMMEDIATE ROLLBACK** if any of these occur:

- ❌ Any API endpoint returns different response than production
- ❌ Authentication behavior differs from production
- ❌ Frontend displays errors not present in production
- ❌ Backend health checks fail consistently
- ❌ Chatbot functionality broken or behaves differently
- ❌ Task CRUD operations fail or produce different results

---

## Rollback Procedure

### Quick Rollback

If you just deployed and need to rollback immediately:

```bash
# Rollback to previous revision
helm rollback taskflow

# Or specify a specific revision
helm rollback taskflow 1
```

**Expected Output**:
```
Rollback was a success! Happy Helm

ing!
```

### Complete Uninstall

If no previous revision exists or you want to start fresh:

```bash
# Uninstall the release
helm uninstall taskflow

# Verify pods are terminated
kubectl get pods

# Verify services are removed
kubectl get services
```

**Expected**: All taskflow-related resources are deleted.

---

## Post-Rollback Investigation

**DO NOT proceed with fixes until root cause is identified!**

### 1. Document the Failure

Capture all evidence:

```bash
# Get pod status
kubectl get pods > failure-pods.txt

# Get pod events
kubectl describe pod <pod-name> > failure-events.txt

# Get backend logs
kubectl logs deployment/taskflow-backend > failure-backend-logs.txt

# Get frontend logs
kubectl logs deployment/taskflow-frontend > failure-frontend-logs.txt

# Get service configuration
kubectl describe service taskflow-backend-service > failure-backend-service.txt
kubectl describe service taskflow-frontend-service > failure-frontend-service.txt

# Get Helm values
helm get values taskflow > failure-helm-values.yaml
```

### 2. Analyze Root Cause

Check for common issues:

#### Database Connection Failures

**Symptoms**:
- Backend pods crash-loop
- Logs show: `psycopg2.OperationalError` or `could not connect to server`

**Investigation**:
```bash
# Check DATABASE_URL is correct
kubectl get secret taskflow-backend-secrets -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Test connectivity from backend pod
kubectl exec deployment/taskflow-backend -- nc -zv <database-host> <database-port>
```

**Fix**:
1. Verify DATABASE_URL format: `postgresql://user:pass@host:port/dbname`
2. Verify database is accessible from Minikube
3. Update values-local.yaml with correct DATABASE_URL
4. Redeploy

#### JWT Secret Mismatch

**Symptoms**:
- Login returns 401 Unauthorized
- Backend logs show: `Invalid token` or `Signature verification failed`

**Investigation**:
```bash
# Check backend secret
kubectl get secret taskflow-backend-secrets -o jsonpath='{.data.BETTER_AUTH_SECRET}' | base64 -d

# Check frontend secret
kubectl get secret taskflow-frontend-secrets -o jsonpath='{.data.BETTER_AUTH_SECRET}' | base64 -d
```

**Fix**:
1. Verify BETTER_AUTH_SECRET is at least 32 characters
2. Verify backend and frontend secrets are IDENTICAL
3. Update values-local.yaml
4. Redeploy

#### CORS Errors

**Symptoms**:
- Browser console shows: `CORS policy: No 'Access-Control-Allow-Origin' header`
- Frontend cannot call backend APIs

**Investigation**:
```bash
# Check CORS_ORIGINS configuration
kubectl get secret taskflow-backend-secrets -o jsonpath='{.data.CORS_ORIGINS}' | base64 -d

# Get actual frontend URL
minikube ip
kubectl get svc taskflow-frontend-service -o jsonpath='{.spec.ports[0].nodePort}'
```

**Fix**:
1. Verify CORS_ORIGINS includes: `http://<minikube-ip>:<nodeport>`
2. Update values-local.yaml
3. Redeploy

#### API Key Invalid

**Symptoms**:
- Chatbot returns 500 errors
- Backend logs show: `AuthenticationError` or `Invalid API key`

**Investigation**:
```bash
# Check API key is present
kubectl get secret taskflow-backend-secrets -o jsonpath='{.data.ANTHROPIC_API_KEY}' | base64 -d
```

**Fix**:
1. Verify ANTHROPIC_API_KEY starts with `sk-ant-api03-`
2. Verify key is valid (test at https://console.anthropic.com/)
3. Update values-local.yaml
4. Redeploy

#### Image Pull Errors

**Symptoms**:
- Pods show `ImagePullBackOff` or `ErrImagePull`
- Describe pod shows: `Failed to pull image`

**Investigation**:
```bash
kubectl describe pod <pod-name> | findstr -i "image"
```

**Fix**:
1. Verify images are loaded into Minikube:
   ```bash
   minikube ssh docker images | findstr taskflow
   ```
2. If missing, reload images:
   ```bash
   minikube image load taskflow-backend:1.0.0
   minikube image load taskflow-frontend:1.0.0
   ```
3. Redeploy

#### Resource Constraints

**Symptoms**:
- Pods show `Pending` status
- Describe pod shows: `Insufficient cpu` or `Insufficient memory`

**Investigation**:
```bash
kubectl describe node minikube | findstr -i "allocated\|capacity"
```

**Fix**:
1. Increase Minikube resources:
   ```bash
   minikube delete
   minikube start --cpus=4 --memory=8192
   ```
2. Reduce resource requests in values-local.yaml
3. Redeploy

---

## Redeployment After Fix

### 1. Verify Fix

Before redeploying, verify the fix:

**For configuration changes**:
```bash
# Review values-local.yaml changes
cat Phase-IV/helm/values-local.yaml
```

**For image changes**:
```bash
# Verify new images built successfully
docker images | findstr taskflow

# Reload into Minikube
minikube image load taskflow-backend:1.0.0
minikube image load taskflow-frontend:1.0.0
```

### 2. Redeploy

```bash
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-IV\helm

# If previous deployment exists, upgrade
helm upgrade taskflow ./taskflow -f values-local.yaml --wait

# If starting fresh after uninstall
helm install taskflow ./taskflow -f values-local.yaml --wait --timeout 5m
```

### 3. Validate Fix

Re-run validation from DEPLOYMENT.md Step 11:

- [ ] Pods reach Running state
- [ ] Backend health check returns 200 OK
- [ ] Frontend loads without errors
- [ ] User signup works
- [ ] Task CRUD operations work
- [ ] Chatbot interaction works

---

## Validation Checklist

After any redeployment, verify **ALL** of these:

### Infrastructure Validation

```bash
# 1. Check pod status
kubectl get pods
# Expected: All pods Running (1/1 Ready)

# 2. Check services
kubectl get services
# Expected: Both services created with correct ports

# 3. Check backend health
kubectl exec deployment/taskflow-backend -- curl -s http://localhost:8000/health
# Expected: {"status": "healthy", ...}

# 4. Check DNS resolution
kubectl exec deployment/taskflow-frontend -- nslookup taskflow-backend-service
# Expected: Service IP resolves

# 5. Check backend reachability from frontend
kubectl exec deployment/taskflow-frontend -- wget -qO- http://taskflow-backend-service:8000/health
# Expected: Health check response
```

### Application Validation

**Access frontend**: http://\<minikube-ip\>:\<nodeport\>

```
✅ Frontend UI loads
✅ No JavaScript console errors
✅ No CORS errors in network tab

# Test Authentication
✅ Signup creates new user
✅ Login returns JWT token
✅ Token persists across page refresh
✅ Logout works (if implemented)

# Test Task Operations
✅ Create task appears in list
✅ Update task persists changes
✅ Mark task complete updates status
✅ Delete task removes from list
✅ Tasks persist after page refresh

# Test Chatbot
✅ Chatbot responds to messages
✅ Chatbot can list tasks (list_tasks tool)
✅ Chatbot can create task (add_task tool)
✅ Chatbot can update task (update_task tool)
✅ Chatbot can complete task (complete_task tool)
✅ Chatbot can delete task (delete_task tool)
```

### Production Comparison

**Compare with canonical deployments**:

| Operation | Kubernetes | Vercel/HuggingFace | Match? |
|-----------|------------|-------------------|--------|
| Signup response | ... | ... | ✅/❌ |
| Login response | ... | ... | ✅/❌ |
| Create task response | ... | ... | ✅/❌ |
| List tasks response | ... | ... | ✅/❌ |
| Chatbot response format | ... | ... | ✅/❌ |

**Constitutional Mandate**: If ANY operation doesn't match production, deployment is INVALID.

---

## Emergency Procedures

### Complete Cluster Reset

If all else fails and you need to start completely fresh:

```bash
# 1. Uninstall Helm release
helm uninstall taskflow

# 2. Delete all Kubernetes resources
kubectl delete all --all

# 3. Stop Minikube
minikube stop

# 4. Delete Minikube cluster
minikube delete

# 5. Recreate cluster
minikube start --cpus=4 --memory=8192

# 6. Reload images
minikube image load taskflow-backend:1.0.0
minikube image load taskflow-frontend:1.0.0

# 7. Redeploy from scratch
helm install taskflow ./taskflow -f values-local.yaml --wait --timeout 5m
```

### Rebuild Images

If Docker images are corrupted or need rebuilding:

```bash
# 1. Remove old images
docker rmi taskflow-backend:1.0.0
docker rmi taskflow-frontend:1.0.0

# 2. Rebuild backend
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\backend
docker build --no-cache -f ../../Phase-IV/docker/backend.Dockerfile -t taskflow-backend:1.0.0 .

# 3. Rebuild frontend
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\frontend
docker build --no-cache -f ../../Phase-IV/docker/frontend.Dockerfile -t taskflow-frontend:1.0.0 .

# 4. Reload into Minikube
minikube image load taskflow-backend:1.0.0
minikube image load taskflow-frontend:1.0.0

# 5. Restart deployment
kubectl rollout restart deployment/taskflow-backend
kubectl rollout restart deployment/taskflow-frontend
```

---

## Getting Help

### Diagnostic Commands

```bash
# Get all resources
kubectl get all

# Get events (shows recent errors)
kubectl get events --sort-by='.lastTimestamp'

# Describe deployment
kubectl describe deployment taskflow-backend
kubectl describe deployment taskflow-frontend

# Get Helm release history
helm history taskflow

# Get Helm manifest
helm get manifest taskflow

# Check Minikube logs
minikube logs
```

### Log Analysis

```bash
# Tail backend logs (follow)
kubectl logs -f deployment/taskflow-backend

# Tail frontend logs (follow)
kubectl logs -f deployment/taskflow-frontend

# Get last 100 lines of backend logs
kubectl logs deployment/taskflow-backend --tail=100

# Get logs from previous pod (if crashed)
kubectl logs deployment/taskflow-backend --previous
```

---

## Common Error Messages

### "ImagePullBackOff"
**Cause**: Image not loaded into Minikube
**Fix**: Run `minikube image load taskflow-backend:1.0.0`

### "CrashLoopBackOff"
**Cause**: Application crashing on startup
**Fix**: Check logs with `kubectl logs <pod-name>`

### "Pending" (pod never starts)
**Cause**: Insufficient cluster resources
**Fix**: Increase Minikube resources or reduce pod resource requests

### "ErrImageNeverPull"
**Cause**: imagePullPolicy set incorrectly
**Fix**: Verify values.yaml has `pullPolicy: IfNotPresent`

### "InvalidImageName"
**Cause**: Image tag mismatch
**Fix**: Verify image tags in values.yaml match built images

---

## Safety Checklist

Before ANY redeployment, verify:

- [ ] Root cause of failure is understood and documented
- [ ] Fix is tested and verified
- [ ] No application code was modified (git status clean)
- [ ] values-local.yaml contains valid secrets
- [ ] Docker images are built and loaded into Minikube
- [ ] Minikube has sufficient resources
- [ ] Helm chart passes lint check

**Never**:
- ❌ Guess at fixes without understanding root cause
- ❌ Modify Phase-II or Phase-III application code
- ❌ Change API routes, ports, or schemas
- ❌ Skip validation steps to "save time"
- ❌ Proceed with deployment if validation fails

---

**Rollback procedures ready!**

Remember: **Safety over completion**. A failed deployment is better than a broken deployment that appears to work.

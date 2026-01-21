# Phase IV - Local Kubernetes Deployment Guide

**Target**: Deploy TaskFlow AI Chatbot to Minikube
**Constitutional Compliance**: Zero application code changes, exact production behavior replication

---

## Prerequisites Checklist

Before starting, ensure you have:

- [x] Docker Desktop installed and running
- [x] Minikube installed (v1.28+)
- [x] Helm 3.x installed
- [x] kubectl installed
- [x] PostgreSQL database accessible (local or remote)
- [x] Anthropic Claude API key
- [x] Minimum 4GB RAM and 2 CPU cores available

---

## Step 1: Start Minikube

Start Minikube with sufficient resources:

```bash
minikube start --cpus=4 --memory=8192
```

**Expected Output**:
```
🎉  minikube v1.xx.x on Windows 10
✨  Using the docker driver based on existing profile
👍  Starting control plane node minikube in cluster minikube
🚜  Pulling base image ...
🔄  Restarting existing docker container for "minikube" ...
🐳  Preparing Kubernetes v1.28.x on Docker xx.xx.x ...
🔎  Verifying Kubernetes components...
🌟  Enabled addons: storage-provisioner, default-storageclass
🏄  Done! kubectl is now configured to use "minikube" cluster
```

**Verify Minikube is running**:
```bash
minikube status
```

**Expected**:
```
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

**Get Minikube IP** (you'll need this later):
```bash
minikube ip
```

**Save this IP address!** Example: `192.168.49.2`

---

## Step 2: Build Docker Images

Navigate to the repository root and build both images:

### Build Backend Image

```bash
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\backend
docker build -f ../../Phase-IV/docker/backend.Dockerfile -t taskflow-backend:1.0.0 .
```

**Expected**: Build completes successfully (may take 2-5 minutes)

### Build Frontend Image

```bash
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-II\frontend
docker build -f ../../Phase-IV/docker/frontend.Dockerfile -t taskflow-frontend:1.0.0 .
```

**Expected**: Build completes successfully (may take 5-10 minutes for npm install and build)

### Verify Images Built

```bash
docker images | findstr taskflow
```

**Expected Output**:
```
taskflow-backend    1.0.0    xxxxx    X minutes ago    XXX MB
taskflow-frontend   1.0.0    xxxxx    X minutes ago    XXX MB
```

---

## Step 3: Load Images into Minikube

Make local Docker images available to Kubernetes:

```bash
minikube image load taskflow-backend:1.0.0
minikube image load taskflow-frontend:1.0.0
```

**Expected**: Each command completes without errors

**Verify images are in Minikube**:
```bash
minikube ssh docker images | findstr taskflow
```

---

## Step 4: Configure Secrets

### Copy the template

```bash
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-IV\helm
copy values-local.yaml.template values-local.yaml
```

### Edit values-local.yaml

Open `values-local.yaml` in a text editor and fill in:

**Required Backend Secrets**:
1. **DATABASE_URL**: Your PostgreSQL connection string
   ```yaml
   DATABASE_URL: "postgresql://postgres:yourpassword@192.168.1.100:5432/taskflow"
   ```

2. **BETTER_AUTH_SECRET**: Generate a 32+ character secret
   ```bash
   # PowerShell: Generate random secret
   -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
   ```
   ```yaml
   BETTER_AUTH_SECRET: "your-generated-32-char-secret-here"
   ```

3. **ANTHROPIC_API_KEY**: Your Claude API key
   ```yaml
   ANTHROPIC_API_KEY: "sk-ant-api03-your-actual-key-here"
   ```

4. **CORS_ORIGINS**: Add Minikube IP (you'll update this after deployment)
   ```yaml
   CORS_ORIGINS: "http://localhost:3000,http://192.168.49.2:NODEPORT,https://taskflow-ai-chatbot.vercel.app"
   ```

**Required Frontend Secrets**:
1. **BETTER_AUTH_SECRET**: **MUST MATCH backend secret exactly**
2. **BETTER_AUTH_URL**: Minikube frontend URL (update after deployment)

**CRITICAL**: Save `values-local.yaml` and **NEVER commit it to git**!

---

## Step 5: Validate Helm Chart

Before deploying, validate the Helm chart:

```bash
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-IV\helm

# Lint the chart
helm lint taskflow

# Preview rendered templates (without actual secrets for security)
helm template taskflow taskflow/
```

**Expected**: No errors, templates render correctly

---

## Step 6: Deploy to Minikube

Install the Helm chart with your local secrets:

```bash
helm install taskflow ./taskflow -f values-local.yaml --wait --timeout 5m
```

**Expected Output**:
```
NAME: taskflow
LAST DEPLOYED: [timestamp]
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
🎉 TaskFlow AI Chatbot has been deployed to Kubernetes!
...
```

**What happens**:
1. Backend ConfigMap and Secrets created
2. Backend Deployment starts (pulls image, starts pod)
3. Backend Service created (ClusterIP on port 8000)
4. Backend health checks run (initial delay 30s)
5. Frontend ConfigMap and Secrets created
6. Frontend Deployment starts (init container waits for backend)
7. Frontend Service created (NodePort on port 3000)
8. Frontend health checks run

**This may take 2-3 minutes** - the `--wait` flag blocks until all pods are Ready.

---

## Step 7: Verify Deployment

### Check Pod Status

```bash
kubectl get pods
```

**Expected Output**:
```
NAME                                 READY   STATUS    RESTARTS   AGE
taskflow-backend-xxxxxxxxxx-xxxxx    1/1     Running   0          2m
taskflow-frontend-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

**If pods are not Running**:
```bash
# Check pod events
kubectl describe pod <pod-name>

# Check pod logs
kubectl logs <pod-name>
```

### Check Services

```bash
kubectl get services
```

**Expected Output**:
```
NAME                        TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
kubernetes                  ClusterIP   10.96.0.1        <none>        443/TCP          Xm
taskflow-backend-service    ClusterIP   10.96.xxx.xxx    <none>        8000/TCP         2m
taskflow-frontend-service   NodePort    10.96.xxx.xxx    <none>        3000:30xxx/TCP   2m
```

**Save the frontend NodePort!** Example: `30080` (the number after `3000:`)

---

## Step 8: Update CORS Configuration

Now that you have the NodePort, update the CORS configuration:

### Get the values

```bash
# Minikube IP (from Step 1)
minikube ip
# Example: 192.168.49.2

# Frontend NodePort (from Step 7)
kubectl get svc taskflow-frontend-service -o jsonpath='{.spec.ports[0].nodePort}'
# Example: 30080
```

### Update values-local.yaml

Edit `values-local.yaml` and update CORS_ORIGINS and BETTER_AUTH_URL:

```yaml
backend:
  secrets:
    CORS_ORIGINS: "http://localhost:3000,http://192.168.49.2:30080,https://taskflow-ai-chatbot.vercel.app"

frontend:
  secrets:
    BETTER_AUTH_URL: "http://192.168.49.2:30080"
```

### Upgrade the deployment

```bash
helm upgrade taskflow ./taskflow -f values-local.yaml
```

**Wait for pods to restart** (about 30 seconds):
```bash
kubectl get pods -w
```

---

## Step 9: Validate Backend

Test the backend health endpoint:

```bash
kubectl exec deployment/taskflow-backend -- curl -s http://localhost:8000/health
```

**Expected Output**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "chat_registered": true
}
```

**Test API docs** (from your machine):

Get backend pod name:
```bash
kubectl get pods -l app.kubernetes.io/component=backend -o name
```

Port-forward to access backend locally:
```bash
kubectl port-forward deployment/taskflow-backend 8000:8000
```

Open browser to: http://localhost:8000/docs

**Expected**: FastAPI Swagger UI loads with all 11 endpoints

---

## Step 10: Access Frontend

Get the frontend URL:

```bash
$MINIKUBE_IP = minikube ip
$NODE_PORT = kubectl get svc taskflow-frontend-service -o jsonpath='{.spec.ports[0].nodePort}'
echo "Frontend URL: http://${MINIKUBE_IP}:${NODE_PORT}"
```

**Open browser** to the frontend URL (e.g., http://192.168.49.2:30080)

**Expected**:
- ✅ TaskFlow UI loads without errors
- ✅ No JavaScript console errors
- ✅ Login/signup buttons visible

---

## Step 11: End-to-End Validation

Test the full workflow:

### 1. User Signup

- Navigate to signup page
- Enter email and password (min 8 characters)
- Click "Sign Up"

**Expected**: User created, redirected to dashboard

### 2. Create Task

- Click "Add Task" or similar
- Enter task title: "Test deployment"
- Enter description (optional)
- Click "Create" or "Save"

**Expected**: Task appears in task list

### 3. Update Task

- Click on the task
- Modify the title or description
- Save changes

**Expected**: Changes persist after page refresh

### 4. Mark Task Complete

- Click checkbox or "Complete" button
- **Expected**: Task shows as completed

### 5. Test Chatbot

- Open chatbot widget
- Send message: "Create a task to test chatbot integration"

**Expected**:
- Chatbot responds
- New task appears in task list (demonstrating MCP tool execution)

### 6. Delete Task

- Delete one of the tasks
- **Expected**: Task removed from list

---

## Success Criteria

Deployment is successful if:

- [x] All pods reach `Running` state (1/1 Ready)
- [x] Backend health check returns `200 OK`
- [x] Frontend loads without JavaScript errors
- [x] User signup works
- [x] Task CRUD operations work (create, read, update, delete)
- [x] Task completion toggle works
- [x] Chatbot responds to messages
- [x] Chatbot can execute task tools (add_task, list_tasks, etc.)
- [x] No CORS errors in browser console
- [x] Behavior matches production deployments

---

## Troubleshooting

### Pods Not Starting

**Check pod status**:
```bash
kubectl get pods
kubectl describe pod <pod-name>
```

**Common issues**:
- Image pull errors: Verify images are loaded (`minikube ssh docker images`)
- Insufficient resources: Check Minikube resources (`minikube config view`)
- ConfigMap/Secret errors: Verify values-local.yaml syntax

### Backend Health Checks Failing

**Check backend logs**:
```bash
kubectl logs deployment/taskflow-backend
```

**Common issues**:
- Database connection failed: Verify DATABASE_URL is correct and database is accessible
- BETTER_AUTH_SECRET too short: Must be at least 32 characters
- Missing ANTHROPIC_API_KEY: Verify API key is valid

### Frontend Cannot Reach Backend

**Test DNS resolution**:
```bash
kubectl exec deployment/taskflow-frontend -- nslookup taskflow-backend-service
```

**Expected**: Backend service IP resolves

**Test backend reachability**:
```bash
kubectl exec deployment/taskflow-frontend -- wget -qO- http://taskflow-backend-service:8000/health
```

**Common issues**:
- Init container failed: Check frontend pod logs
- CORS errors: Verify CORS_ORIGINS includes Minikube NodePort URL

### CORS Errors in Browser

**Check browser console** (F12):
```
Access to fetch at 'http://taskflow-backend-service:8000/api/v1/...' from origin 'http://192.168.49.2:30080' has been blocked by CORS policy
```

**Fix**:
1. Ensure CORS_ORIGINS in values-local.yaml includes frontend URL
2. Run `helm upgrade` to apply changes
3. Wait for backend pod to restart

### Chatbot Returns 500 Error

**Check backend logs**:
```bash
kubectl logs deployment/taskflow-backend | findstr -i "anthropic\|error"
```

**Common issues**:
- Invalid ANTHROPIC_API_KEY: Verify key is correct
- API rate limit exceeded: Wait and retry
- Database connection lost: Check DATABASE_URL

---

## Next Steps

After successful deployment:

1. **Test edge cases**: Invalid credentials, network failures, database disconnect
2. **Monitor resources**: `kubectl top pods`
3. **Scale backend**: `kubectl scale deployment taskflow-backend --replicas=2`
4. **Compare with production**: Verify identical behavior to Vercel/HuggingFace

For rollback procedures, see: [ROLLBACK.md](./ROLLBACK.md)

---

## Quick Reference Commands

```bash
# Get pod status
kubectl get pods

# Get service info
kubectl get services

# View backend logs
kubectl logs -f deployment/taskflow-backend

# View frontend logs
kubectl logs -f deployment/taskflow-frontend

# Port-forward backend
kubectl port-forward deployment/taskflow-backend 8000:8000

# Port-forward frontend
kubectl port-forward deployment/taskflow-frontend 3000:3000

# Restart pods
kubectl rollout restart deployment/taskflow-backend
kubectl rollout restart deployment/taskflow-frontend

# Get frontend URL
minikube service taskflow-frontend-service --url

# Helm status
helm status taskflow

# Helm rollback
helm rollback taskflow

# Helm uninstall
helm uninstall taskflow
```

---

**Deployment complete!** 🎉

Your local Kubernetes deployment should now behave identically to production.

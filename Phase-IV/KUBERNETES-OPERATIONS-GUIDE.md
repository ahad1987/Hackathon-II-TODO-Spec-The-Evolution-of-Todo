# Kubernetes Operations Guide - TaskFlow AI Chatbot

**Complete guide to opening, operating, and managing your TaskFlow deployment on Kubernetes**

---

## Table of Contents

1. [Starting Your Project](#1-starting-your-project)
2. [Accessing Your Application](#2-accessing-your-application)
3. [How It Works (Architecture)](#3-how-it-works-architecture)
4. [Daily Operations](#4-daily-operations)
5. [Monitoring & Logs](#5-monitoring--logs)
6. [Troubleshooting](#6-troubleshooting)
7. [Stopping & Restarting](#7-stopping--restarting)
8. [Advanced Operations](#8-advanced-operations)

---

## 1. Starting Your Project

### First Time Startup (Complete Process)

#### Step 1: Start Minikube
```powershell
# Start Minikube with required resources
minikube start --cpus=4 --memory=3500 --driver=docker
```

**What this does**:
- Creates a local Kubernetes cluster inside Docker
- Allocates 4 CPU cores and 3.5GB RAM
- Typically takes 30-60 seconds if already initialized

**Expected output**:
```
😄  minikube v1.37.0 on Windows 11
✨  Using the docker driver
👍  Starting control plane node minikube
🐳  Preparing Kubernetes v1.28.x
🔎  Verifying Kubernetes components...
🏄  Done! kubectl is now configured to use "minikube" cluster
```

#### Step 2: Verify Minikube is Running
```powershell
minikube status
```

**Expected output**:
```
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

#### Step 3: Check if Your Application is Already Deployed
```powershell
helm list
```

**If you see `taskflow` listed**:
```
NAME        NAMESPACE   REVISION    STATUS      CHART
taskflow    default     1           deployed    taskflow-1.0.0
```
✅ Your application is already deployed! Skip to [Step 5](#step-5-access-your-application)

**If you see nothing**:
Proceed to Step 4 to deploy.

#### Step 4: Deploy Your Application (If Not Already Deployed)
```powershell
# Navigate to helm directory
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-IV\helm

# Deploy with Helm
helm install taskflow ./taskflow -f values-local.yaml --wait --timeout 5m
```

**What this does**:
- Creates ConfigMaps (non-secret configuration)
- Creates Secrets (DATABASE_URL, API keys, JWT secrets)
- Creates Deployments (backend and frontend pods)
- Creates Services (networking for backend and frontend)
- Waits for all pods to be healthy before returning

**Expected output**:
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

#### Step 5: Access Your Application
```powershell
# Get the frontend URL
minikube service taskflow-frontend-service --url
```

**Expected output**:
```
http://127.0.0.1:58743
```

**Open this URL in your browser** and you're ready to use TaskFlow!

---

### Quick Startup (If Already Configured)

If you've already deployed TaskFlow before and just need to restart:

```powershell
# 1. Start Minikube
minikube start

# 2. Wait 30-60 seconds for pods to restart automatically

# 3. Access frontend
minikube service taskflow-frontend-service --url
```

That's it! Your application automatically restarts when Minikube starts.

---

## 2. Accessing Your Application

### Primary Access Method: Minikube Service Tunnel

**Open the application**:
```powershell
minikube service taskflow-frontend-service
```

**What this does**:
- Creates a tunnel from your Windows machine to the Kubernetes service
- Opens your default browser automatically
- Shows the URL in the terminal

**Expected output**:
```
|-----------|---------------------------|-------------|---------------------------|
| NAMESPACE |           NAME            | TARGET PORT |            URL            |
|-----------|---------------------------|-------------|---------------------------|
| default   | taskflow-frontend-service | http/3000   | http://127.0.0.1:58743    |
|-----------|---------------------------|-------------|---------------------------|
🎉  Opening service default/taskflow-frontend-service in default browser...
```

**Keep this terminal window open** while using the application!

---

### Alternative Access Methods

#### Method 1: Direct URL Access
```powershell
# Get the URL without opening browser
minikube service taskflow-frontend-service --url
```

Copy the URL (e.g., `http://127.0.0.1:58743`) and paste it in your browser.

#### Method 2: NodePort Access (Direct IP)
```powershell
# Get Minikube IP
minikube ip
# Output: 192.168.49.2

# Get NodePort
kubectl get svc taskflow-frontend-service -o jsonpath='{.spec.ports[0].nodePort}'
# Output: 31259

# Open in browser: http://192.168.49.2:31259
```

**Note**: This method may not work on Windows due to networking limitations. Use the service tunnel (Method 1) instead.

#### Method 3: Port Forwarding
```powershell
kubectl port-forward deployment/taskflow-frontend 3000:3000
```

Then open: `http://localhost:3000`

**Note**: This bypasses the Kubernetes Service and connects directly to a pod.

---

### Accessing Backend API Directly

**View API Documentation (Swagger UI)**:
```powershell
# Port-forward backend
kubectl port-forward deployment/taskflow-backend 8000:8000

# Open in browser: http://localhost:8000/docs
```

**Backend API endpoints**:
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- All endpoints: `http://localhost:8000/api/v1/*`

---

## 3. How It Works (Architecture)

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR WINDOWS MACHINE                     │
│                                                              │
│  Browser (http://127.0.0.1:58743)                          │
│       ↓                                                      │
│  Minikube Service Tunnel                                    │
│       ↓                                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              MINIKUBE KUBERNETES CLUSTER               │ │
│  │                                                         │ │
│  │  ┌─────────────────────────────────────────┐          │ │
│  │  │  Frontend Pod (Next.js)                 │          │ │
│  │  │  - Container: taskflow-frontend:1.0.0   │          │ │
│  │  │  - Port: 3000                           │          │ │
│  │  │  - User: nextjs (non-root)              │          │ │
│  │  │  - Health checks: ✓ liveness/readiness │          │ │
│  │  └──────────────┬──────────────────────────┘          │ │
│  │                 │                                       │ │
│  │                 │ Calls: http://taskflow-backend-      │ │
│  │                 │        service:8000/api/v1/*         │ │
│  │                 ↓                                       │ │
│  │  ┌─────────────────────────────────────────┐          │ │
│  │  │  Backend Pod (FastAPI)                  │          │ │
│  │  │  - Container: taskflow-backend:1.0.0    │          │ │
│  │  │  - Port: 8000                           │          │ │
│  │  │  - User: appuser (non-root)             │          │ │
│  │  │  - Health checks: ✓ liveness/readiness │          │ │
│  │  │  - MCP Tools: 5 tools loaded            │          │ │
│  │  └──────────────┬──────────────────────────┘          │ │
│  │                 │                                       │ │
│  └─────────────────┼───────────────────────────────────────┘ │
│                    │                                         │
└────────────────────┼─────────────────────────────────────────┘
                     │
                     ↓
         ┌───────────────────────────┐
         │  External Services        │
         │  - Neon PostgreSQL        │
         │  - Anthropic Claude API   │
         └───────────────────────────┘
```

### Data Flow Explanation

**When you open the application:**

1. **Browser → Minikube Tunnel → Frontend Service → Frontend Pod**
   - You type: `http://127.0.0.1:58743`
   - Minikube tunnel routes traffic to Frontend Service (NodePort)
   - Service routes to Frontend Pod on port 3000
   - Next.js server responds with HTML/CSS/JavaScript

2. **Frontend Pod → Backend Service → Backend Pod**
   - Frontend JavaScript makes API calls to: `http://taskflow-backend-service:8000/api/v1/*`
   - Kubernetes DNS resolves `taskflow-backend-service` to Backend Service IP
   - Service routes to Backend Pod on port 8000
   - FastAPI application processes the request

3. **Backend Pod → External Services**
   - **Database**: Backend connects to Neon PostgreSQL via DATABASE_URL
   - **AI**: Backend calls Anthropic Claude API for chatbot responses
   - **MCP Tools**: Backend executes task operations (add, update, delete, list, complete)

4. **Response Flow (Reverse)**
   - Backend sends JSON response → Frontend
   - Frontend updates UI → Browser
   - User sees the result

---

### Kubernetes Resources Explained

#### 1. **Pods** (Running Containers)
```powershell
kubectl get pods
```

**What you see**:
```
NAME                                 READY   STATUS    RESTARTS   AGE
taskflow-backend-xxxxxxxxxx-xxxxx    1/1     Running   0          10m
taskflow-frontend-xxxxxxxxxx-xxxxx   1/1     Running   0          10m
```

**Explanation**:
- Each pod is a running instance of your application
- `1/1 Ready` means 1 container is running out of 1 expected
- `Running` means the pod is healthy
- `RESTARTS: 0` means no crashes (good!)
- Backend pod runs Python/FastAPI
- Frontend pod runs Node.js/Next.js

#### 2. **Services** (Networking)
```powershell
kubectl get services
```

**What you see**:
```
NAME                        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
taskflow-backend-service    ClusterIP   10.96.123.45    <none>        8000/TCP         10m
taskflow-frontend-service   NodePort    10.96.67.89     <none>        3000:31259/TCP   10m
```

**Explanation**:
- **Backend Service (ClusterIP)**: Internal only, not accessible from outside Kubernetes
  - DNS name: `taskflow-backend-service`
  - Port: 8000
  - Frontend uses this to call backend APIs

- **Frontend Service (NodePort)**: Accessible from outside Kubernetes
  - Port 3000 inside cluster
  - Port 31259 exposed on Minikube IP
  - You access this via Minikube tunnel

#### 3. **Deployments** (Pod Management)
```powershell
kubectl get deployments
```

**What you see**:
```
NAME                READY   UP-TO-DATE   AVAILABLE   AGE
taskflow-backend    1/1     1            1           10m
taskflow-frontend   1/1     1            1           10m
```

**Explanation**:
- Deployments manage pods (create, update, restart)
- `1/1 Ready` means 1 replica is desired, 1 is running
- Deployments handle rolling updates and health checks

#### 4. **ConfigMaps** (Non-Secret Configuration)
```powershell
kubectl get configmaps
```

**What you see**:
```
NAME                       DATA   AGE
taskflow-backend-config    3      10m
taskflow-frontend-config   2      10m
```

**Explanation**:
- Stores environment variables like `ENVIRONMENT=development`
- Not encrypted (for non-sensitive data only)

#### 5. **Secrets** (Sensitive Configuration)
```powershell
kubectl get secrets
```

**What you see**:
```
NAME                         TYPE     DATA   AGE
taskflow-backend-secrets     Opaque   4      10m
taskflow-frontend-secrets    Opaque   2      10m
```

**Explanation**:
- Stores sensitive data: DATABASE_URL, ANTHROPIC_API_KEY, BETTER_AUTH_SECRET
- Base64 encoded (basic obfuscation)
- Mounted as environment variables in pods

---

## 4. Daily Operations

### Opening Your Project (Daily Routine)

**Standard startup (3 steps)**:
```powershell
# 1. Start Minikube (if not already running)
minikube start

# 2. Wait 30 seconds for pods to start

# 3. Open the application
minikube service taskflow-frontend-service
```

**That's it!** Your browser opens with TaskFlow ready to use.

---

### Checking if Everything is Running

**Quick health check**:
```powershell
# Check Minikube status
minikube status

# Check pods
kubectl get pods

# Check backend health
kubectl exec deployment/taskflow-backend -- curl -s http://localhost:8000/health
```

**All green?** You're good to go!

---

### Using the Application

**Frontend Features**:
1. **Signup/Login**: Create account or login with existing credentials
2. **Task Management**:
   - Create new tasks
   - Update task titles/descriptions
   - Mark tasks as complete
   - Delete tasks
3. **Chatbot**:
   - Open chat widget (usually bottom-right corner)
   - Send natural language commands:
     - "Create a task to buy groceries"
     - "List all my tasks"
     - "Mark 'buy groceries' as done"
     - "Update 'buy groceries' to 'buy vegetables'"
     - "Delete the task 'buy vegetables'"

**All operations persist to PostgreSQL database!**

---

### Common Operations

#### Restart the Application
```powershell
# Restart backend
kubectl rollout restart deployment/taskflow-backend

# Restart frontend
kubectl rollout restart deployment/taskflow-frontend

# Wait for new pods to be ready
kubectl get pods -w
```

Press `Ctrl+C` to stop watching.

#### Update Configuration
```powershell
# Edit values-local.yaml with new settings
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-IV\helm
notepad values-local.yaml

# Apply changes
helm upgrade taskflow ./taskflow -f values-local.yaml

# Verify upgrade
helm status taskflow
```

#### Check Deployment Status
```powershell
# Quick overview
kubectl get all

# Detailed deployment info
kubectl describe deployment taskflow-backend
kubectl describe deployment taskflow-frontend

# Helm status
helm status taskflow
```

---

## 5. Monitoring & Logs

### Viewing Logs (Real-Time)

**Backend logs** (see API calls, database queries, errors):
```powershell
kubectl logs -f deployment/taskflow-backend
```

**Frontend logs** (see page requests, errors):
```powershell
kubectl logs -f deployment/taskflow-frontend
```

**Combined logs** (both backend and frontend):
```powershell
# In separate terminals
kubectl logs -f deployment/taskflow-backend
kubectl logs -f deployment/taskflow-frontend
```

**Stop tailing logs**: Press `Ctrl+C`

---

### Viewing Historical Logs

**Last 100 lines from backend**:
```powershell
kubectl logs deployment/taskflow-backend --tail=100
```

**Last 500 lines from frontend**:
```powershell
kubectl logs deployment/taskflow-frontend --tail=500
```

**Save logs to file**:
```powershell
kubectl logs deployment/taskflow-backend > backend-logs.txt
kubectl logs deployment/taskflow-frontend > frontend-logs.txt
```

---

### Resource Monitoring

**Check pod resource usage** (CPU, Memory):
```powershell
kubectl top pods
```

**Expected output**:
```
NAME                                CPU(cores)   MEMORY(bytes)
taskflow-backend-xxx                100m         200Mi
taskflow-frontend-xxx               50m          100Mi
```

**Check node resource usage**:
```powershell
kubectl top node
```

**Monitor in real-time**:
```powershell
kubectl top pods -w
```

---

### Event Monitoring

**See recent events** (pod starts, restarts, errors):
```powershell
kubectl get events --sort-by='.lastTimestamp'
```

**Watch events live**:
```powershell
kubectl get events --watch
```

---

### Visual Monitoring (Kubernetes Dashboard)

**Enable and open dashboard**:
```powershell
# Enable dashboard addon
minikube addons enable dashboard
minikube addons enable metrics-server

# Open dashboard
minikube dashboard
```

**Dashboard shows**:
- Pod status with visual indicators
- CPU/Memory graphs
- Logs viewer
- Event timeline
- Deployment controls

---

## 6. Troubleshooting

### Pods Not Starting

**Check pod status**:
```powershell
kubectl get pods
```

**If STATUS is not `Running`**:

**ImagePullBackOff**:
```powershell
# Images not loaded into Minikube
minikube image load taskflow-backend:1.0.0
minikube image load taskflow-frontend:1.0.0

# Restart deployment
kubectl rollout restart deployment/taskflow-backend
kubectl rollout restart deployment/taskflow-frontend
```

**CrashLoopBackOff**:
```powershell
# Check logs for error
kubectl logs deployment/taskflow-backend --tail=50

# Common fixes:
# 1. Database connection issue → Check DATABASE_URL
# 2. Missing API key → Check ANTHROPIC_API_KEY
# 3. Port conflict → Check if port 8000/3000 already in use
```

**Pending**:
```powershell
# Not enough resources
kubectl describe pod <pod-name>

# Solution: Increase Minikube resources
minikube delete
minikube start --cpus=6 --memory=8192
```

---

### Cannot Access Frontend

**Check if service tunnel is running**:
```powershell
# This command should stay running
minikube service taskflow-frontend-service
```

**If tunnel closes immediately**:
```powershell
# Use port-forward instead
kubectl port-forward deployment/taskflow-frontend 3000:3000
# Then open: http://localhost:3000
```

---

### CORS Errors in Browser

**Check browser console** (F12 → Console):
```
Access to fetch at '...' has been blocked by CORS policy
```

**Fix**:
```powershell
# 1. Get actual frontend URL
minikube service taskflow-frontend-service --url
# Copy the URL (e.g., http://127.0.0.1:58743)

# 2. Update CORS configuration
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-IV\helm
notepad values-local.yaml

# 3. Add the URL to CORS_ORIGINS
# Example: CORS_ORIGINS: "http://localhost:3000,http://127.0.0.1:58743,..."

# 4. Apply changes
helm upgrade taskflow ./taskflow -f values-local.yaml

# 5. Wait for backend to restart
kubectl get pods -w
```

---

### Chatbot Not Responding

**Check backend logs**:
```powershell
kubectl logs deployment/taskflow-backend | findstr -i "anthropic"
```

**Common issues**:

**Invalid API Key**:
```
AuthenticationError: Invalid API key
```
**Fix**: Update ANTHROPIC_API_KEY in values-local.yaml

**Rate Limit**:
```
RateLimitError: Rate limit exceeded
```
**Fix**: Wait a few minutes and retry

**Network Error**:
```
Connection timeout to api.anthropic.com
```
**Fix**: Check internet connection

---

### Database Connection Issues

**Check backend logs**:
```powershell
kubectl logs deployment/taskflow-backend | findstr -i "database\|psycopg2"
```

**Common issues**:

**Connection refused**:
```
psycopg2.OperationalError: could not connect to server
```
**Fix**: Check DATABASE_URL is correct and database is accessible

**SSL required**:
```
SSL required
```
**Fix**: Ensure DATABASE_URL includes `?sslmode=require`

**Test connectivity**:
```powershell
kubectl exec deployment/taskflow-backend -- curl -v https://ep-old-sunset-ahewj02h-pooler.c-3.us-east-1.aws.neon.tech
```

---

### Complete Reset (Nuclear Option)

If everything is broken:

```powershell
# 1. Uninstall Helm release
helm uninstall taskflow

# 2. Delete all resources
kubectl delete all --all

# 3. Restart Minikube
minikube stop
minikube start

# 4. Reload images
minikube image load taskflow-backend:1.0.0
minikube image load taskflow-frontend:1.0.0

# 5. Redeploy
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-IV\helm
helm install taskflow ./taskflow -f values-local.yaml --wait

# 6. Access application
minikube service taskflow-frontend-service
```

---

## 7. Stopping & Restarting

### Graceful Shutdown

**Stop Minikube** (preserves all data):
```powershell
minikube stop
```

**What happens**:
- Kubernetes cluster stops
- All pods stop gracefully
- Configuration is saved
- Next `minikube start` restores everything automatically

**Restart after stop**:
```powershell
minikube start
# Wait 30 seconds
minikube service taskflow-frontend-service
```

---

### Pause Deployment (Keep Minikube Running)

**Scale down to zero** (saves resources):
```powershell
kubectl scale deployment taskflow-backend --replicas=0
kubectl scale deployment taskflow-frontend --replicas=0
```

**Restart**:
```powershell
kubectl scale deployment taskflow-backend --replicas=1
kubectl scale deployment taskflow-frontend --replicas=1
```

---

### Complete Shutdown and Cleanup

**Remove deployment but keep Minikube**:
```powershell
helm uninstall taskflow
```

**Remove Minikube cluster entirely**:
```powershell
minikube delete
```

**Warning**: This deletes everything! You'll need to redeploy from scratch.

---

## 8. Advanced Operations

### Scaling (Multiple Replicas)

**Scale backend to 2 replicas**:
```powershell
kubectl scale deployment taskflow-backend --replicas=2
```

**Verify**:
```powershell
kubectl get pods
# You'll see 2 backend pods
```

**Benefits**:
- Load balancing across replicas
- High availability (if one crashes, other handles traffic)
- Rolling updates with zero downtime

**Scale back**:
```powershell
kubectl scale deployment taskflow-backend --replicas=1
```

---

### Automatic Scaling (Based on CPU)

**Create autoscaler**:
```powershell
kubectl autoscale deployment taskflow-backend --cpu-percent=70 --min=1 --max=5
```

**What this does**:
- Monitors CPU usage
- If CPU > 70%, adds more pods (up to 5)
- If CPU < 70%, removes pods (down to 1)

**Check autoscaler status**:
```powershell
kubectl get hpa
```

**Remove autoscaler**:
```powershell
kubectl delete hpa taskflow-backend
```

---

### Executing Commands Inside Pods

**Open shell in backend pod**:
```powershell
kubectl exec -it deployment/taskflow-backend -- /bin/bash
```

**Once inside**:
```bash
# Check Python version
python --version

# List files
ls -la

# Check environment variables
env | grep DATABASE

# Exit
exit
```

**Run single command**:
```powershell
kubectl exec deployment/taskflow-backend -- python --version
```

---

### Direct Database Access (From Backend Pod)

**Open Python shell with database access**:
```powershell
kubectl exec -it deployment/taskflow-backend -- python
```

**Inside Python shell**:
```python
import os
from sqlalchemy import create_engine

# Get database URL from environment
db_url = os.getenv('DATABASE_URL')

# Create engine
engine = create_engine(db_url)

# Test connection
with engine.connect() as conn:
    result = conn.execute("SELECT COUNT(*) FROM tasks")
    print(f"Total tasks: {result.fetchone()[0]}")

# Exit Python
exit()
```

---

### Viewing All Resources

**Get everything**:
```powershell
kubectl get all
```

**Output shows**:
- Pods
- Services
- Deployments
- ReplicaSets

**Get specific resource details**:
```powershell
# Detailed pod info
kubectl describe pod <pod-name>

# Detailed service info
kubectl describe service taskflow-backend-service

# Detailed deployment info
kubectl describe deployment taskflow-backend
```

---

### Helm Operations

**List all releases**:
```powershell
helm list
```

**View release history**:
```powershell
helm history taskflow
```

**Rollback to previous version**:
```powershell
helm rollback taskflow
```

**Rollback to specific revision**:
```powershell
helm rollback taskflow 1
```

**Get rendered values**:
```powershell
helm get values taskflow
```

**Get all Kubernetes manifests**:
```powershell
helm get manifest taskflow
```

---

## Quick Reference Card

### Daily Commands (Copy This!)

```powershell
# ========================================
# DAILY TASKFLOW OPERATIONS
# ========================================

# START
minikube start
minikube service taskflow-frontend-service

# CHECK STATUS
kubectl get pods
kubectl top pods

# VIEW LOGS
kubectl logs -f deployment/taskflow-backend
kubectl logs -f deployment/taskflow-frontend

# RESTART
kubectl rollout restart deployment/taskflow-backend
kubectl rollout restart deployment/taskflow-frontend

# STOP
minikube stop

# ========================================
# TROUBLESHOOTING
# ========================================

# Backend health
kubectl exec deployment/taskflow-backend -- curl -s http://localhost:8000/health

# Recent events
kubectl get events --sort-by='.lastTimestamp' | select -First 10

# Full status
kubectl get all
helm status taskflow

# Complete reset
helm uninstall taskflow
helm install taskflow ./taskflow -f values-local.yaml --wait

# ========================================
# DIRECT ACCESS
# ========================================

# Frontend
minikube service taskflow-frontend-service

# Backend API docs
kubectl port-forward deployment/taskflow-backend 8000:8000
# Then open: http://localhost:8000/docs

# Dashboard
minikube dashboard
```

---

## Summary

### How to Open Your Project

**Simple version (2 steps)**:
1. `minikube start`
2. `minikube service taskflow-frontend-service`

**That's it!** Your browser opens with TaskFlow running.

### How It Works

- **Minikube**: Creates a Kubernetes cluster on your machine
- **Docker Images**: Your application packaged as containers
- **Pods**: Running instances of your containers
- **Services**: Networking that connects frontend ↔ backend
- **Helm**: Manages deployment configuration

### Key Operations

- **Start**: `minikube start` + `minikube service taskflow-frontend-service`
- **Check**: `kubectl get pods` + `kubectl top pods`
- **Logs**: `kubectl logs -f deployment/taskflow-backend`
- **Restart**: `kubectl rollout restart deployment/taskflow-backend`
- **Stop**: `minikube stop`

---

**You now have complete control over your Kubernetes deployment!** 🚀

---

**Last Updated**: 2026-01-21
**Created By**: Claude Sonnet 4.5 (AI Agent)
**For**: TaskFlow AI Chatbot - Phase IV Deployment

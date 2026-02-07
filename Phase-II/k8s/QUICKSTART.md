# Kubernetes Quick Start

Get TaskFlow running on Kubernetes in 5 minutes!

## Prerequisites Check

```bash
# Check if you have required tools
kubectl version --client
dapr --version
```

If missing, install:
- **kubectl**: https://kubernetes.io/docs/tasks/tools/
- **Dapr CLI**: https://docs.dapr.io/getting-started/install-dapr-cli/

## Option 1: Automated Deployment (Recommended)

### Using Minikube (Linux/Mac)

```bash
# 1. Start Minikube
minikube start --memory=4096 --cpus=4

# 2. Run deployment script
cd k8s
./deploy.sh

# 3. Access application
kubectl port-forward service/frontend 3000:3000
kubectl port-forward service/backend 8000:8000

# Open http://localhost:3000
```

### Using Docker Desktop Kubernetes (Windows/Mac)

```bash
# 1. Enable Kubernetes in Docker Desktop
# Settings → Kubernetes → Enable Kubernetes

# 2. Set cluster type and run deployment
cd k8s
export CLUSTER_TYPE=docker-desktop
./deploy.sh

# 3. Access application
kubectl port-forward service/frontend 3000:3000
kubectl port-forward service/backend 8000:8000
```

## Option 2: Manual Deployment

### Step 1: Start Local Cluster

**Minikube:**
```bash
minikube start --memory=4096 --cpus=4
```

**Kind:**
```bash
kind create cluster --name taskflow
```

**Docker Desktop:**
- Enable Kubernetes in Settings

### Step 2: Install Dapr

```bash
dapr init -k
dapr status -k
```

### Step 3: Create Secrets

```bash
cd k8s

# Copy and edit secrets template
cp secrets-template.yaml secrets.yaml
nano secrets.yaml  # or use your favorite editor

# Replace these values:
# - YOUR_PASSWORD → Your Postgres password
# - YOUR_SECURE_JWT_SECRET_KEY_HERE → Random string for JWT
# - YOUR_ANTHROPIC_API_KEY_HERE → Your Anthropic API key

# Apply secrets
kubectl apply -f secrets.yaml
```

### Step 4: Build Images

**For Minikube:**
```bash
eval $(minikube docker-env)
cd ..
docker-compose build
cd k8s
```

**For Kind:**
```bash
cd ..
docker-compose build
kind load docker-image phase-ii-backend:latest --name taskflow
kind load docker-image phase-ii-frontend:latest --name taskflow
kind load docker-image phase-ii-recurring-processor:latest --name taskflow
kind load docker-image phase-ii-reminder-service:latest --name taskflow
kind load docker-image phase-ii-notification-service:latest --name taskflow
kind load docker-image phase-ii-audit-logger:latest --name taskflow
cd k8s
```

### Step 5: Deploy Everything

```bash
# Deploy infrastructure
kubectl apply -f infrastructure/

# Wait for infrastructure
kubectl wait --for=condition=ready pod -l tier=infrastructure --timeout=600s

# Deploy Dapr components
kubectl apply -f dapr/pubsub.yaml

# Deploy application
kubectl apply -f services/phase-v/

# Wait for apps
kubectl wait --for=condition=available deployment --all --timeout=600s
```

### Step 6: Access Application

```bash
# Port forward services
kubectl port-forward service/frontend 3000:3000 &
kubectl port-forward service/backend 8000:8000 &

# Open in browser
open http://localhost:3000  # Mac
start http://localhost:3000  # Windows
xdg-open http://localhost:3000  # Linux
```

## Verify Deployment

```bash
# Check all pods
kubectl get pods

# Check deployments
kubectl get deployments

# Check services
kubectl get services

# View monitoring status
curl http://localhost:8000/api/v1/monitoring/overview | jq

# Expected output:
# - overall_health: "healthy"
# - dapr.healthy: 5
# - kafka.broker.connected: true
# - kubernetes.mode: "kubernetes"
# - kubernetes.cluster: "connected"
```

## Common Issues

### Pods stuck in "ImagePullBackOff"
```bash
# For local clusters, make sure images are loaded
# Minikube: eval $(minikube docker-env) before building
# Kind: kind load docker-image <image-name>
```

### Secrets not found
```bash
# Make sure secrets.yaml was created and applied
kubectl get secrets | grep taskflow
```

### Dapr sidecars failing
```bash
# Check Dapr is initialized
dapr status -k

# Check component configuration
kubectl get components
```

## Access the Monitoring Panel

Once deployed:
1. Open http://localhost:3000/tasks
2. The monitoring panel on the right will show:
   - ✅ Kubernetes: Mode=kubernetes, Cluster=connected
   - ✅ Dapr: 5/5 sidecars healthy
   - ✅ Kafka: Broker connected, 5 topics
   - ✅ Secrets: All 4 secrets configured

## Clean Up

```bash
# Delete all resources
kubectl delete -f services/phase-v/
kubectl delete -f dapr/
kubectl delete -f infrastructure/
kubectl delete -f secrets.yaml

# Stop cluster (local only)
minikube stop  # or: kind delete cluster --name taskflow
```

## Next Steps

- See **DEPLOY.md** for detailed documentation
- Configure Ingress for external access
- Set up monitoring with Prometheus/Grafana
- Configure auto-scaling

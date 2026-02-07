# Kubernetes Deployment Guide

This guide walks you through deploying the TaskFlow application to a Kubernetes cluster.

## Prerequisites

1. **Kubernetes Cluster** - One of the following:
   - **Minikube** (Local): `minikube start --memory=4096 --cpus=4`
   - **Kind** (Local): `kind create cluster --name taskflow`
   - **Docker Desktop K8s** (Local): Enable in Docker Desktop settings
   - **Cloud K8s** (AWS EKS, GCP GKE, Azure AKS, etc.)

2. **kubectl** - Kubernetes CLI tool
   ```bash
   kubectl version --client
   ```

3. **Dapr** - Install Dapr on your Kubernetes cluster
   ```bash
   # Install Dapr CLI
   wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash

   # Initialize Dapr on K8s cluster
   dapr init -k

   # Verify Dapr installation
   dapr status -k
   ```

4. **Docker Images** - Build and push images to a registry accessible by your cluster
   - For local clusters (minikube/kind): Use local registry or load images
   - For cloud clusters: Push to Docker Hub, GCR, ECR, etc.

## Quick Start

### Step 1: Set Up Kubernetes Cluster

**Option A: Minikube (Recommended for local development)**
```bash
# Start minikube with enough resources
minikube start --memory=4096 --cpus=4

# Enable registry addon (optional, for local images)
minikube addons enable registry

# Point your shell to minikube's docker daemon
eval $(minikube docker-env)
```

**Option B: Docker Desktop Kubernetes**
- Open Docker Desktop
- Go to Settings → Kubernetes
- Check "Enable Kubernetes"
- Click "Apply & Restart"

**Option C: Kind**
```bash
kind create cluster --name taskflow --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF
```

### Step 2: Verify Cluster Connection

```bash
# Check cluster info
kubectl cluster-info

# View nodes
kubectl get nodes
```

### Step 3: Install Dapr on Kubernetes

```bash
# Install Dapr CLI (if not already installed)
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash

# Initialize Dapr on your cluster
dapr init -k

# Verify Dapr components are running
kubectl get pods -n dapr-system

# Expected output:
# dapr-operator-xxx          Running
# dapr-placement-server-xxx  Running
# dapr-sentry-xxx            Running
# dapr-sidecar-injector-xxx  Running
```

### Step 4: Build and Load Docker Images

**For Minikube:**
```bash
# Set docker environment to minikube
eval $(minikube docker-env)

# Build all images
cd ../Phase-II
docker-compose build backend frontend recurring-processor reminder-service notification-service audit-logger

# Verify images are available in minikube
minikube ssh docker images | grep phase-ii
```

**For Kind:**
```bash
# Build images
cd ../Phase-II
docker-compose build backend frontend recurring-processor reminder-service notification-service audit-logger

# Load images into kind cluster
kind load docker-image phase-ii-backend:latest --name taskflow
kind load docker-image phase-ii-frontend:latest --name taskflow
kind load docker-image phase-ii-recurring-processor:latest --name taskflow
kind load docker-image phase-ii-reminder-service:latest --name taskflow
kind load docker-image phase-ii-notification-service:latest --name taskflow
kind load docker-image phase-ii-audit-logger:latest --name taskflow
```

**For Cloud/Remote Registry:**
```bash
# Tag images with your registry
docker tag phase-ii-backend:latest YOUR_REGISTRY/phase-ii-backend:latest
docker tag phase-ii-frontend:latest YOUR_REGISTRY/phase-ii-frontend:latest
# ... (repeat for all services)

# Push to registry
docker push YOUR_REGISTRY/phase-ii-backend:latest
# ... (repeat for all services)

# Update image references in deployment YAML files
```

### Step 5: Create Kubernetes Secrets

```bash
# Copy the secrets template
cp k8s/secrets-template.yaml k8s/secrets.yaml

# Edit secrets.yaml and replace placeholder values
# IMPORTANT: Do NOT commit secrets.yaml to version control

# Apply secrets
kubectl apply -f k8s/secrets.yaml

# Verify secrets were created
kubectl get secrets | grep taskflow
```

**Expected secrets:**
- `taskflow-postgres-secret` - Database credentials
- `taskflow-redis-secret` - Redis connection
- `taskflow-kafka-secret` - Kafka broker address
- `taskflow-jwt-secret` - JWT signing key
- `taskflow-anthropic-secret` - Anthropic API key

### Step 6: Deploy Infrastructure (Postgres, Redis, Kafka, Zookeeper)

```bash
# Deploy infrastructure components
kubectl apply -f k8s/infrastructure/

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s
kubectl wait --for=condition=ready pod -l app=kafka --timeout=300s

# Check infrastructure status
kubectl get pods -l tier=infrastructure
```

### Step 7: Deploy Dapr Components (Pub/Sub)

```bash
# Apply Dapr pub/sub component
kubectl apply -f k8s/dapr/pubsub.yaml

# Verify Dapr components
kubectl get components

# Expected output:
# NAME                        AGE
# taskflow-pubsub             X
# taskflow-pubsub-publisher   X
```

### Step 8: Deploy Application Services

```bash
# Deploy Phase V services (backend + event-driven microservices)
kubectl apply -f k8s/services/phase-v/

# Wait for deployments to be ready
kubectl wait --for=condition=available deployment --all --timeout=600s

# Check deployment status
kubectl get deployments
kubectl get pods
```

### Step 9: Expose Services

**Option A: Port Forwarding (Quick testing)**
```bash
# Forward backend API
kubectl port-forward service/backend 8000:8000

# Forward frontend
kubectl port-forward service/frontend 3000:3000

# Access application at http://localhost:3000
```

**Option B: LoadBalancer (Minikube)**
```bash
# Start minikube tunnel (in separate terminal)
minikube tunnel

# Update services to LoadBalancer type
kubectl patch service backend -p '{"spec":{"type":"LoadBalancer"}}'
kubectl patch service frontend -p '{"spec":{"type":"LoadBalancer"}}'

# Get external IPs
kubectl get services
```

**Option C: Ingress (Production)**
```bash
# Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Apply ingress configuration
kubectl apply -f k8s/ingress.yaml
```

### Step 10: Verify Deployment

```bash
# Check all pods are running
kubectl get pods

# Check services
kubectl get services

# Check Dapr sidecars
kubectl get pods -o=custom-columns=NAME:.metadata.name,CONTAINERS:.spec.containers[*].name

# View logs
kubectl logs -l app=backend
kubectl logs -l app=backend -c daprd  # Dapr sidecar logs

# Check monitoring endpoint
kubectl port-forward service/backend 8000:8000
curl http://localhost:8000/api/v1/monitoring/overview
```

## Monitoring After Deployment

Once deployed, access the monitoring panel at `http://FRONTEND_URL/tasks` to see:

- **Kubernetes Section** should show:
  - Mode: `kubernetes`
  - Cluster: `connected`
  - Deployments with ready replicas
  - **Secrets Status**: Configured secrets and any missing ones

- **Dapr Section** should show:
  - All 5 sidecars healthy

- **Kafka Section** should show:
  - Broker connected
  - 5 taskflow topics active

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod to see events
kubectl describe pod POD_NAME

# Check logs
kubectl logs POD_NAME

# Check Dapr sidecar logs
kubectl logs POD_NAME -c daprd
```

### Secrets Not Found

```bash
# Verify secrets exist
kubectl get secrets | grep taskflow

# Check secret details (values will be base64 encoded)
kubectl get secret taskflow-postgres-secret -o yaml
```

### Dapr Issues

```bash
# Check Dapr status
dapr status -k

# Verify Dapr components
kubectl get components

# Check Dapr operator logs
kubectl logs -n dapr-system -l app=dapr-operator
```

### Image Pull Errors

```bash
# For local clusters, verify images are loaded
minikube ssh docker images  # minikube
docker exec kind-control-plane crictl images  # kind

# For remote registry, check image pull secrets
kubectl get secrets
```

### Kafka Connection Issues

```bash
# Check Kafka pod logs
kubectl logs -l app=kafka

# Verify Kafka service
kubectl get svc kafka

# Test Kafka connectivity from a pod
kubectl run kafka-test --rm -it --image=confluentinc/cp-kafka:7.5.0 -- kafka-topics --bootstrap-server kafka:29092 --list
```

## Clean Up

```bash
# Delete all resources
kubectl delete -f k8s/services/phase-v/
kubectl delete -f k8s/dapr/
kubectl delete -f k8s/infrastructure/
kubectl delete -f k8s/secrets.yaml

# Or delete by namespace (if using custom namespace)
kubectl delete namespace taskflow

# Stop cluster (local only)
minikube stop  # or kind delete cluster --name taskflow
```

## Production Considerations

1. **Resource Limits**: Update deployment YAMLs with appropriate CPU/memory limits
2. **Persistent Volumes**: Configure PVCs for Postgres and Kafka data
3. **TLS/SSL**: Enable HTTPS with cert-manager
4. **Secrets Management**: Use external secret managers (Vault, AWS Secrets Manager, etc.)
5. **Monitoring**: Deploy Prometheus and Grafana
6. **Logging**: Set up EFK/ELK stack
7. **Auto-scaling**: Configure HPA (Horizontal Pod Autoscaler)
8. **Backup**: Set up backup strategies for databases

## Next Steps

- [ ] Configure Ingress for external access
- [ ] Set up monitoring with Prometheus/Grafana
- [ ] Configure persistent volumes for stateful services
- [ ] Set up CI/CD pipeline for automated deployments
- [ ] Configure auto-scaling based on load
- [ ] Implement backup and disaster recovery

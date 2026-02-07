#!/bin/bash
set -e

echo "========================================
TaskFlow Kubernetes Deployment (Backend)
========================================"

# Step 1: Check Dapr
echo "[INFO] Step 1: Checking Dapr installation..."
if ! kubectl get namespace dapr-system &>/dev/null; then
    echo "[INFO] Installing Dapr..."
    dapr init -k
    echo "[INFO] Waiting for Dapr components..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/part-of=dapr -n dapr-system --timeout=300s
else
    echo "[INFO] Dapr already installed"
fi

# Step 2: Create secrets
echo "[INFO] Step 2: Creating secrets..."
kubectl apply -f secrets.yaml 2>/dev/null || echo "[INFO] Secrets already exist"

# Step 3: Deploy infrastructure
echo "[INFO] Step 3: Deploying infrastructure (Postgres, Redis, Kafka)..."
kubectl apply -f infrastructure/

echo "[INFO] Waiting for infrastructure to be ready..."
sleep 10

# Wait for Postgres
echo "[INFO] Waiting for Postgres..."
kubectl wait --for=condition=ready pod -l app=postgres -n default --timeout=180s || echo "[WARN] Postgres timeout, continuing..."

# Wait for Redis
echo "[INFO] Waiting for Redis..."
kubectl wait --for=condition=ready pod -l app=redis -n default --timeout=180s || echo "[WARN] Redis timeout, continuing..."

# Wait for Zookeeper
echo "[INFO] Waiting for Zookeeper..."
kubectl wait --for=condition=ready pod -l app=zookeeper -n kafka --timeout=180s || echo "[WARN] Zookeeper timeout, continuing..."

# Step 4: Deploy Dapr components
echo "[INFO] Step 4: Deploying Dapr components..."
kubectl apply -f dapr/

# Step 5: Build images (backend only, skip frontend)
echo "[INFO] Step 5: Building Docker images in Minikube..."
eval $(minikube docker-env)

cd ..
echo "[INFO] Building backend image..."
docker build -f backend/Dockerfile -t phase-ii-backend:latest .

echo "[INFO] Building Phase V service images..."
docker build -f backend/services/audit_logger/Dockerfile -t phase-ii-audit-logger:latest .
docker build -f backend/services/notification/Dockerfile -t phase-ii-notification-service:latest .
docker build -f backend/services/reminder/Dockerfile -t phase-ii-reminder-service:latest .
docker build -f backend/services/recurring_processor/Dockerfile -t phase-ii-recurring-processor:latest .

cd k8s

# Step 6: Deploy services
echo "[INFO] Step 6: Deploying backend services..."
kubectl apply -f services/backend/

echo "[INFO] Step 7: Deploying Phase V services..."
kubectl apply -f services/phase-v/

# Step 8: Wait for deployments
echo "[INFO] Step 8: Waiting for services to be ready..."
sleep 20

echo "
========================================
Deployment Status
========================================
"
kubectl get pods -n default
echo ""
kubectl get pods -n kafka
echo ""
kubectl get svc -n default

echo "
========================================
Deployment Complete!
========================================

Access your application:
  Backend API: kubectl port-forward service/backend 8000:8000 -n default

Check logs:
  kubectl logs -f deployment/backend -n default
  kubectl logs -f deployment/reminder-service -n default

Check status:
  kubectl get pods -A
"

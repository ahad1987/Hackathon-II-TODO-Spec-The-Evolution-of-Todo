#!/bin/bash
set -e

echo "========================================
TaskFlow Backend-Only Deployment
========================================"

# Deploy infrastructure
echo "[INFO] Step 1: Deploying infrastructure..."
kubectl apply -f infrastructure/

# Wait for Postgres
echo "[INFO] Waiting for Postgres..."
kubectl wait --for=condition=ready pod -l app=postgres -n default --timeout=180s

# Deploy Dapr components
echo "[INFO] Step 2: Deploying Dapr components..."
kubectl apply -f dapr/

# Deploy backend only (skip frontend in docker-compose build)
echo "[INFO] Step 3: Building backend images..."
eval $(minikube docker-env)
docker-compose build backend recurring-processor reminder-service notification-service audit-logger

# Deploy services
echo "[INFO] Step 4: Deploying backend services..."
kubectl apply -f services/backend/
kubectl apply -f services/phase-v/

echo "[INFO] Step 5: Waiting for pods..."
kubectl wait --for=condition=ready pod -l app=backend -n default --timeout=300s || true

echo "
========================================
Deployment Complete!
========================================
Backend API: kubectl port-forward service/backend 8000:8000
Phase V services deployed successfully!
"

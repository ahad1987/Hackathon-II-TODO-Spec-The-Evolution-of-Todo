#!/bin/bash

# TaskFlow Kubernetes Deployment Script
# This script automates the deployment of TaskFlow to Kubernetes

set -e  # Exit on error

NAMESPACE="${NAMESPACE:-default}"
CLUSTER_TYPE="${CLUSTER_TYPE:-minikube}"  # minikube, kind, docker-desktop, cloud

echo "========================================"
echo "TaskFlow Kubernetes Deployment"
echo "========================================"
echo "Namespace: $NAMESPACE"
echo "Cluster Type: $CLUSTER_TYPE"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Verify prerequisites
log_info "Step 1: Verifying prerequisites..."

if ! command -v kubectl &> /dev/null; then
    log_error "kubectl not found. Please install kubectl first."
    exit 1
fi

if ! command -v dapr &> /dev/null; then
    log_error "Dapr CLI not found. Please install Dapr CLI first."
    exit 1
fi

log_info "✓ kubectl found: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
log_info "✓ dapr found: $(dapr --version)"

# Step 2: Check cluster connection
log_info "Step 2: Checking Kubernetes cluster connection..."

if ! kubectl cluster-info &> /dev/null; then
    log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

log_info "✓ Connected to cluster: $(kubectl cluster-info | head -n 1)"

# Step 3: Check Dapr installation
log_info "Step 3: Checking Dapr installation on cluster..."

if ! kubectl get namespace dapr-system &> /dev/null; then
    log_warn "Dapr not installed on cluster. Installing now..."
    dapr init -k
    log_info "✓ Dapr installed successfully"
else
    log_info "✓ Dapr already installed"
fi

# Verify Dapr components
log_info "Verifying Dapr components..."
kubectl wait --for=condition=ready pod -n dapr-system --all --timeout=300s || {
    log_error "Dapr components failed to start"
    exit 1
}
log_info "✓ All Dapr components are ready"

# Step 4: Create namespace if not exists
if [ "$NAMESPACE" != "default" ]; then
    log_info "Step 4: Creating namespace '$NAMESPACE'..."
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    log_info "✓ Namespace ready"
fi

# Step 5: Check and create secrets
log_info "Step 5: Checking Kubernetes secrets..."

if [ ! -f "secrets.yaml" ]; then
    log_error "secrets.yaml not found. Please create it from secrets-template.yaml"
    echo ""
    echo "Run these commands:"
    echo "  cp secrets-template.yaml secrets.yaml"
    echo "  # Edit secrets.yaml with your actual secret values"
    echo "  # Then run this script again"
    exit 1
fi

# Check if secrets already exist
if kubectl get secret taskflow-postgres-secret -n $NAMESPACE &> /dev/null; then
    log_warn "Secrets already exist. Skipping secret creation."
    read -p "Do you want to recreate secrets? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting existing secrets..."
        kubectl delete -f secrets.yaml -n $NAMESPACE || true
        log_info "Creating new secrets..."
        kubectl apply -f secrets.yaml -n $NAMESPACE
    fi
else
    log_info "Creating secrets..."
    kubectl apply -f secrets.yaml -n $NAMESPACE
fi

log_info "✓ Secrets configured"

# Step 6: Build and load images (for local clusters)
if [ "$CLUSTER_TYPE" = "minikube" ]; then
    log_info "Step 6: Building images for Minikube..."
    eval $(minikube docker-env)
    cd ..
    docker-compose build backend frontend recurring-processor reminder-service notification-service audit-logger
    cd k8s
    log_info "✓ Images built in Minikube"

elif [ "$CLUSTER_TYPE" = "kind" ]; then
    log_info "Step 6: Building and loading images for Kind..."
    cd ..
    docker-compose build backend frontend recurring-processor reminder-service notification-service audit-logger

    log_info "Loading images into Kind cluster..."
    kind load docker-image phase-ii-backend:latest --name taskflow
    kind load docker-image phase-ii-frontend:latest --name taskflow
    kind load docker-image phase-ii-recurring-processor:latest --name taskflow
    kind load docker-image phase-ii-reminder-service:latest --name taskflow
    kind load docker-image phase-ii-notification-service:latest --name taskflow
    kind load docker-image phase-ii-audit-logger:latest --name taskflow
    cd k8s
    log_info "✓ Images loaded into Kind"

else
    log_warn "Skipping image build (cluster type: $CLUSTER_TYPE)"
    log_warn "Make sure your images are available in the registry"
fi

# Step 7: Deploy infrastructure
log_info "Step 7: Deploying infrastructure (Postgres, Redis, Kafka)..."

kubectl apply -f infrastructure/ -n $NAMESPACE

log_info "Waiting for infrastructure pods to be ready (this may take a few minutes)..."
kubectl wait --for=condition=ready pod -l tier=infrastructure -n $NAMESPACE --timeout=600s || {
    log_error "Infrastructure pods failed to start"
    kubectl get pods -n $NAMESPACE
    exit 1
}

log_info "✓ Infrastructure deployed and ready"

# Step 8: Deploy Dapr components
log_info "Step 8: Deploying Dapr pub/sub components..."

kubectl apply -f dapr/pubsub.yaml -n $NAMESPACE

# Wait a bit for components to be registered
sleep 5

log_info "✓ Dapr components deployed"

# Step 9: Deploy application services
log_info "Step 9: Deploying application services..."

kubectl apply -f services/phase-v/ -n $NAMESPACE

log_info "Waiting for application deployments to be ready (this may take several minutes)..."
kubectl wait --for=condition=available deployment --all -n $NAMESPACE --timeout=600s || {
    log_warn "Some deployments may not be ready. Checking status..."
    kubectl get deployments -n $NAMESPACE
    kubectl get pods -n $NAMESPACE
}

log_info "✓ Application services deployed"

# Step 10: Display status
echo ""
echo "========================================"
echo "Deployment Summary"
echo "========================================"
echo ""

log_info "Deployments:"
kubectl get deployments -n $NAMESPACE

echo ""
log_info "Pods:"
kubectl get pods -n $NAMESPACE

echo ""
log_info "Services:"
kubectl get services -n $NAMESPACE

echo ""
echo "========================================"
echo "✓ Deployment Complete!"
echo "========================================"
echo ""

log_info "To access the application:"
echo ""
echo "1. Port Forward (Quick Access):"
echo "   kubectl port-forward service/backend 8000:8000 -n $NAMESPACE"
echo "   kubectl port-forward service/frontend 3000:3000 -n $NAMESPACE"
echo ""
echo "2. Check monitoring status:"
echo "   curl http://localhost:8000/api/v1/monitoring/overview"
echo ""
echo "3. View logs:"
echo "   kubectl logs -l app=backend -n $NAMESPACE"
echo "   kubectl logs -l app=backend -c daprd -n $NAMESPACE  # Dapr sidecar"
echo ""
echo "4. Access frontend:"
echo "   http://localhost:3000 (after port-forward)"
echo ""

if [ "$CLUSTER_TYPE" = "minikube" ]; then
    echo "5. Minikube tunnel (for LoadBalancer services):"
    echo "   minikube tunnel"
    echo ""
fi

log_info "For troubleshooting, see k8s/DEPLOY.md"

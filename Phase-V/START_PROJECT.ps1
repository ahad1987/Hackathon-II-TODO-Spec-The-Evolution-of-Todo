# TaskFlow Project Startup Script
# Run this script every time you want to start the project

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TaskFlow Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if Minikube is running
Write-Host "[1/5] Checking Minikube status..." -ForegroundColor Yellow
$status = minikube status --format='{{.Host}}' 2>$null
if ($status -ne "Running") {
    Write-Host "Starting Minikube..." -ForegroundColor Yellow
    minikube start --driver=docker
} else {
    Write-Host "Minikube is already running" -ForegroundColor Green
}

# Step 2: Wait for Kubernetes API
Write-Host "[2/5] Waiting for Kubernetes API..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    $result = kubectl cluster-info 2>$null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}
if ($ready) {
    Write-Host "Kubernetes API is ready" -ForegroundColor Green
} else {
    Write-Host "Kubernetes API not ready, please wait and retry" -ForegroundColor Red
    exit 1
}

# Step 3: Restart pods to ensure fresh state
Write-Host "[3/5] Restarting application pods..." -ForegroundColor Yellow
kubectl rollout restart deployment/postgres deployment/redis -n default 2>$null
kubectl rollout restart statefulset/kafka -n kafka 2>$null
Start-Sleep -Seconds 5
kubectl rollout restart deployment/chat-api deployment/frontend -n default 2>$null

# Step 4: Wait for pods to be ready
Write-Host "[4/5] Waiting for pods to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=chat-api --timeout=180s 2>$null
kubectl wait --for=condition=ready pod -l app=frontend --timeout=120s 2>$null

# Step 5: Start minikube tunnel
Write-Host "[5/5] Starting Minikube tunnel..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  TaskFlow is Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend: http://127.0.0.1:3000" -ForegroundColor White
Write-Host "  Backend:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "  KEEP THIS WINDOW OPEN!" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C to stop the tunnel" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Start tunnel (this keeps running)
minikube tunnel

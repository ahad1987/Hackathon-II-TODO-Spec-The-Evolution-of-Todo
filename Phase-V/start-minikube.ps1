# TaskFlow Minikube Startup Script
# Run this after Minikube restart to get stable access to services

Write-Host "Starting TaskFlow on Minikube..." -ForegroundColor Cyan

# Step 1: Start Minikube if not running
$minikubeStatus = minikube status --format='{{.Host}}' 2>&1
if ($minikubeStatus -ne "Running") {
    Write-Host "Starting Minikube..." -ForegroundColor Yellow
    minikube start --driver=docker
}

# Step 2: Wait for Kubernetes API
Write-Host "Waiting for Kubernetes API..." -ForegroundColor Yellow
kubectl cluster-info 2>&1 | Out-Null
while ($LASTEXITCODE -ne 0) {
    Start-Sleep -Seconds 2
    kubectl cluster-info 2>&1 | Out-Null
}
Write-Host "Kubernetes API ready" -ForegroundColor Green

# Step 3: Restart infrastructure pods
Write-Host "Restarting infrastructure..." -ForegroundColor Yellow
kubectl rollout restart deployment postgres redis -n default 2>&1 | Out-Null
kubectl rollout restart deployment zookeeper -n kafka 2>&1 | Out-Null

# Step 4: Wait for infrastructure
Write-Host "Waiting for infrastructure pods..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s 2>&1 | Out-Null
kubectl wait --for=condition=ready pod -l app=redis --timeout=120s 2>&1 | Out-Null
kubectl wait --for=condition=ready pod -l app=zookeeper -n kafka --timeout=120s 2>&1 | Out-Null

# Step 5: Restart Kafka
kubectl rollout restart statefulset kafka -n kafka 2>&1 | Out-Null

# Step 6: Restart Dapr
Write-Host "Restarting Dapr system..." -ForegroundColor Yellow
kubectl rollout restart deployment -n dapr-system 2>&1 | Out-Null
Start-Sleep -Seconds 5

# Step 7: Restart application services
Write-Host "Restarting application services..." -ForegroundColor Yellow
kubectl rollout restart deployment chat-api frontend audit-logger notification-service recurring-processor reminder-service -n default 2>&1 | Out-Null

# Step 8: Start Minikube Tunnel (runs in new window)
Write-Host "Starting Minikube Tunnel..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command minikube tunnel" -WindowStyle Normal

# Step 9: Wait for services to be ready
Write-Host "Waiting for services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
kubectl wait --for=condition=ready pod -l app=kafka -n kafka --timeout=180s 2>&1 | Out-Null
kubectl rollout status deployment/chat-api --timeout=180s 2>&1 | Out-Null
kubectl rollout status deployment/frontend --timeout=180s 2>&1 | Out-Null

# Step 10: Print access URLs
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TaskFlow is Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend: http://127.0.0.1:3000" -ForegroundColor White
Write-Host "  Backend:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "  NOTE: Keep the Minikube Tunnel window open!" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

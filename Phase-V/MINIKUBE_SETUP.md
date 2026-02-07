# TaskFlow Minikube Permanent Fix

## Problem
Frontend showed "Network Error" after Minikube restarts because `minikube service --url` produces ephemeral ports that break cookies and CORS.

## Solution
Use **Minikube Tunnel** with LoadBalancer services to get stable localhost URLs:
- **Backend**: `http://127.0.0.1:8000`
- **Frontend**: `http://127.0.0.1:3000`

## How It Works
1. Services are configured as `LoadBalancer` type
2. `minikube tunnel` assigns `127.0.0.1` as the external IP
3. Backend CORS allows `http://127.0.0.1:3000`
4. Frontend calls API at `http://127.0.0.1:8000/api/v1`
5. Cookies work because both are on `127.0.0.1`

## After Minikube Restart

### Quick Start (PowerShell)
```powershell
.\start-minikube.ps1
```

### Manual Steps
1. Start Minikube:
   ```
   minikube start --driver=docker
   ```

2. Start tunnel (keep this window open):
   ```
   minikube tunnel
   ```

3. Restart deployments:
   ```
   kubectl rollout restart deployment chat-api frontend -n default
   ```

4. Wait for pods:
   ```
   kubectl rollout status deployment/chat-api --timeout=120s
   kubectl rollout status deployment/frontend --timeout=120s
   ```

5. Access app at: http://127.0.0.1:3000

## Verification Commands
```bash
# Backend health
curl http://127.0.0.1:8000/health/live

# CORS check
curl -X OPTIONS http://127.0.0.1:8000/api/v1/auth/login \
  -H "Origin: http://127.0.0.1:3000" \
  -H "Access-Control-Request-Method: POST" -I

# Login test
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

## Why This Is Permanent
1. **Stable URLs**: `127.0.0.1:8000` and `127.0.0.1:3000` never change
2. **Kubernetes-native**: Uses standard LoadBalancer + NodePort services
3. **No ephemeral ports**: Tunnel provides consistent external IPs
4. **CORS configured correctly**: Backend allows the exact frontend origin
5. **Cookies work**: Same domain (127.0.0.1) for both services

## Files Modified
- `Phase-II/k8s/services/chat-api-deployment.yaml` - CORS origins updated
- `Phase-II/k8s/services/frontend-deployment.yaml` - API URL updated
- `Phase-V/start-minikube.ps1` - PowerShell startup script created

## Current Status
- All pods running (2/2 for Dapr-enabled services)
- Kafka healthy with all topics
- Dapr sidecars connected
- CI/CD configured
- Monitoring shows "All Systems Operational"

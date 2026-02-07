# TaskFlow - How to Run the Project

## Quick Start (One Command)

Open PowerShell as Administrator and run:

```powershell
cd C:\Users\Ahad\Desktop\Hackathon-2-Phase-I\Phase-V
.\START_PROJECT.ps1
```

Keep the terminal window open (it runs the tunnel).

---

## Access URLs (Always the Same)

| Service | URL |
|---------|-----|
| **Frontend** | http://127.0.0.1:3000 |
| **Backend API** | http://127.0.0.1:8000 |
| **API Docs** | http://127.0.0.1:8000/docs |

---

## Manual Steps (If Script Fails)

### 1. Start Minikube
```powershell
minikube start --driver=docker
```

### 2. Wait for Pods
```powershell
kubectl get pods -A
# Wait until all pods show Running or 2/2 Ready
```

### 3. Start Tunnel (KEEP THIS RUNNING)
```powershell
minikube tunnel
```

### 4. Access the App
Open browser: http://127.0.0.1:3000

---

## Stopping the Project

1. Press `Ctrl+C` in the tunnel terminal
2. Optionally stop Minikube:
```powershell
minikube stop
```

---

## Troubleshooting

### "Connection Refused" Error
- Make sure `minikube tunnel` is running
- Check pods are ready: `kubectl get pods`

### Login Returns 401
- Clear browser cookies for 127.0.0.1
- Try in Incognito window

### Pods Not Starting
```powershell
kubectl rollout restart deployment/chat-api deployment/frontend
kubectl rollout restart deployment/postgres deployment/redis
```

### Check Service Status
```powershell
kubectl get svc chat-api frontend
# Should show EXTERNAL-IP as 127.0.0.1
```

---

## Architecture Summary

```
Browser (127.0.0.1:3000)
    |
    v
Frontend (Next.js) ---> Backend API (127.0.0.1:8000)
                             |
                             v
                    PostgreSQL + Redis + Kafka
                             |
                             v
                    Dapr Sidecars (Event Publishing)
                             |
                             v
            Audit Logger, Reminder, Notification Services
```

---

## What's Locked In

| Component | Configuration |
|-----------|--------------|
| Frontend Image | `phase-ii-frontend:latest` with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` |
| Backend CORS | Allows `http://127.0.0.1:3000` |
| Services | LoadBalancer type, exposed via tunnel at 127.0.0.1 |
| Ports | Frontend: 3000, Backend: 8000 (stable, never change) |

---

## Files Reference

| File | Purpose |
|------|---------|
| `START_PROJECT.ps1` | One-click startup script |
| `HOW_TO_RUN.md` | This guide |
| `MINIKUBE_SETUP.md` | Technical details of the fix |

---

## Why This Works

1. **Frontend rebuilt** with `http://127.0.0.1:8000` baked in at build time
2. **Minikube tunnel** exposes LoadBalancer services at stable `127.0.0.1`
3. **Ports never change** - always 3000 (frontend) and 8000 (backend)
4. **No ephemeral URLs** - doesn't depend on `minikube service --url`

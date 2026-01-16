# 🚀 TaskFlow Deployment Guide

Complete step-by-step guide for deploying TaskFlow to production.

## 📋 Pre-Deployment Checklist

- [x] All code committed to GitHub
- [x] Frontend builds successfully
- [x] Backend compiles without errors
- [x] Chatbot integrated and verified
- [x] Database models registered
- [x] Environment variables configured
- [x] Docker configurations ready
- [x] Netlify configuration ready

---

## 🌍 System Architecture

```
┌─────────────────────────────────────────────┐
│         User Browser (Netlify)              │
│  - Next.js 14 Frontend with AI Chatbot      │
│  - Tailwind CSS UI                          │
│  - Real-time Chat Widget                    │
└──────────────────┬──────────────────────────┘
                   │ HTTPS
                   ▼
┌─────────────────────────────────────────────┐
│      Backend API (HF Spaces / Docker)       │
│  - FastAPI Server (Port 7860)               │
│  - JWT Authentication                       │
│  - MCP Task Management Tools                │
│  - Chat Endpoint: /api/{user_id}/chat       │
└──────────────────┬──────────────────────────┘
                   │ PostgreSQL Driver
                   ▼
┌─────────────────────────────────────────────┐
│    Database (Neon PostgreSQL)               │
│  - Users Table                              │
│  - Tasks Table                              │
│  - Conversations Table (Chatbot)            │
│  - Messages Table (Chatbot)                 │
└─────────────────────────────────────────────┘
```

---

## 🔧 Phase 1: Backend Deployment (Hugging Face Spaces)

### Step 1.1: Prepare Hugging Face Account

```bash
# Create account at https://huggingface.co
# Create API token at https://huggingface.co/settings/tokens
# Note: You'll need HF_TOKEN for deployment
```

### Step 1.2: Create Hugging Face Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in details:
   - **Space name:** `taskflow-backend` (or your choice)
   - **License:** OpenRAIL License (or choose your preference)
   - **Space SDK:** Docker
   - **Visibility:** Public
4. Click **Create Space**

### Step 1.3: Configure Environment Variables

In Hugging Face Space settings, add these **Secrets**:

```
DATABASE_URL=postgresql+psycopg://user:password@host/dbname
BETTER_AUTH_SECRET=your-very-long-secret-key-at-least-32-characters
JWT_EXPIRY=86400
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://your-netlify-site.netlify.app
```

**Getting DATABASE_URL from Neon:**
1. Go to https://console.neon.tech
2. Click your project
3. Find "Connection string" → Copy PostgreSQL URL
4. Format: `postgresql+psycopg://user:password@host/dbname`

**Generate BETTER_AUTH_SECRET:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 1.4: Deploy Backend

```bash
# Option A: Using Git Push (HF Spaces)
cd Phase-II
git remote add huggingface https://huggingface.co/spaces/{your_username}/{space_name}
git push -u huggingface main

# Option B: Upload ZIP (if git not available)
# - Download as ZIP from GitHub
# - Upload to HF Spaces via web interface
```

### Step 1.5: Verify Backend Deployment

```bash
# Check health endpoint
curl https://your-space-url/health

# Expected response:
# {"status": "healthy", "version": "0.1.0", "environment": "production"}
```

---

## 🎨 Phase 2: Frontend Deployment (Netlify)

### Step 2.1: Prepare Netlify Account

1. Go to https://netlify.com
2. Sign up / Sign in with GitHub
3. Authorize Netlify to access your GitHub repositories

### Step 2.2: Deploy Frontend

**Option A: Direct GitHub Integration (Recommended)**

1. Click **"Add new site"** → **"Import an existing project"**
2. Select your GitHub repository
3. Select branch: `main`
4. Select base directory: `Phase-II/frontend`
5. Build command: `npm install --include=dev && npm run build`
6. Publish directory: `.next`
7. Click **Deploy site**

**Option B: Manual Deployment**

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy
cd Phase-II/frontend
netlify deploy --prod
```

### Step 2.3: Configure Environment Variables

In Netlify Site Settings → Build & Deploy → Environment:

```
NEXT_PUBLIC_API_URL=https://your-hf-space-url
NEXT_PUBLIC_BACKEND_URL=https://your-hf-space-url
NEXT_PUBLIC_BETTER_AUTH_SECRET=your-secret-key
NODE_ENV=production
```

### Step 2.4: Verify Frontend Deployment

1. Visit your Netlify URL (e.g., `https://your-site.netlify.app`)
2. You should see the TaskFlow login page
3. Chat widget should appear in bottom-right corner

---

## ✅ Phase 3: Post-Deployment Verification

### 3.1: Check Backend Health

```bash
# Get your HF Spaces URL
HF_URL="https://your-space-url"

# Test health endpoint
curl $HF_URL/health

# Expected: {"status":"healthy",...}
```

### 3.2: Test Frontend Access

1. Open your Netlify URL in browser
2. Verify page loads without errors
3. Check browser console for errors (F12)
4. Check Network tab to verify API calls

### 3.3: Test Authentication

```bash
curl -X POST https://your-hf-space-url/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Expected: {"user_id": "...", "token": "..."}
```

### 3.4: Test Chat Endpoint

```bash
# First, get a valid JWT token from signup/login
TOKEN="your_jwt_token"
USER_ID="your_user_id"
HF_URL="https://your-hf-space-url"

# Send a chat message
curl -X POST $HF_URL/api/$USER_ID/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show my tasks"
  }'

# Expected: {"conversation_id":"...", "response":"...", "status":"success"}
```

### 3.5: Test UI Features

1. **Login/Signup:** Create account
2. **Tasks:** Add, complete, delete tasks
3. **Chatbot:** Send messages to chatbot
4. **Chat History:** Send multiple messages
5. **Task Creation via Chat:** "Add task to buy milk"

---

## 🔐 Security Checklist

- [ ] Database URL is Neon PostgreSQL
- [ ] JWT secret is 32+ characters
- [ ] CORS origins are restricted to your domain
- [ ] Debug mode is OFF in production
- [ ] Environment is set to "production"
- [ ] No `.env` files are in git
- [ ] Secrets are only in platform settings
- [ ] HTTPS is enforced (Netlify/HF Spaces do this)

---

## 📊 Monitoring & Troubleshooting

### Logs

**Backend (HF Spaces):**
- Go to Space Settings → Logs
- Check for errors during startup

**Frontend (Netlify):**
- Go to Deployments → View logs
- Check for build errors

### Common Issues

**Issue: 502 Bad Gateway**
- Check backend is running: `curl https://your-space/health`
- Verify database connection
- Check environment variables

**Issue: CORS Errors**
- Verify frontend URL is in backend CORS_ORIGINS
- Check browser console for specific error

**Issue: Chat endpoint 401 Unauthorized**
- Verify JWT token is included
- Check token hasn't expired
- Verify user_id in URL matches token

**Issue: Database connection error**
- Verify DATABASE_URL is correct
- Check Neon database is running
- Verify connection limit not reached

### Enable Debug Mode

For troubleshooting, temporarily enable debug:

```
DEBUG=true
ENVIRONMENT=development
```

Then check logs for detailed error messages. Remember to disable after fixing!

---

## 🔄 Deployment Updates

To deploy updates:

1. **Make changes locally**
2. **Test thoroughly**
3. **Commit to GitHub:** `git commit -m "your message"`
4. **Push to main:** `git push origin main`
5. **Automatic redeploy:**
   - Frontend: Netlify auto-deploys (2-3 minutes)
   - Backend: Push to HF Spaces (5-10 minutes)

---

## 📞 Support & Resources

- **Hugging Face Docs:** https://huggingface.co/docs/hub
- **Netlify Docs:** https://docs.netlify.com
- **Neon Docs:** https://neon.tech/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Next.js Docs:** https://nextjs.org/docs

---

## ✨ What's Deployed

### Backend Features
- ✅ User authentication (JWT)
- ✅ Task management CRUD
- ✅ AI Chatbot with intent detection
- ✅ Conversation persistence
- ✅ MCP task tools (list, add, complete, delete, update)
- ✅ Health checks
- ✅ Error handling

### Frontend Features
- ✅ Login/Signup
- ✅ Task dashboard
- ✅ Create/complete/delete tasks
- ✅ AI Chat widget
- ✅ Responsive design
- ✅ Real-time updates

### Database
- ✅ Users table (authentication)
- ✅ Tasks table (task management)
- ✅ Conversations table (chat history)
- ✅ Messages table (chat messages)

---

## 🎉 You're Live!

After completing all phases, your TaskFlow application is live in production with:
- Full-stack authentication
- Real-time chat interface
- Task management with AI
- Persistent database
- Horizontal scaling ready

Enjoy your deployed application! 🚀

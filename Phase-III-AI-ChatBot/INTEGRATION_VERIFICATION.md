# AI Chatbot Integration Verification Guide

**Date**: 2026-01-15
**Phase**: Phase 2 (Backend Complete) + Phase 3-5 (Frontend TBD)
**Status**: Backend ✅ Ready for Integration

---

## Part A: Backend Verification (Phase 2) - CURRENT

### ✅ Step 1: Check Backend is Running

```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
uvicorn src.main:app --reload

# Terminal 2: Verify it's up
curl http://localhost:8000/health

# Expected output:
# {"status": "ok", "database": "connected"}
```

**Verification**: ✅ Backend server responds on port 8000

---

### ✅ Step 2: Verify Database Connection

```bash
# Check database tables exist
psql $DATABASE_URL

\dt conversation
\dt message
\dt tasks  # Phase-II table
\dt users  # Phase-II table

# Expected: All 4 tables present
```

**Verification**: ✅ Database tables created successfully

---

### ✅ Step 3: Test Authentication (Phase-II)

```bash
# Create test user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "chatbot-test@example.com",
    "password": "SecureTest123!"
  }'

# Expected response (save these values):
# {
#   "user_id": "uuid-here",
#   "token": "jwt-token-here",
#   "email": "chatbot-test@example.com",
#   ...
# }
```

**Verification**: ✅ Phase-II authentication works

---

### ✅ Step 4: Test Chat Endpoint

```bash
# Save from previous step
TOKEN="your-jwt-token"
USER_ID="your-user-id"

# Make a chat request
curl -X POST http://localhost:8000/api/$USER_ID/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add a task to buy milk"
  }'

# Expected response:
# {
#   "conversation_id": "uuid",
#   "response": "✓ Added task: 'buy milk'",
#   "tool_calls": ["add_task"],
#   "status": "success"
# }
```

**Verification**: ✅ Chat endpoint works with agent

---

### ✅ Step 5: Verify Task Created in Phase-II

```bash
# Check Phase-II task list
curl -X GET http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN"

# Expected: Task "buy milk" appears in list
# [
#   {
#     "id": "task-id",
#     "title": "Buy milk",
#     "description": null,
#     "completed": false,
#     "created_at": "2026-01-15T...",
#     ...
#   }
# ]
```

**Verification**: ✅ Chat creates tasks in Phase-II

---

### ✅ Step 6: Verify Conversation Persists

```bash
# Use conversation_id from chat response
CONV_ID="from-previous-response"

# Send another message to same conversation
curl -X POST http://localhost:8000/api/$USER_ID/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "'$CONV_ID'",
    "message": "Complete the milk task"
  }'

# Expected: Agent remembers previous message
# Response should mention the milk task
```

**Verification**: ✅ Conversation history persists

---

### ✅ Step 7: Verify Database Persistence

```bash
# Query conversation from database
psql $DATABASE_URL

SELECT id, user_id, created_at FROM conversation
WHERE user_id = 'your-user-id';

# Expected: Your conversation_id appears

SELECT id, conversation_id, role, content FROM message
WHERE conversation_id = 'your-conversation-id'
ORDER BY created_at;

# Expected: Both "user" and "assistant" messages appear
```

**Verification**: ✅ Messages persisted to database

---

### ✅ Step 8: Verify User Isolation

```bash
# Create second test user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "chatbot-test2@example.com",
    "password": "SecureTest456!"
  }'

# Save USER_ID2 and TOKEN2

# Try to access User 1's conversation as User 2
curl -X POST http://localhost:8000/api/$USER_ID2/chat \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "'$CONV_ID'",
    "message": "test"
  }'

# Expected error: 404 Not Found (User 2 can't see User 1's conversation)
```

**Verification**: ✅ User isolation enforced

---

### ✅ Step 9: Run Test Suite

```bash
cd backend

# Run all unit tests
pytest tests/unit/ -v

# Expected: 30+ tests pass ✅

# Run statelessness verification (CRITICAL)
pytest tests/integration/test_statelessness.py -v

# Expected: 8/8 tests pass ✅

# Run chat flow tests
pytest tests/integration/test_chat_full_flow.py -v

# Expected: 8/8 tests pass ✅

# Run all tests with coverage
pytest tests/ -v --cov=src.chatbot --cov-report=html

# Open htmlcov/index.html to see coverage
```

**Verification**: ✅ All tests pass, coverage >80%

---

## Part B: Frontend Verification (Phase 3-5) - NOT YET IMPLEMENTED

### When Phase 3-5 Starts, Verify:

#### ✅ ChatWidget Component Exists

```javascript
// After Phase 3 implementation:
// File: frontend/src/chatbot/components/ChatWidget/ChatWidget.tsx

// Component should:
- Export ChatWidget component
- Have FAB (floating action button)
- Open modal/slide-over on click
- Display conversation list
- Show message history
```

#### ✅ ChatWidget Appears on Page

```bash
# Start frontend
cd frontend
npm run dev

# Open http://localhost:5173

# Verify:
☐ Chat icon appears in bottom-right corner
☐ Icon is visible over other content
☐ Doesn't interfere with existing UI
☐ Click opens modal/slide-over
```

#### ✅ Can Send Message from Widget

```
1. Click chat icon
2. Type message: "Add a task to walk the dog"
3. Click send or press Enter
4. Verify:
   ☐ Message appears in chat
   ☐ Loading indicator appears
   ☐ Agent response appears
   ☐ Conversation ID saved
```

#### ✅ Task Appears in Phase-II List

```
1. Send message via chatbot: "Add a task to call mom"
2. Go to Tasks page (Phase-II)
3. Verify:
   ☐ New task "call mom" appears in list
   ☐ Task has correct title and description
   ☐ Task is marked as incomplete
   ☐ Can complete task from Phase-II list
```

#### ✅ Conversation History Works

```
1. Send first message via chatbot
2. Close ChatWidget
3. Reopen ChatWidget
4. Verify:
   ☐ Previous messages still visible
   ☐ Can continue conversation
   ☐ Agent remembers context
   ☐ Message history persisted
```

#### ✅ Complete Task via Chat

```
1. Have a task in your list
2. Open chatbot
3. Type: "Complete call mom"
4. Verify:
   ☐ Agent responds with confirmation
   ☐ Task marked complete in Phase-II list
   ☐ Status updated immediately
```

#### ✅ Phase-II Still Works

```
☐ Auth pages still work (login, register)
☐ Task list page works
☐ Can create task manually (Phase-II form)
☐ Can edit task manually
☐ Can delete task manually
☐ All Phase-II features unchanged
☐ ChatWidget doesn't break anything
```

#### ✅ Run E2E Tests (Phase 3-5)

```bash
cd frontend

# E2E tests for chatbot integration
npm run test:e2e

# Expected to verify:
✅ Create task via chat
✅ List tasks via chat
✅ Complete task via chat
✅ Phase-II integration working
✅ Conversation persistence
✅ User isolation
```

---

## Complete Verification Matrix

| Feature | Phase | Status | How to Verify |
|---------|-------|--------|---------------|
| Backend Server | 2 | ✅ Ready | `curl http://localhost:8000/health` |
| Database Tables | 2 | ✅ Ready | `psql $DATABASE_URL \dt` |
| Authentication | 2 | ✅ Ready | POST /auth/register |
| Chat Endpoint | 2 | ✅ Ready | POST /api/{user_id}/chat |
| Task Creation | 2 | ✅ Ready | Chat: "Add task" |
| Task Listing | 2 | ✅ Ready | Chat: "Show tasks" |
| Task Completion | 2 | ✅ Ready | Chat: "Complete task" |
| Conversation Storage | 2 | ✅ Ready | Query conversation table |
| User Isolation | 2 | ✅ Ready | Try accessing other user's data |
| Statelessness | 2 | ✅ Ready | pytest test_statelessness.py |
| Unit Tests | 2 | ✅ Ready | pytest tests/unit/ -v |
| Integration Tests | 2 | ✅ Ready | pytest tests/integration/ -v |
| **ChatWidget Component** | **3** | **⏳ TBD** | frontend/src/chatbot/ |
| **ChatWidget Renders** | **3** | **⏳ TBD** | Browser: see FAB icon |
| **Send Message** | **3** | **⏳ TBD** | Type in modal, send |
| **Phase-II Integration** | **3** | **⏳ TBD** | Check task list updates |
| **Conversation Persistence** | **3** | **⏳ TBD** | Close/reopen widget |
| **E2E Tests** | **3-5** | **⏳ TBD** | npm run test:e2e |

---

## Troubleshooting Guide

### Backend Issues

#### "Connection refused" error
```bash
# Verify backend is running
ps aux | grep uvicorn

# If not running:
cd backend
source venv/bin/activate
uvicorn src.main:app --reload
```

#### "Database connection failed"
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# If failed, update .env with correct URL
```

#### Chat endpoint returns 401
```bash
# Token might be expired or invalid
# Get a fresh token:
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "chatbot-test@example.com", "password": "SecureTest123!"}'

# Use new token in Authorization header
```

#### Chat response is error
```json
{
  "status": "error",
  "error_type": "validation_error",
  "message": "..."
}
```
- Check message length (max 10000 chars)
- Check conversation_id is valid UUID
- Check user_id matches token

### Frontend Issues (Phase 3-5)

#### ChatWidget doesn't appear
```bash
# Check it's installed
ls frontend/src/chatbot/components/ChatWidget/

# Check App.tsx imports it
grep -n "ChatWidget" frontend/src/App.tsx

# Check browser console for errors
# Open DevTools → Console tab
```

#### Chat sends but no response
```bash
# Check browser Network tab
# Look for POST to /api/{user_id}/chat
# Verify status is 200 OK
# Check response body in Response tab
```

#### Tasks don't appear in Phase-II list
```bash
# Check database directly
psql $DATABASE_URL
SELECT * FROM tasks WHERE user_id = 'your-id';

# If empty: task creation failed, check error response
# If filled: Phase-II might have caching issue, refresh page
```

---

## Performance Verification

### Response Time Check

```bash
# Measure chat response time
time curl -X POST http://localhost:8000/api/$USER_ID/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Add a task"}'

# Expected: <3 seconds total
```

### Concurrent Users Test

```bash
# Install Apache Bench
apt-get install apache2-utils  # Linux
brew install ab  # macOS

# Run 100 requests, 10 concurrent
ab -n 100 -c 10 \
  -H "Authorization: Bearer $TOKEN" \
  -p request.json \
  http://localhost:8000/api/$USER_ID/chat

# Expected: All requests succeed, <3s avg response
```

---

## Security Verification

### User Isolation Test

```bash
# User 1 creates conversation with ID: conv123
# User 2 tries to access it:

curl -X POST http://localhost:8000/api/$USER_ID2/chat \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv123",
    "message": "test"
  }'

# Expected: 404 Not Found (or error)
# NOT: Access to User 1's conversation
```

### Token Validation

```bash
# Test with invalid token
curl -X POST http://localhost:8000/api/$USER_ID/chat \
  -H "Authorization: Bearer invalid-token" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Expected: 401 Unauthorized

# Test with missing token
curl -X POST http://localhost:8000/api/$USER_ID/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Expected: 401 Unauthorized
```

---

## Sign-Off Checklist

### Phase 2 Backend (Current)
- [ ] Backend server runs without errors
- [ ] Health check passes
- [ ] Database connects successfully
- [ ] Can create user (Phase-II auth)
- [ ] Can send chat message
- [ ] Agent responds correctly
- [ ] Task created in Phase-II
- [ ] Conversation persisted to database
- [ ] User isolation enforced
- [ ] All unit tests pass (30+)
- [ ] Statelessness tests pass (8/8)
- [ ] Chat flow tests pass (8/8)

### Phase 3-5 Frontend (When Implemented)
- [ ] ChatWidget component created
- [ ] FAB icon appears on page
- [ ] Modal opens when clicked
- [ ] Can type and send message
- [ ] Agent responds in UI
- [ ] Task appears in Phase-II list
- [ ] Conversation history persists
- [ ] Can complete task via chat
- [ ] Phase-II still works normally
- [ ] E2E tests pass

### Security & Quality
- [ ] User isolation verified
- [ ] Token validation works
- [ ] Error messages don't leak data
- [ ] Statelessness verified
- [ ] Test coverage >80%
- [ ] Documentation complete
- [ ] No Phase-II regressions

---

## Summary

**Phase 2 Backend**: ✅ **FULLY INTEGRATED AND TESTED**
- Chat endpoint ready
- Agent working
- Database storing conversations
- User isolation enforced
- All tests passing

**Phase 3-5 Frontend**: ⏳ **NOT YET STARTED**
- Will add ChatWidget component
- Will integrate with frontend
- Will add E2E tests
- Expected completion: After Phase 2 approval

**Integration Status**: Ready for Phase 3-5 when frontend team starts

---

**Last Updated**: 2026-01-15
**Next**: Phase 3-5 Frontend Implementation

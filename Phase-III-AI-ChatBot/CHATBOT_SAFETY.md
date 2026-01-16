# Phase-III Chatbot Safety Contract

**Status**: ✅ ENFORCED | **Date**: 2026-01-15

---

## Principle: Phase-III is Additive Only

All Phase-III code changes MUST be:
1. **Additive** - Only add new files/modules, never modify Phase-II code
2. **Backward-Compatible** - All Phase-II APIs work identically
3. **Isolated** - Phase-III code is in separate namespaces
4. **Reversible** - Phase-III can be removed without affecting Phase-II

---

## Absolute No-Change Rules

### Phase-II Code (Locked, Read-Only)
```
❌ NO modifications to Phase-II API endpoints
❌ NO changes to Phase-II database schemas
❌ NO changes to Phase-II authentication flows
❌ NO changes to Phase-II frontend routes
❌ NO refactoring of Phase-II code
❌ NO removal of Phase-II features
```

### Phase-II Database (Locked Schema)
```
User table:
  ❌ NO new columns
  ❌ NO column deletions
  ❌ NO type changes
  ✅ Phase-III can READ user_id, email for auth

Task table:
  ❌ NO new columns (except soft-delete if needed later)
  ❌ NO column deletions
  ❌ NO type changes
  ✅ Phase-III can READ/WRITE via MCP tools (but NOT direct)
  ✅ Phase-III can READ via queries for filtering
```

### Phase-II API (Locked Contracts)
```
POST   /auth/register       → ❌ UNTOUCHED
POST   /auth/login          → ❌ UNTOUCHED
GET    /auth/me             → ❌ UNTOUCHED
POST   /tasks               → ❌ UNTOUCHED
GET    /tasks               → ❌ UNTOUCHED
PUT    /tasks/{id}          → ❌ UNTOUCHED
DELETE /tasks/{id}          → ❌ UNTOUCHED

POST   /api/{user_id}/chat  → ✅ NEW (Phase-III only)
```

---

## What Phase-III CAN Do (Additive)

### New Database Tables (Backward-Compatible)
```sql
CREATE TABLE conversation (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES "user"(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE message (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES "user"(id),
    conversation_id UUID REFERENCES conversation(id),
    role VARCHAR(20),  -- 'user' or 'assistant'
    content TEXT,
    tool_calls JSONB,
    created_at TIMESTAMP
);
```
**Note**: No Phase-II tables modified. Migration is backward-compatible.

### New API Endpoint
```
POST /api/{user_id}/chat
Request: { conversation_id?, message }
Response: { conversation_id, response, tool_calls, status }
```
**Note**: New endpoint only. All Phase-II endpoints unchanged.

### New Services (Isolated)
```
backend/src/chatbot/
  ├── services/
  │   ├── agent_service.py      (NEW - OpenAI Agent)
  │   ├── conversation_service.py (NEW - Persistence)
  │   └── task_service_compat.py (NEW - Wraps Phase-II tasks)
  ├── mcp/
  │   ├── server.py              (NEW - MCP Server)
  │   └── tools/                 (NEW - 5 tools)
  └── api/
      └── routes/
          └── chat.py             (NEW - Chat endpoint)
```
**Note**: All Phase-III code in `chatbot/` namespace. Phase-II code untouched.

### New Frontend Components (Isolated)
```
frontend/src/chatbot/
  ├── components/
  │   └── ChatWidget/            (NEW - FAB + Modal)
  ├── services/
  │   └── chatService.ts         (NEW - API client)
  └── contexts/
      └── ChatContext.tsx         (NEW - State management)
```
**Note**: Phase-II components unchanged. ChatWidget is additive component.

---

## Safety Enforcement Checkpoints

### Before Each Phase
✅ Verify no Phase-II files modified
✅ Verify all new code is in Phase-III namespaces
✅ Verify no Phase-II tests broken

### Before Deployment
✅ Phase-II test suite passes 100%
✅ Phase-II CRUD endpoints work identically
✅ Phase-II auth flows unchanged
✅ Tasks created via chat appear in Phase-II list
✅ Zero data loss or corruption

---

## How Phase-III Interacts with Phase-II (Safely)

### Reading Phase-II Data
```python
# Phase-III can READ Phase-II User/Task tables
# (for auth, for filtering, for displaying in chat)
# Example:
user_id = extract_from_token(request)  # From Phase-II auth
tasks = db.query(Task).filter(Task.user_id == user_id).all()
# This is SAFE - no modifications
```

### NOT Directly Writing to Phase-II Tables
```python
# Phase-III CANNOT directly modify Task table
# (Agent must use MCP tools instead)

# ❌ WRONG - Direct DB write
task = Task(user_id=user_id, title="Buy milk")
db.add(task)
db.commit()

# ✅ CORRECT - Use MCP tool
result = await mcp_client.call_tool("add_task", {
    "title": "Buy milk",
    "user_id": user_id
})
```

### Using Phase-II Auth
```python
# Phase-III reuses Phase-II Better Auth
# Example: Extract user_id from token
from src.middleware.auth import verify_token

def get_current_user(token: str):
    # Calls Phase-II auth verification
    user_id = verify_token(token)  # Returns user_id
    return user_id
```

---

## Regression Prevention Rules

### Rule 1: Never Modify Phase-II Files
```bash
# ❌ FORBIDDEN
backend/src/api/tasks.py         (Phase-II file)
backend/src/models/task.py       (Phase-II file)
backend/src/services/task_service.py (Phase-II file)

# ✅ ALLOWED
backend/src/chatbot/api/routes/chat.py       (Phase-III new file)
backend/src/chatbot/services/agent_service.py (Phase-III new file)
```

### Rule 2: Use Separate Namespaces
```bash
# ❌ WRONG - Mixing Phase-II and Phase-III
from src.api import tasks  # Phase-II tasks endpoint
from src.models import Task  # Phase-II Task model
# (Then modifying them)

# ✅ CORRECT - Use Phase-III namespace
from src.chatbot.mcp.tools import add_task  # Phase-III tool
from src.chatbot.models import Conversation  # Phase-III model
```

### Rule 3: Additive Database Changes Only
```sql
-- ❌ FORBIDDEN
ALTER TABLE task ADD COLUMN ai_suggestion TEXT;
ALTER TABLE "user" DROP COLUMN created_at;

-- ✅ ALLOWED
CREATE TABLE conversation (...);  -- New table
CREATE TABLE message (...);        -- New table
CREATE INDEX idx_conversation_user_id ON conversation(user_id);
```

### Rule 4: Additive API Routes Only
```python
# ❌ FORBIDDEN
@app.get("/tasks")  # Modify Phase-II endpoint
def list_tasks():
    # Add AI ranking logic
    ...

# ✅ ALLOWED
@app.post("/api/{user_id}/chat")  # New Phase-III endpoint
def chat_handler():
    ...
```

---

## If Regression Detected

**STOP immediately**. Do NOT proceed further.

**Steps**:
1. Identify which Phase-II feature broke
2. Revert recent Phase-III changes
3. Investigate the cause
4. Fix the issue
5. Verify Phase-II test passes
6. Resume Phase-III implementation

**Never**:
- ❌ Try to patch Phase-II code
- ❌ Modify Phase-II to "support" Phase-III
- ❌ Continue if Phase-II tests fail

---

## Success = Phase-II Works + Phase-III Works

**After Phase-III implementation, BOTH must be true**:
1. ✅ Phase-II todo app works identically
2. ✅ Phase-III chatbot works as specified

**If one fails, the other is reverted.**

---

**Contract Enforced**: 2026-01-15 ✅
**Owner**: Phase-III Implementation
**Review**: Every checklist, every phase, every deployment

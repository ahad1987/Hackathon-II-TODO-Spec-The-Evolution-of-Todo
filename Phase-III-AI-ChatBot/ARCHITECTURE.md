# Phase-III AI Chatbot Architecture

**Date**: 2026-01-15 | **Status**: ✅ Design Complete | **Task**: T006

---

## Overview

Phase-III adds an AI-powered chatbot to the existing Phase-II TODO Web App. The architecture maintains strict separation between Phase-II (black box) and Phase-III (new features), ensuring zero regression.

```
┌─────────────────────────────────────────────────────────┐
│          Phase-III AI Chatbot (NEW)                     │
├─────────────────────────────────────────────────────────┤
│  Frontend: ChatWidget FAB → Modal with Chat UI          │
│  Backend: POST /api/{user_id}/chat endpoint             │
│  Services: OpenAI Agent + MCP Server                    │
│  Database: Conversation, Message tables (new)           │
└─────────────────────────────────────────────────────────┘
                         ↓ uses
┌─────────────────────────────────────────────────────────┐
│          Phase-II TODO Web App (LOCKED)                 │
├─────────────────────────────────────────────────────────┤
│  Frontend: Task UI (unchanged)                          │
│  Backend: /tasks, /auth endpoints (unchanged)           │
│  Services: Task CRUD, Auth (unchanged)                  │
│  Database: User, Task tables (unchanged)                │
│  Auth: Better Auth (unchanged)                          │
└─────────────────────────────────────────────────────────┘
```

---

## Module Organization

### Backend Structure

```
backend/
├── src/
│   ├── api/                      (Phase-II)
│   │   ├── auth.py
│   │   ├── tasks.py
│   │   └── health.py
│   │
│   ├── models/                   (Phase-II)
│   │   ├── user.py
│   │   └── task.py
│   │
│   ├── services/                 (Phase-II)
│   │   ├── user_service.py
│   │   └── task_service.py
│   │
│   ├── chatbot/                  (Phase-III - ISOLATED)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py   (NEW - Conversation SQLModel)
│   │   │   └── message.py        (NEW - Message SQLModel)
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── agent_service.py  (NEW - OpenAI Agent orchestration)
│   │   │   └── conversation_service.py (NEW - Conversation persistence)
│   │   │
│   │   ├── mcp/
│   │   │   ├── __init__.py
│   │   │   ├── server.py         (NEW - MCP server initialization)
│   │   │   ├── error_handler.py  (NEW - Tool error handling)
│   │   │   ├── validators.py     (NEW - Input validation)
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── add_task.py          (NEW - Create task tool)
│   │   │       ├── list_tasks.py        (NEW - List tasks tool)
│   │   │       ├── complete_task.py     (NEW - Complete task tool)
│   │   │       ├── delete_task.py       (NEW - Delete task tool)
│   │   │       └── update_task.py       (NEW - Update task tool)
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py   (NEW - Auth middleware, user extraction)
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       └── chat.py       (NEW - POST /api/{user_id}/chat endpoint)
│   │   │
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── cors.py           (NEW - CORS configuration)
│   │   │
│   │   └── prompts/
│   │       └── system.md         (NEW - Agent system prompt)
│   │
│   ├── middleware/               (Phase-II)
│   │   └── auth.py
│   │
│   ├── database.py               (Phase-II)
│   ├── config.py                 (Phase-II)
│   └── main.py                   (Phase-II - app setup)
│
├── tests/
│   ├── unit/
│   │   ├── test_mcp_tools.py            (NEW)
│   │   ├── test_auth_validation.py      (NEW)
│   │   └── test_conversation_service.py (NEW)
│   │
│   └── integration/
│       ├── test_chat_endpoint.py        (NEW)
│       ├── test_chat_create_task.py     (NEW)
│       ├── test_phase2_regression.py    (NEW - Phase-II verification)
│       └── ...
│
├── alembic/
│   └── versions/
│       ├── 001_create_conversation.py   (NEW)
│       └── 002_create_message.py        (NEW)
│
└── requirements.txt              (Updated: add OpenAI, MCP SDK)
```

### Frontend Structure

```
frontend/
├── src/
│   ├── pages/                    (Phase-II)
│   │   ├── TasksPage.tsx        (Modified: +ChatWidget mount)
│   │   ├── DashboardPage.tsx    (Modified: +ChatWidget mount)
│   │   └── ...
│   │
│   ├── components/              (Phase-II)
│   │   ├── TaskList.tsx
│   │   ├── TaskForm.tsx
│   │   └── ...
│   │
│   ├── chatbot/                 (Phase-III - ISOLATED)
│   │   ├── components/
│   │   │   ├── ChatWidget/
│   │   │   │   ├── ChatWidget.tsx      (NEW - FAB + Modal container)
│   │   │   │   ├── ChatPanel.tsx       (NEW - Message display area)
│   │   │   │   ├── ChatInput.tsx       (NEW - User input field)
│   │   │   │   ├── ChatMessage.tsx     (NEW - Message rendering)
│   │   │   │   ├── ChatWidget.module.css (NEW - Styling)
│   │   │   │   └── types.ts            (NEW - TypeScript types)
│   │   │   └── index.ts
│   │   │
│   │   ├── services/
│   │   │   ├── chatService.ts          (NEW - API client for /chat endpoint)
│   │   │   ├── conversationService.ts  (NEW - Conversation state sync)
│   │   │   └── index.ts
│   │   │
│   │   ├── contexts/
│   │   │   ├── ChatContext.tsx         (NEW - React Context for chat state)
│   │   │   └── types.ts
│   │   │
│   │   └── hooks/
│   │       ├── useChat.ts              (NEW - Chat state hook)
│   │       └── useConversation.ts      (NEW - Conversation hook)
│   │
│   ├── services/                (Phase-II)
│   │   ├── authService.ts
│   │   ├── taskService.ts
│   │   └── ...
│   │
│   ├── types/                   (Phase-II)
│   │   ├── user.ts
│   │   ├── task.ts
│   │   └── ...
│   │
│   └── App.tsx                  (Modified: +ChatContext, +ChatWidget)
│
├── tests/
│   ├── unit/
│   │   ├── components/
│   │   │   └── test_ChatWidget.tsx     (NEW)
│   │   ├── services/
│   │   │   └── test_chatService.ts     (NEW)
│   │   └── contexts/
│   │       └── test_ChatContext.tsx    (NEW)
│   │
│   ├── integration/
│   │   ├── test_chat_widget_isolation.ts (NEW)
│   │   └── test_phase2_integration.ts    (NEW)
│   │
│   └── e2e/
│       ├── test_create_task_flow.ts    (NEW)
│       ├── test_list_tasks_flow.ts     (NEW)
│       └── test_complete_task_flow.ts  (NEW)
│
└── package.json                 (Updated: add ChatKit, openai SDK)
```

---

## Data Flow

### Chat Request Lifecycle (Stateless)

```
1. User types in ChatWidget
         ↓
2. ChatInput sends message to chatService
         ↓
3. chatService calls POST /api/{user_id}/chat
         ↓
4. Backend receives request
   - Authenticate: verify JWT token
   - Extract: user_id from token
   - Load: conversation history from DB
         ↓
5. Agent executes with history + user message
   - Intent detection (create/read/update/complete/delete)
   - Tool selection (add_task, list_tasks, etc.)
   - Tool invocation (via MCP tools)
         ↓
6. MCP Tools execute (stateless)
   - Validate input
   - Query/mutate database
   - Return results
         ↓
7. Agent assembles response
   - Format results for user
   - Provide confirmation/feedback
         ↓
8. Backend persists message + response
   - Save user message to DB
   - Save assistant response to DB
   - Save tool calls to DB
         ↓
9. Backend returns response to frontend
   - conversation_id
   - response text
   - tool_calls list
   - status
         ↓
10. ChatPanel displays response
    - Render messages
    - Update conversation history
    - Preserve conversation_id for next message
         ↓
11. Server releases all in-memory state
    - No state retained between requests
```

### Database Schema Integration

```
Phase-II (Locked):
┌─────────────────┐
│ "user" table    │
├─────────────────┤
│ id (PK)         │
│ email           │
│ password_hash   │
│ created_at      │
│ updated_at      │
└─────────────────┘
       ↑
       │ FK
       │
┌─────────────────┬─────────────────┬──────────────────┐
│ "task" table    │ conversation(*) │ message(*)       │
├─────────────────┼─────────────────┼──────────────────┤
│ id (PK)         │ id (PK)         │ id (PK)          │
│ user_id (FK)    │ user_id (FK)    │ user_id (FK)     │
│ title           │ created_at      │ conversation_id  │
│ description     │ updated_at      │ role             │
│ completed       │                 │ content          │
│ created_at      │                 │ tool_calls       │
│ updated_at      │                 │ created_at       │
└─────────────────┴─────────────────┴──────────────────┘
       ↑                                      ↑
       └──────────────────────────────────────┘
  Phase-II (locked, read-only via MCP tools)
```

**Rules**:
- User, Task tables: Phase-II controls, read-only for Phase-III
- Conversation, Message: Phase-III owns, new tables
- All tables scoped by user_id (strict isolation)

---

## API Contract

### Phase-II Endpoints (Unchanged)
```
POST   /auth/register
POST   /auth/login
GET    /auth/me
POST   /tasks
GET    /tasks
PUT    /tasks/{id}
DELETE /tasks/{id}
GET    /health
```

### Phase-III Endpoint (New)
```
POST /api/{user_id}/chat

Request:
{
  "conversation_id"?: "uuid",  // Optional, creates new if omitted
  "message": "user input text" // Required
}

Response:
{
  "conversation_id": "uuid",
  "response": "assistant response text",
  "tool_calls": ["add_task", "complete_task"],
  "status": "success" | "error"
}

Error Responses:
401 Unauthorized (missing/invalid token)
403 Forbidden (user_id mismatch)
422 Unprocessable Entity (validation error)
500 Internal Server Error (logged, no details to user)
```

---

## Authentication & Authorization

### User Identification
```
1. Request arrives with Authorization: Bearer <JWT_TOKEN>
2. Token validated using Phase-II Better Auth configuration
3. user_id extracted from token claims
4. user_id used for all database queries (WHERE user_id = :user_id)
5. Prevents cross-user access
```

### User Scoping Rules
```
✅ Users can only access their own tasks
✅ Users can only access their own conversations
✅ Agents can only operate on user's tasks
✅ Database queries filtered by user_id
✅ API responses filtered by user_id
```

---

## Isolation Boundaries

### Phase-III Does NOT Touch
- ❌ Phase-II API routes
- ❌ Phase-II models (User, Task)
- ❌ Phase-II services
- ❌ Phase-II middleware
- ❌ Phase-II UI components
- ❌ Phase-II authentication logic
- ❌ Phase-II database (only reads Task table via MCP tools)

### Phase-III OWNS (Isolated)
- ✅ chatbot/ namespace (all Phase-III code)
- ✅ Conversation, Message models
- ✅ MCP tools and server
- ✅ Agent service
- ✅ Chat endpoint
- ✅ ChatWidget component
- ✅ Chat services and contexts

### Phase-III CAN READ (Phase-II)
- ✅ User table (for authentication)
- ✅ Task table (to list user's tasks)
- ✅ Phase-II API endpoints (to verify Phase-II works)

### Phase-III MUST WRITE THROUGH (MCP Tools)
- ✅ Task creation → add_task tool
- ✅ Task updates → update_task tool
- ✅ Task completion → complete_task tool
- ✅ Task deletion → delete_task tool
- ✅ Task listing → list_tasks tool (reads DB)

---

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (shared with Phase-II)
- **ORM**: SQLModel (shared with Phase-II)
- **Database**: Neon PostgreSQL (shared)
- **AI**: OpenAI Agents SDK
- **Tools**: MCP SDK (Model Context Protocol)
- **Auth**: Better Auth (shared Phase-II)
- **Migrations**: Alembic (shared Phase-II)

### Frontend
- **Language**: TypeScript / React
- **UI Library**: OpenAI ChatKit
- **State Management**: React Context (Phase-III only)
- **Build**: Vite (Phase-II standard)

### Database
- **Provider**: Neon PostgreSQL
- **Driver**: psycopg2 (Python)
- **ORM**: SQLModel
- **Migration Tool**: Alembic

---

## Safety & Guarantees

### Stateless Request Handling
```
✅ NO in-memory conversation state
✅ NO server affinity required
✅ Server restart = zero data loss
✅ Horizontal scaling enabled
```

### User Isolation
```
✅ All queries scoped by user_id
✅ Users cannot access other users' data
✅ Authorization checks on every request
✅ Error messages don't leak data
```

### Phase-II Protection
```
✅ All Phase-II tests must pass
✅ Phase-II CRUD must work identically
✅ Phase-II auth must be unchanged
✅ Zero modifications to Phase-II code
```

### Data Integrity
```
✅ Database transactions for atomic operations
✅ Foreign key constraints enforced
✅ No duplicate messages in conversation
✅ No data loss on failures
```

---

## Deployment Model

### Development
- Phase-III backend runs on localhost:8000 (alongside Phase-II)
- Phase-III frontend dev server on localhost:5173
- Shared database: local PostgreSQL or Neon dev instance

### Staging
- Phase-III backend: Netlify/Railway (with Phase-II)
- Phase-III frontend: Vercel (with Phase-II)
- Shared database: Neon staging instance

### Production
- Phase-III backend: Netlify/Railway (integrated with Phase-II)
- Phase-III frontend: Vercel (integrated with Phase-II)
- Shared database: Neon production instance

---

## Monitoring & Observability

### Logging
```
✅ Chat requests logged (user_id, message, response)
✅ MCP tool calls logged (tool name, inputs, outputs)
✅ Errors logged with context
✅ No sensitive data in logs
```

### Metrics
```
✅ Chat request latency (p95, p99)
✅ Tool execution time per tool
✅ Database query time
✅ Error rates by type
```

### Alerts
```
✅ Phase-II test failures
✅ Chat endpoint errors (5xx)
✅ High latency (>3 seconds)
✅ User isolation violations
```

---

**Architecture Verified**: 2026-01-15 ✅
**Ready for Implementation**: Phase 2 Foundational (56 tasks)

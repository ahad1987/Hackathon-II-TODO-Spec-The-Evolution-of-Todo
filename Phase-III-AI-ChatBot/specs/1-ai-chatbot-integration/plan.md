# Implementation Plan: AI-Powered Todo Chatbot (Phase-III)

**Branch**: `1-ai-chatbot-integration` | **Date**: 2026-01-15 | **Spec**: `specs/1-ai-chatbot-integration/spec.md`

**Input**: Feature specification from `/specs/1-ai-chatbot-integration/spec.md` with 7 prioritized user stories, 70+ functional requirements, 14 success criteria, and 6 edge cases.

---

## Summary

Build a fully functional AI-powered Todo chatbot integrated with Phase-II TODO Web App via stateless FastAPI backend, OpenAI Agents SDK, and MCP tool protocol. Chat widget provides natural language CRUD operations on todos through persistent database-backed conversations. Zero regressions to Phase-II; additive-only changes with strict user isolation and stateless server architecture.

**Technical Approach**:
1. Extend Phase-II database with `Conversation` and `Message` models (backward-compatible)
2. Build MCP server exposing 5 task-management tools (add_task, list_tasks, complete_task, delete_task, update_task)
3. Implement stateless FastAPI chat endpoint (`POST /api/{user_id}/chat`) with conversation history loading
4. Integrate OpenAI Agents SDK for intent detection and tool selection
5. Embed OpenAI ChatKit UI as floating chat widget in Phase-II frontend (non-intrusive, fully isolated)
6. Enforce strict user isolation and stateless operation guarantees

---

## Technical Context

**Language/Version**: Python 3.11+ (phase-II standard)

**Primary Dependencies**:
- FastAPI (existing Phase-II backend)
- OpenAI Python SDK + Agents SDK (official)
- MCP SDK (official Model Context Protocol)
- SQLModel (existing Phase-II ORM)
- Neon PostgreSQL (existing Phase-II database)
- Better Auth (existing Phase-II authentication)
- OpenAI ChatKit (official React UI component)

**Storage**: Neon PostgreSQL (Phase-II shared database)

**Testing**: pytest (Phase-II standard), integration tests for Phase-II regression

**Target Platform**: Web (full-stack: Python backend + React frontend)

**Project Type**: Web application with backend + frontend components

**Performance Goals**:
- Chat response latency: p95 ≤ 3 seconds
- MCP tool execution: ≤ 500ms per tool call
- Support 100 concurrent chat users
- Database query response: ≤ 100ms

**Constraints**:
- Zero Phase-II regressions (all existing tests pass)
- Stateless backend (no in-memory conversation state)
- User-scoped database queries (strict isolation)
- MCP tools exclusively for task mutations (no direct DB writes)

**Scale/Scope**:
- Phase III MVP: Natural language CRUD for single user's tasks
- Initial deployment: <10K conversations/day
- Horizontal scalability: Stateless design supports unlimited users

---

## Constitution Check

**GATE: Must pass before implementation. Re-check after design.**

### Principle I: Phase-II Integrity (CRITICAL)
- ✅ PASS: Plan extends database with new tables (Conversation, Message) only; existing Task table unchanged
- ✅ PASS: Phase-II API endpoints unchanged; chat endpoint is new additive endpoint
- ✅ PASS: Better Auth unchanged; chat uses existing user authentication
- ✅ PASS: Phase-II frontend routes unmodified; chat widget is additive UI layer
- ✅ PASS: Regression testing explicitly planned (Phase 5)
- **Requirement**: All Phase-II CRUD tests must pass before Phase-III deployment

### Principle II: Stateless Server Architecture
- ✅ PASS: Chat request loads conversation history from DB, processes, persists response
- ✅ PASS: No in-memory conversation state; each request is independent
- ✅ PASS: Server restart does not affect conversations (database is source of truth)
- ✅ PASS: Enables horizontal scaling (any instance can process any request)
- **Requirement**: Every chat request must fetch full state from database

### Principle III: Full CRUD via Natural Language
- ✅ PASS: Spec covers all 5 CRUD operations (create, list, read via describe, update, delete)
- ✅ PASS: OpenAI Agent handles intent detection
- ✅ PASS: User stories P1/P2 cover CRUD workflows
- **Requirement**: Agent must understand task intent from free-form text

### Principle IV: Immutable API Contract
- ✅ PASS: Chat endpoint locked: POST /api/{user_id}/chat
- ✅ PASS: Request/response schema defined in spec (conversation_id, message, response)
- ✅ PASS: No breaking changes to API contract allowed
- **Requirement**: API contract must be versioned if ever changed

### Principle V: MCP Tooling Constitution
- ✅ PASS: Exactly 5 tools defined: add_task, list_tasks, complete_task, delete_task, update_task
- ✅ PASS: All task mutations go through tools (no direct DB access from agent)
- ✅ PASS: Tools are stateless (database-backed only)
- ✅ PASS: Tool error handling prevents agent crashes
- **Requirement**: No agent-direct database manipulation

### Principle VI: Agent Behavior Standards
- ✅ PASS: Intent detection via OpenAI Agents SDK
- ✅ PASS: Tool selection logic defined (spec FR-013)
- ✅ PASS: Multi-tool chaining supported (spec FR-014)
- ✅ PASS: Confirmations for destructive operations (spec FR-015)
- ✅ PASS: Error handling graceful (spec FR-017)
- **Requirement**: Agent behavior validated against spec scenarios

### Principle VII: Database Schema & Persistence
- ✅ PASS: Conversation model defined (user_id, id, created_at, updated_at)
- ✅ PASS: Message model defined (user_id, id, conversation_id, role, content, created_at)
- ✅ PASS: Task model unchanged (backward-compatible)
- ✅ PASS: All user-scoped queries (WHERE user_id = :user_id)
- ✅ PASS: Migration strategy: Alembic for schema changes, no downtime
- **Requirement**: All schema changes backward-compatible

---

## Project Structure

### Documentation (Phase-III Feature)

```text
specs/1-ai-chatbot-integration/
├── spec.md                          # Specification (complete)
├── plan.md                          # This file (implementation plan)
├── research.md                      # Phase 0 (research findings)
├── data-model.md                    # Phase 1 (entity definitions)
├── quickstart.md                    # Phase 1 (setup & integration guide)
├── contracts/                       # Phase 1 (API contracts)
│   ├── chat-api.openapi.yml         # Chat endpoint contract
│   └── mcp-tools.schema.json        # MCP tool schemas
├── checklists/
│   └── requirements.md              # Quality checklist (validated)
└── tasks.md                         # Phase 2 output (NOT created by /sp.plan)
```

### Source Code Structure

```text
# Backend: FastAPI application (extends Phase-II backend)
backend/
├── src/
│   ├── models/                      # Database models
│   │   ├── conversation.py          # Conversation model (NEW)
│   │   ├── message.py               # Message model (NEW)
│   │   └── task.py                  # Task model (unchanged, Phase-II)
│   ├── services/                    # Business logic
│   │   ├── chat_service.py          # Chat request handling (NEW)
│   │   ├── conversation_service.py  # Conversation persistence (NEW)
│   │   ├── mcp_server.py            # MCP tool definitions (NEW)
│   │   ├── agent_service.py         # OpenAI agent orchestration (NEW)
│   │   └── task_service.py          # Task operations (extends Phase-II)
│   ├── api/
│   │   ├── routes/
│   │   │   └── chat.py              # Chat endpoint (NEW)
│   │   └── dependencies.py          # Auth/user injection (extends Phase-II)
│   └── mcp/                         # MCP tool implementations (NEW)
│       ├── add_task_tool.py
│       ├── list_tasks_tool.py
│       ├── complete_task_tool.py
│       ├── delete_task_tool.py
│       └── update_task_tool.py
└── tests/
    ├── unit/
    │   ├── test_chat_service.py     # Chat service tests (NEW)
    │   ├── test_mcp_tools.py        # MCP tool tests (NEW)
    │   └── test_agent_behavior.py   # Agent behavior tests (NEW)
    ├── integration/
    │   ├── test_chat_api.py         # Chat endpoint tests (NEW)
    │   ├── test_phase2_regression.py # Phase-II regression tests (NEW)
    │   └── test_conversation_persistence.py # Persistence tests (NEW)
    └── contract/
        └── test_mcp_contracts.py    # MCP tool contract tests (NEW)

# Frontend: React application (extends Phase-II frontend)
frontend/
├── src/
│   ├── components/
│   │   ├── ChatWidget/              # Chat widget component (NEW)
│   │   │   ├── ChatWidget.tsx       # Main widget FAB + modal
│   │   │   ├── ChatPanel.tsx        # Conversation display
│   │   │   ├── ChatInput.tsx        # User message input
│   │   │   └── ChatMessage.tsx      # Message rendering
│   │   └── [Phase-II components unchanged]
│   ├── pages/
│   │   ├── TasksPage.tsx            # Extends Phase-II (adds chat widget)
│   │   ├── DashboardPage.tsx        # Extends Phase-II (adds chat widget)
│   │   └── [Phase-II pages unchanged]
│   ├── services/
│   │   ├── chatService.ts           # Chat API client (NEW)
│   │   ├── conversationService.ts   # Conversation state (NEW)
│   │   └── [Phase-II services unchanged]
│   ├── contexts/
│   │   └── ChatContext.tsx          # Chat state management (NEW, using ChatKit)
│   └── [Phase-II structure unchanged]
└── tests/
    ├── unit/
    │   └── components/
    │       └── ChatWidget.test.tsx  # Widget tests (NEW)
    └── integration/
        └── test_chat_widget_isolation.test.tsx # Phase-II integration tests (NEW)
```

**Structure Decision**: Web application (backend + frontend) with additive components for chat. Phase-II structure completely unchanged; chat widget is isolated React component layer. MCP server runs within FastAPI backend process.

---

## Planning Phases

### Phase 0: Research & Validation

**Objective**: Resolve all technical unknowns and validate feasibility

**Tasks**:
1. Research OpenAI Agents SDK integration patterns for task-based agents
2. Research MCP SDK implementation patterns for stateless tool definitions
3. Research OpenAI ChatKit React component integration into existing React apps
4. Research FastAPI best practices for stateless conversation handling
5. Research conversation history management in stateless systems (DB persistence)
6. Research Phase-II Better Auth token structure and scope
7. Validate PostgreSQL schema extension compatibility (no downtime migrations)
8. Document current Phase-II API structure and identify integration points

**Outputs**:
- `research.md` with findings, decisions, rationale, and alternatives

**Validation Gate**:
- ✅ All unknowns resolved
- ✅ Integration points identified
- ✅ No conflicts with Phase-II detected

---

### Phase 1: Foundation & Safety Setup

**Objective**: Establish safe integration baseline with Phase-II

**Design Tasks**:

1.1 **Database Schema Design** (Additive Only)
- Design `Conversation` model: user_id (FK), id (UUID PK), created_at, updated_at
- Design `Message` model: user_id (FK), id (UUID PK), conversation_id (FK), role, content, created_at
- Design schema migration strategy (Alembic, backward-compatible)
- Verify Phase-II Task table remains unchanged
- **No modifications** to Phase-II existing tables

1.2 **MCP Tool Contracts** (Stateless Design)
- Define `add_task` tool contract: inputs (title, description, user_id), outputs, error cases
- Define `list_tasks` tool contract: inputs (user_id, filter), outputs, error cases
- Define `complete_task` tool contract: inputs (task_id, user_id), outputs, idempotency
- Define `delete_task` tool contract: inputs (task_id, user_id), outputs
- Define `update_task` tool contract: inputs (task_id, user_id, updates), outputs, validation
- Each tool must: operate on database only, be stateless, return structured responses
- **Enforce**: No in-memory state, no agent-direct DB access

1.3 **Chat API Contract** (Immutable)
- Define POST /api/{user_id}/chat endpoint
- Request schema: conversation_id (optional), message (required)
- Response schema: conversation_id, response, tool_calls, status
- Error responses: 401 Unauthorized, 422 Validation Error, 500 Server Error
- **Enforce**: No breaking changes allowed

1.4 **Authentication & User Isolation** (Phase-II Integration)
- Design Better Auth token extraction from request
- Design user_id scoping for all database queries
- Design authorization checks (users can only access own tasks/conversations)
- Design error responses for unauthorized access
- **Verify**: Phase-II auth system unchanged

1.5 **Stateless Request Lifecycle** (Database-Backed)
- Load conversation history from DB by conversation_id
- Append user message to conversation context
- Execute OpenAI Agent with MCP tools and history
- Persist assistant response (agent output + tool calls) to Message table
- Return response to client
- **Release all in-memory state after response**

1.6 **Chat Widget Design** (Phase-II Frontend Integration)
- Design floating action button (FAB) placement (bottom-right, non-intrusive)
- Design modal/slide-over panel for conversation UI
- Design open/close behavior (preserves conversation_id)
- Design responsive layout (desktop/tablet/mobile)
- Design accessibility (keyboard navigation, screen readers)
- **Constraint**: Must NOT affect Phase-II routes or components
- **Constraint**: Must be fully removable without side effects
- **Integration**: Use OpenAI ChatKit component; manage chat context with React Context

1.7 **Security & Auth Validation Design**
- Design Better Auth token validation middleware
- Design user isolation enforcement (all queries scoped)
- Design CORS configuration (Phase-II boundary respected)
- Design input sanitization for user messages
- Design error message strategy (no sensitive data leaks)
- **Verify**: No new authentication system introduced

**Outputs**:
- `data-model.md` (entity definitions, relationships, constraints)
- `contracts/chat-api.openapi.yml` (OpenAPI schema for chat endpoint)
- `contracts/mcp-tools.schema.json` (JSON Schema for tool definitions)
- `quickstart.md` (setup, integration guide, local development)

**Validation Gate**:
- ✅ Constitution Check re-evaluated (Phase 1 design conforms)
- ✅ All contracts defined, unambiguous, testable
- ✅ No Phase-II changes required
- ✅ User isolation design validated
- ✅ Stateless design validated

---

### Phase 2: Backend MCP Server & Agent Integration

**Objective**: Build MCP tool layer and AI agent orchestration

**Implementation Strategy** (No Code, Only Plan):

2.1 **MCP Server Setup**
- Initialize MCP SDK in FastAPI backend
- Register all 5 tools with MCP server
- Define tool input/output schemas (JSON Schema)
- Implement tool execution with database persistence (stateless)
- Test: Unit tests for each tool contract

2.2 **Task Management Tools** (Stateless Implementations)
- `add_task`: Accept title/description, validate, create Task row, return id + task data
- `list_tasks`: Query Task table (user-scoped), filter by status, order by created_at desc, return list
- `complete_task`: Find task by id (user-scoped), set completed=true, update timestamp, return task
- `delete_task`: Find task by id (user-scoped), delete row, return confirmation
- `update_task`: Find task by id (user-scoped), update fields, return changes + task
- **Each tool**: User-scoped, database-backed, idempotent where applicable, clear error handling

2.3 **OpenAI Agent Setup**
- Initialize Agents SDK with OpenAI API key
- Configure agent with system prompt (task-focused, confirmation-based)
- Register MCP tools with agent
- Implement intent detection (create, read, update, complete, delete task intents)
- Implement tool selection logic (agent chooses tool based on intent)
- Implement multi-tool chaining (e.g., list_tasks → complete_task)
- **Constraint**: Agent must confirm destructive operations (delete, complete)
- **Constraint**: Agent must never hallucinate task IDs

2.4 **Conversation Persistence Service**
- Implement conversation creation (POST /api/{user_id}/chat, new conversation_id)
- Implement conversation history loading (fetch all messages for conversation_id)
- Implement message persistence (store user message, then assistant response)
- Implement user scoping (WHERE user_id = :user_id)
- **Guarantee**: No conversation data retained in memory after response

2.5 **Chat Request Handling**
- Implement stateless request flow:
  1. Authenticate request (verify token, extract user_id)
  2. Load conversation history from DB
  3. Append user message to history
  4. Execute agent with MCP tools + history
  5. Persist assistant response (message + tool calls)
  6. Return response to client
  7. Release all in-memory state
- Implement error handling (agent errors, tool errors, DB errors)
- Implement retry logic (idempotent tool calls)

2.6 **Testing Strategy** (Phase 2)
- Unit tests: Each MCP tool contract validation
- Unit tests: Agent intent detection (various phrasings)
- Integration tests: Chat endpoint with Phase-II task data
- Integration tests: Conversation persistence (create, load, append)
- Contract tests: MCP tool request/response schemas
- Edge case tests: Network timeouts, DB errors, concurrent updates
- Phase-II regression tests: Verify all Phase-II tests pass

---

### Phase 3: Frontend Chat Widget Integration

**Objective**: Embed OpenAI ChatKit as non-intrusive UI layer in Phase-II frontend

**Implementation Strategy** (No Code, Only Plan):

3.1 **ChatKit Component Setup**
- Import OpenAI ChatKit React component
- Configure ChatKit with custom styling (Phase-II brand)
- Implement ChatWidget wrapper component (FAB + modal)
- Implement conversation state management (React Context)

3.2 **Chat Widget Component**
- Build floating action button (FAB, bottom-right, non-intrusive)
- Build modal/slide-over panel (conversation display area)
- Build message list component (render user + assistant messages)
- Build input field component (text input + send button)
- Build response rendering (text + tool call indicators)
- **Constraint**: Must NOT modify Phase-II task pages
- **Constraint**: Must be fully removable from app
- **Accessibility**: Keyboard navigation, screen reader support

3.3 **Chat Service & API Integration**
- Implement chatService.ts (API client for /api/{user_id}/chat)
- Implement conversationService.ts (local conversation state)
- Implement authentication context integration (use Phase-II auth)
- Implement conversation persistence (use conversation_id from response)
- Implement error handling (API errors, retry, fallback messages)

3.4 **Phase-II Integration** (Additive Only)
- Add ChatWidget to task pages (Pages that display tasks)
- Mount ChatWidget in layout/root component (appears on all authenticated pages)
- Pass user_id from Phase-II auth context to ChatWidget
- Share Phase-II task context with chat (optional enhancement for multi-turn)
- **Verify**: Phase-II page functionality unaffected

3.5 **Responsive Design** (Mobile/Tablet/Desktop)
- Design FAB positioning for mobile (not blocking input)
- Design modal sizing for mobile (full width, scrollable)
- Design message text wrapping (readable on small screens)
- Design input field sizing (touch-friendly)
- Test: Device emulation (mobile, tablet, desktop viewports)

3.6 **Testing Strategy** (Phase 3)
- Unit tests: ChatWidget component rendering
- Unit tests: Message display and formatting
- Unit tests: Input handling and message sending
- Integration tests: Chat widget + Phase-II task pages (no regressions)
- Integration tests: Chat widget + Phase-II auth (user isolation)
- E2E tests: Full chat flow (create task via chat, see in Phase-II list)
- Accessibility tests: Keyboard navigation, screen readers

---

### Phase 4: Security & User Isolation Validation

**Objective**: Verify strict user isolation and security boundaries

**Validation Tasks**:

4.1 **Authentication & Authorization**
- Verify Better Auth token validation (valid tokens only)
- Verify user_id extraction from token (correct user context)
- Verify all database queries user-scoped (WHERE user_id = :user_id)
- Verify users cannot access other users' tasks (test with multiple users)
- Verify users cannot access other users' conversations (test isolation)
- Verify 401 Unauthorized returned for missing/invalid tokens

4.2 **Data Isolation**
- Test: User A creates task, verify User B cannot see it
- Test: User A creates conversation, verify User B cannot access history
- Test: User A deletes task, verify User B task unaffected
- Test: Concurrent user operations (no race conditions, no data leaks)

4.3 **Input Validation & Sanitization**
- Verify user message input sanitized (no injection attacks)
- Verify title/description sanitized (no XSS if displayed)
- Verify no sensitive data in error messages
- Verify tool inputs validated (e.g., title not empty)

4.4 **API Security**
- Verify CORS configuration (Phase-II boundary respected)
- Verify rate limiting (prevent abuse)
- Verify no credentials leaked in logs
- Verify error responses don't expose system details

4.5 **Testing Strategy** (Phase 4)
- Security unit tests: Input validation, sanitization
- Security integration tests: Multi-user isolation
- Security contract tests: Token validation, authorization
- Penetration testing: Attempt unauthorized access

---

### Phase 5: Testing & Phase-II Regression Verification

**Objective**: Comprehensive testing ensuring zero Phase-II regressions

**Test Categories**:

5.1 **Phase-II Regression Tests** (CRITICAL)
- Run Phase-II test suite: Verify all existing tests pass
- Test Phase-II task CRUD: Create, read, update, delete via Phase-II UI
- Test Phase-II authentication: Login, logout, session persistence
- Test Phase-II database queries: Verify no schema changes affect Phase-II
- Test Phase-II API endpoints: Verify all endpoints return identical results
- Test Phase-II UI routes: Verify no route conflicts with chat widget

5.2 **Phase-III Functional Tests**
- User Story 1: Create task via chat (P1)
- User Story 2: List tasks via chat (P1)
- User Story 3: Complete task via chat (P1)
- User Story 4: Update task via chat (P2)
- User Story 5: Delete task via chat (P2)
- User Story 6: Conversation persistence (P2)
- User Story 7: Multi-turn context (P3)

5.3 **Stateless Behavior Tests**
- Test: Server restart does not affect conversation
- Test: Concurrent requests processed independently
- Test: No in-memory state leaked between requests
- Test: Database is single source of truth

5.4 **MCP Tool Tests**
- Test: Each tool validates inputs correctly
- Test: Each tool returns correct schema
- Test: Tools handle errors gracefully
- Test: Tools are idempotent where required
- Test: No direct database access from agent

5.5 **Chat Widget Tests**
- Test: FAB appears on authenticated pages
- Test: Modal opens/closes without navigation
- Test: Conversation history persists
- Test: User isolation enforced (can't see other conversations)
- Test: Responsive on mobile/tablet/desktop
- Test: Accessible (keyboard, screen readers)

5.6 **Integration Tests**
- Test: Chat widget + Phase-II task page (create task in chat, see in Phase-II)
- Test: Chat widget + Phase-II auth (login/logout works)
- Test: Chat widget + Phase-II database (data consistency)
- Test: Chat API + MCP tools + database (full chain)

5.7 **Performance Tests**
- Measure: Chat response latency (p95 ≤ 3 seconds)
- Measure: MCP tool execution time (≤ 500ms)
- Measure: Database query time (≤ 100ms)
- Load test: 100 concurrent chat users
- Measure: Conversation history retrieval (scalable)

5.8 **Edge Case Tests**
- Test: Gibberish user input (ask for clarification)
- Test: Network timeout during tool execution (idempotent retry)
- Test: Concurrent task updates (database lock, retry message)
- Test: Rate limiting (graceful "service busy" message)
- Test: Empty database (helpful "no tasks" message)

**Validation Gate**:
- ✅ 100% Phase-II regression tests pass
- ✅ All P1 user stories pass acceptance tests
- ✅ All P2 user stories pass acceptance tests
- ✅ Stateless behavior verified
- ✅ MCP tool contracts validated
- ✅ User isolation verified
- ✅ Performance targets met (SC-002, SC-004)
- ✅ Chat widget fully isolated, removable

---

### Phase 6: Deployment Readiness

**Objective**: Production-safe deployment preparation

**Tasks**:

6.1 **Environment Configuration**
- Document required environment variables (.env template)
- Separate development, staging, production configs
- Configure OpenAI API key (secure, no hardcoding)
- Configure database connection (Phase-II Neon)
- Configure Better Auth token validation
- Configure CORS allowed domains

6.2 **Domain & Security Setup**
- Configure ChatKit domain allowlist
- Verify CORS headers (Phase-II boundary respected)
- Verify no secrets in git history
- Verify no secrets in logs
- Verify error messages safe for production

6.3 **Database Migrations**
- Prepare Alembic migrations (Conversation, Message tables)
- Verify migrations are backward-compatible
- Plan migration rollback procedure
- Test migrations on production schema

6.4 **Deployment Procedure**
- Document Phase-III deployment steps
- Document rollback procedure
- Verify monitoring/alerting configured
- Verify logging captures chat interactions (audit trail)

6.5 **Documentation**
- README: Phase-III setup, architecture, API documentation
- Architecture docs: Design decisions, rationale
- API docs: Chat endpoint contract, MCP tool schemas
- Operational docs: Deployment, monitoring, troubleshooting
- User docs: Chat widget usage, capabilities

---

## RAG & MCP Tool Priority Order

**Tool Execution Priority**:
```
MCP Tools (highest priority) > Database Queries > RAG Skills (lowest priority)
```

**MCP Tool Usage** (Mandatory):
- All task mutations (create, update, delete, complete) MUST use MCP tools
- Agent MUST never write to database directly
- Tools serve as single source of truth for task operations

**Database Query Usage** (When MCP Insufficient):
- Loading conversation history (read-only, no tool exists)
- Loading user context (read-only)
- Persisting assistant responses (read-only for chat, write via Message table)
- User isolation verification (read-only)

**RAG Skill Usage** (Strictly Limited):
- **Allowed**:
  - rag-indexer: Index chatbot specification, MCP tool documentation, API contracts
  - rag-retriever: Retrieve explanatory context (e.g., "what is add_task tool?")
  - rag-answerer: Answer user questions about chatbot capabilities (e.g., "Can I delete tasks?")
- **Prohibited**:
  - rag-answerer performing task operations (use MCP tools instead)
  - rag-retriever accessing live task data (use database queries instead)
  - RAG making decisions that bypass agent logic (agent decides intent)
  - RAG manipulating conversation history (database persists, not RAG)

**Decision Logic**:
- User asks "Create a task" → Agent selects add_task tool → Tool executes → Success
- User asks "What tools do you have?" → RAG retrieves tool docs → Answer user
- User asks "Show my tasks" → Agent selects list_tasks tool → Tool queries database → Success
- User asks "How does the chatbot work?" → RAG retrieves spec → Explain to user

---

## Safety & Regression Protection

### Phase-II Integrity Checkpoints

Every implementation phase must verify:

✅ **No schema breaking changes**: Conversation/Message tables are additive; Task table unchanged
✅ **No API contract changes**: Phase-II endpoints unchanged; chat endpoint is new
✅ **No auth system changes**: Better Auth unchanged; chat uses existing token validation
✅ **No frontend route changes**: Phase-II routes unchanged; chat widget is additive component
✅ **Test suite passes**: All Phase-II tests pass before Phase-III tests run
✅ **User data integrity**: No task/user data modified; no data loss

### Required Constitutional Approvals

Before implementation, confirm:
- ✅ All 7 principles pass Constitution Check (above)
- ✅ No deviations from locked technology stack
- ✅ All MCP tools stateless and database-backed
- ✅ Stateless chat request lifecycle enforced
- ✅ User isolation guaranteed by design

**Critical Flag**: If any implementation step violates Constitution Check or risked Phase-II breakage, it MUST:
1. Be flagged explicitly
2. Require user (architect) approval
3. Document rationale and tradeoffs
4. Show why simpler alternatives insufficient

---

## Next Steps

1. ✅ Phase 0 (Phase 0 Complete): Research findings in `research.md`
2. ✅ Phase 1 (Phase 1 Complete): Data model, contracts, quickstart in `data-model.md`, `contracts/`, `quickstart.md`
3. → **Proceed to `/sp.tasks`**: Task breakdown for implementation
4. → Execute `/sp.implement`: Implementation by Claude Code
5. → Deployment: Production rollout with Phase-II regression verification

---

**Artifacts Created**:
- `plan.md` (this file)
- `research.md` (Phase 0 findings)
- `data-model.md` (Phase 1 entities)
- `contracts/chat-api.openapi.yml` (Phase 1 API schema)
- `contracts/mcp-tools.schema.json` (Phase 1 MCP schemas)
- `quickstart.md` (Phase 1 setup guide)

**Validation Status**: ✅ Ready for task breakdown (`/sp.tasks`)

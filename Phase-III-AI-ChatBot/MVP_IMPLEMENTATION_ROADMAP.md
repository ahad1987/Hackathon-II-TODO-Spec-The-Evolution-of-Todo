# Phase-III MVP Implementation Roadmap

**Status**: 🚀 In Progress | **Date**: 2026-01-15
**Scope**: 104 Core Tasks (Phase 1 + Phase 2 + US1-3)
**Target**: Functional AI Chatbot with Natural Language CRUD

---

## MVP Scope Summary

### What's Included (MVP)
- ✅ Phase 1: Setup & Safety Foundation (6 tasks)
- ✅ Phase 2: Foundational Prerequisites (56 tasks)
- ✅ Phase 3-5: User Stories 1-3 (29 tasks)
  - US1: Natural Language Task Creation (P1)
  - US2: Natural Language Task Listing (P1)
  - US3: Natural Language Task Completion (P1)

### What's NOT Included (Phase II, beyond MVP)
- ❌ Phase 6: US4-5 (Update/Delete tasks via chat)
- ❌ Phase 7: US6-7 (Persistence, multi-turn context)
- ❌ Phase 8-10: Advanced features (error handling beyond basics, accessibility, responsive design beyond baseline)
- ❌ Phase 11-15: Full testing suite, performance optimization, advanced deployment

### MVP Deliverable
**A fully functional AI chatbot that allows users to**:
1. Create tasks via natural language (e.g., "Add a task to buy groceries")
2. View their tasks via natural language (e.g., "Show my tasks")
3. Mark tasks complete via natural language (e.g., "Complete buying groceries")

All with proper:
- Natural language intent detection
- User authentication & isolation
- Database persistence
- Phase-II integration (tasks appear in Phase-II TODO list)

---

## Implementation Phases

### Phase 1: Setup & Safety Foundation (6 Tasks)
**Estimated**: 2-3 hours

**Deliverables**:
- Backend namespace structure: `backend/src/chatbot/`
- Frontend namespace structure: `frontend/src/chatbot/`
- Safety documentation (Phase-II protection)
- Architecture documentation
- Environment configuration example
- Updated dependencies (requirements.txt, package.json)

**Key Tasks**:
- T001: Phase-II regression baseline verification
- T002: Lock Phase-II schemas (document as read-only)
- T003: Create CHATBOT_SAFETY.md
- T004: Create backend/src/chatbot/ directory
- T005: Create frontend/src/chatbot/ directory
- T006: Create ARCHITECTURE.md

**Success Criteria**:
- ✅ Phase-II test suite runs without errors
- ✅ All namespace directories created
- ✅ Dependencies documented
- ✅ Environment template created (.env.example)

**Status**: ⏳ Starting...

---

### Phase 2: Foundational Prerequisites (56 Tasks)
**Estimated**: 20-24 hours
**CRITICAL**: Must complete before any user story implementation

#### C. Database Extensions (8 Tasks)
- Conversation SQLModel
- Message SQLModel
- Alembic migrations (backward-compatible)
- Database indexes
- Conversation service (create, load, append)
- Transaction support

#### D. MCP Server & Tools (9 Tasks)
- MCP server initialization
- 5 MCP tools (add_task, list_tasks, complete_task, delete_task, update_task)
- Input validation
- Error handling
- Unit tests for tools

#### E. OpenAI Agent Setup (9 Tasks)
- Agent initialization (Agents SDK, GPT-4)
- Tool registration
- Intent detection rules
- Confirmation prompts for destructive ops
- Prevent task ID hallucination
- Multi-tool chaining
- RAG integration (help only)
- System prompt
- Error handling

#### F. Chat Endpoint (11 Tasks)
- POST /api/{user_id}/chat implementation
- Conversation history loading
- Message appending
- Agent execution
- Response persistence
- Response serialization
- Statelessness verification
- Request/response validation
- Integration test

#### G. Authentication & Security (8 Tasks)
- JWT validation
- User_id matching
- 401/403 responses
- Input sanitization
- Error masking
- CORS configuration
- Security unit tests

#### H. Conversation Persistence (5 Tasks)
- Conversation creation
- Conversation retrieval
- Message persistence
- User isolation enforcement
- Persistence layer tests

**Success Criteria**:
- ✅ All models created and tested
- ✅ Migrations run successfully
- ✅ All MCP tools functional
- ✅ Agent responds to chat requests
- ✅ User authentication works
- ✅ Conversation history persists

**Status**: ⏳ Queued

---

### Phase 3-5: User Stories 1-3 (MVP CRUD Operations)
**Estimated**: 16-20 hours

#### US1: Natural Language Task Creation (14 Tasks)
**Goal**: "Add a task to buy groceries" → Task created, shown in chat & Phase-II

Backend:
- T062: Agent add_task intent detection
- T063: add_task tool unit tests
- T064: Chat integration test (full flow)
- T065: Phase-II regression verification

Frontend:
- T066: ChatWidget component (FAB + modal)
- T067: ChatPanel component (message display)
- T068: ChatInput component (user input)
- T069: Chat service client
- T070: ChatContext (state management)
- T071: Integrate ChatWidget into TasksPage
- T072: Integrate ChatWidget into DashboardPage
- T073: Chat widget unit tests
- T074: E2E test (full creation flow)
- T075: Conversation persistence test

#### US2: Natural Language Task Listing (7 Tasks)
**Goal**: "Show my tasks" → Chatbot lists all user tasks

Backend:
- T076: Agent list_tasks intent detection
- T077: list_tasks tool unit tests
- T078: Chat integration test

Frontend:
- T079: ChatMessage component for formatted lists
- T080: List response rendering
- T081: List formatting tests
- T082: E2E test (list tasks flow)
- T083: Tool call verification

#### US3: Natural Language Task Completion (8 Tasks)
**Goal**: "Complete buying groceries" → Task marked done

Backend:
- T084: Agent complete_task intent detection
- T085: complete_task tool unit tests
- T086: Chat integration test
- T087: Phase-II regression verification

Frontend:
- T088: Confirmation display in messages
- T089: Confirmation rendering tests
- T090: E2E test (complete task flow)

**Checkpoint**: ✅ MVP Core CRUD Complete

**Success Criteria**:
- ✅ Create task via chat works
- ✅ List tasks via chat works
- ✅ Complete task via chat works
- ✅ All tasks appear in Phase-II TODO list
- ✅ User can see all CRUD operations in chat
- ✅ Phase-II app still works normally

**Status**: ⏳ Queued

---

## Technical Stack (Locked for MVP)

**Backend**:
- Python 3.11+ (FastAPI) - Phase-II standard
- OpenAI SDK + Agents SDK
- MCP SDK (Model Context Protocol)
- SQLModel ORM
- Alembic for migrations
- Better Auth (Phase-II integration)

**Frontend**:
- React + OpenAI ChatKit
- React Context for state management
- TypeScript

**Database**:
- Neon PostgreSQL (Phase-II shared)
- Conversation & Message tables (new)
- Task table (existing Phase-II, unchanged)

---

## Critical Safety Checkpoints

### Before Phase 2 (After Phase 1)
- [ ] Phase-II test suite runs without errors
- [ ] All namespace directories created
- [ ] Dependencies documented
- [ ] BASELINE.md created with Phase-II test results

### Before US1 (After Phase 2)
- [ ] All migrations run successfully
- [ ] All MCP tools tested individually
- [ ] Chat endpoint responds correctly
- [ ] Authentication works (JWT validation passes)
- [ ] Conversation persistence works
- [ ] **NO Phase-II data modified**

### After MVP (Before deployment)
- [ ] Phase-II regression tests: ALL PASS
- [ ] US1, US2, US3 acceptance criteria met
- [ ] Chat widget doesn't break Phase-II UI
- [ ] All tasks created via chat appear in Phase-II list

---

## Success Criteria (MVP Acceptance)

**Functional**:
- ✅ User can create tasks via natural language chat
- ✅ User can view their tasks via natural language chat
- ✅ User can mark tasks complete via natural language chat
- ✅ All operations work with Phase-II TODO app integration
- ✅ Conversation history persists (server restart test)

**Quality**:
- ✅ No Phase-II regressions
- ✅ User authentication & isolation verified
- ✅ All tasks properly scoped to authenticated user
- ✅ Error handling for edge cases (empty title, non-existent task, etc.)

**Documentation**:
- ✅ Setup guide created (SETUP.md)
- ✅ Architecture documented (ARCHITECTURE.md)
- ✅ API contract documented
- ✅ README updated with chat feature

---

## Task Execution Order

### Week 1: Phases 1-2 Foundation
- Day 1-2: Phase 1 Setup (directory structure, safety docs)
- Day 3-5: Phase 2a Database (models, migrations)
- Day 6-7: Phase 2b MCP (tools, validation)

### Week 2: Phases 2c-2h Infrastructure
- Day 1-2: Phase 2c Agent (Agents SDK setup, intent detection)
- Day 3-4: Phase 2d Chat Endpoint (stateless handler)
- Day 5-6: Phase 2e-f Auth & Persistence
- Day 7: Phase 2 Checkpoint Testing

### Week 3: User Stories (Parallel Frontend/Backend)
- Backend: US1, US2, US3 (tools, tests, integration)
- Frontend: ChatWidget, ChatPanel, ChatInput, ChatContext
- Testing: E2E tests, Phase-II regression verification

### Week 4: MVP Testing & Documentation
- Full regression testing
- MVP acceptance testing
- Documentation completion
- Deployment readiness

---

## Progress Tracking

Use this checklist to track MVP completion:

**Phase 1: Setup** (6/6)
- [ ] T001 ✓ Phase-II regression baseline
- [ ] T002 ✓ Phase-II schema lockdown
- [ ] T003 ✓ CHATBOT_SAFETY.md
- [ ] T004 ✓ backend/src/chatbot/ created
- [ ] T005 ✓ frontend/src/chatbot/ created
- [ ] T006 ✓ ARCHITECTURE.md

**Phase 2: Foundational** (0/56)
- Database (0/8)
- MCP Tools (0/9)
- Agent (0/9)
- Chat Endpoint (0/11)
- Auth & Security (0/8)
- Persistence (0/5)

**Phase 3-5: User Stories** (0/29)
- US1 (0/14)
- US2 (0/7)
- US3 (0/8)

**Total MVP Progress: 0/104 (0%)**

---

## Known Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Phase-II regression | HIGH | Regression testing at every checkpoint, additive-only changes |
| Stateless guarantee | HIGH | Code review + explicit verification in T045, server restart test |
| User data leakage | HIGH | User isolation tests, authorization checks in every endpoint |
| OpenAI API limits | MEDIUM | Error handling, rate limit graceful degradation |
| Database schema conflicts | MEDIUM | Alembic migrations with rollback, schema tests |
| Chat widget breaking Phase-II | MEDIUM | Component isolation, E2E tests, design as fully removable |

---

## Quick Reference: Task File Locations

**Backend**:
- Models: `backend/src/chatbot/models/{conversation,message}.py`
- Services: `backend/src/chatbot/services/{conversation_service,agent_service}.py`
- MCP: `backend/src/chatbot/mcp/{server.py, tools/*.py, validators.py, error_handler.py}`
- API: `backend/src/chatbot/api/{routes/chat.py, dependencies.py}`
- Config: `backend/src/chatbot/config/cors.py`
- Migrations: `backend/alembic/versions/{001,002}_*.py`

**Frontend**:
- Components: `frontend/src/chatbot/components/ChatWidget/{ChatWidget,ChatPanel,ChatInput,ChatMessage}.tsx`
- Services: `frontend/src/chatbot/services/{chatService,conversationService}.ts`
- Context: `frontend/src/chatbot/contexts/ChatContext.tsx`
- Pages: `frontend/src/pages/{TasksPage,DashboardPage}.tsx` (modified to include ChatWidget)

**Tests**:
- Unit: `backend/tests/unit/{test_mcp_tools,test_auth_validation,test_conversation_service}.py`
- Integration: `backend/tests/integration/{test_chat_endpoint,test_chat_create_task,test_phase2_regression}.py`
- E2E: `frontend/tests/e2e/{test_create_task_flow,test_list_tasks_flow,test_complete_task_flow}.ts`

**Documentation**:
- Setup: `SETUP.md`
- Architecture: `ARCHITECTURE.md`
- Safety: `CHATBOT_SAFETY.md`
- Baseline: `specs/1-ai-chatbot-integration/BASELINE.md`

---

**Next**: Start Phase 1 Implementation

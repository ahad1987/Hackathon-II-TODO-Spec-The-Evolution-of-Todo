# Tasks: Phase-III AI-Powered Todo Chatbot

**Input**: Design documents from `/specs/1-ai-chatbot-integration/`
**Prerequisites**: plan.md (complete), spec.md (7 user stories, P1-P3), research.md, data-model.md
**Status**: Ready for implementation
**Scope**: Full Phase-III AI Chatbot with natural language CRUD, MCP tools, stateless backend, chat widget UI
**Architecture**: Stateless + MCP + OpenAI Agents SDK + SQLModel + FastAPI
**Risk**: Medium (isolated from Phase-II, fully backward-compatible)
**Backward Compatibility**: Mandatory - zero Phase-II regressions

---

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no block dependencies)
- **[Story]**: User story label (US1, US2, etc.) - ONLY for user story phase tasks
- **File paths**: Absolute and specific (e.g., `backend/src/models/conversation.py`)

---

## Phase 1: Setup (Shared Infrastructure & Safety Foundation)

**Purpose**: Initialize project structure, verify Phase-II baseline, establish safety boundaries

**Critical**: Phase-II integrity verification must pass before proceeding

### A. Architecture & Safety Foundation

- [ ] T001 Verify Phase-II regression baseline: run Phase-II test suite and document results in `specs/1-ai-chatbot-integration/BASELINE.md`
- [ ] T002 Lock Phase-II schemas, routes, API contracts as read-only in `backend/src/models/task.py` (document preserved fields)
- [ ] T003 Define Phase-III additive-only contract in `CHATBOT_SAFETY.md` (no destructive changes to Phase-II)
- [ ] T004 Create chatbot namespace structure: `backend/src/chatbot/` (models, services, mcp, api)
- [ ] T005 Create frontend chatbot namespace: `frontend/src/chatbot/` (components, services, contexts)
- [ ] T006 Document module isolation boundaries in `ARCHITECTURE.md` (what touches Phase-II, what doesn't)

### B. Environment & Dependencies

- [ ] T007 [P] Add OpenAI SDK to backend dependencies: `backend/requirements.txt` (openai, openai-agents, mcp-sdk)
- [ ] T008 [P] Add OpenAI ChatKit to frontend dependencies: `frontend/package.json` (chatkit, react-openai)
- [ ] T009 Add SQLModel Conversation/Message models support: `backend/requirements.txt` (sqlmodel, alembic)
- [ ] T010 [P] Create `.env.example` with Phase-III variables: `OPENAI_API_KEY`, `CHATKIT_DOMAIN_KEY`, `DB_URL`
- [ ] T011 Document environment setup in `SETUP.md`: dev, staging, production config examples

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work begins until this entire phase completes

### C. Database Extensions (Stateless Support)

- [ ] T012 Create Conversation SQLModel in `backend/src/chatbot/models/conversation.py` (id, user_id, created_at, updated_at)
- [ ] T013 Create Message SQLModel in `backend/src/chatbot/models/message.py` (id, user_id, conversation_id, role, content, created_at, tool_calls)
- [ ] T014 [P] Create Alembic migration for Conversation table: `backend/alembic/versions/001_create_conversation.py` (backward-compatible)
- [ ] T015 [P] Create Alembic migration for Message table: `backend/alembic/versions/002_create_message.py` (backward-compatible, FK to Conversation)
- [ ] T016 Add database indexes: `conversation(user_id, created_at)`, `message(conversation_id, created_at, user_id)` in migrations
- [ ] T017 Verify Phase-II Task table untouched: run migration test in `tests/integration/test_phase2_regression.py` (zero changes to Task schema)
- [ ] T018 Create conversation service: `backend/src/chatbot/services/conversation_service.py` (create, load, append_message)
- [ ] T019 Add database transaction support for stateless operations in `backend/src/chatbot/services/conversation_service.py`

### D. MCP Server & Tool Foundation

- [ ] T020 Initialize MCP server in `backend/src/chatbot/mcp/server.py` (Official MCP SDK, tool registry)
- [ ] T021 [P] Create add_task MCP tool in `backend/src/chatbot/mcp/tools/add_task.py` (input validation, DB persistence, user-scoped)
- [ ] T022 [P] Create list_tasks MCP tool in `backend/src/chatbot/mcp/tools/list_tasks.py` (filter support, ordering, user-scoped)
- [ ] T023 [P] Create complete_task MCP tool in `backend/src/chatbot/mcp/tools/complete_task.py` (idempotent, user-scoped)
- [ ] T024 [P] Create delete_task MCP tool in `backend/src/chatbot/mcp/tools/delete_task.py` (permanent delete, user-scoped)
- [ ] T025 [P] Create update_task MCP tool in `backend/src/chatbot/mcp/tools/update_task.py` (validation, user-scoped)
- [ ] T026 Add tool input validation in `backend/src/chatbot/mcp/validators.py` (title not empty, user_id match, task ID validation)
- [ ] T027 Add tool error handling in `backend/src/chatbot/mcp/error_handler.py` (structured responses, never crashes agent)
- [ ] T028 Create unit tests for MCP tools in `backend/tests/unit/test_mcp_tools.py` (each tool contract verified)

### E. OpenAI Agent Setup

- [ ] T029 Create OpenAI Agent in `backend/src/chatbot/services/agent_service.py` (Agents SDK, GPT-4)
- [ ] T030 Register all 5 MCP tools with agent in `backend/src/chatbot/services/agent_service.py`
- [ ] T031 Define tool-selection rules (intent → tool mapping) in `backend/src/chatbot/services/agent_service.py` (create/add, read/list, update, complete, delete)
- [ ] T032 Add confirmation prompts for destructive operations in `backend/src/chatbot/services/agent_service.py` (templates for delete/complete)
- [ ] T033 Prevent task ID hallucination: agent uses only tool-returned IDs in `backend/src/chatbot/services/agent_service.py`
- [ ] T034 Enable multi-tool chaining in `backend/src/chatbot/services/agent_service.py` (list tasks → identify → execute)
- [ ] T035 Integrate RAG retriever for help/explanations ONLY in `backend/src/chatbot/services/agent_service.py` (block RAG from CRUD)
- [ ] T036 Create agent system prompt in `backend/src/chatbot/prompts/system.md` (task-focused, confirmation-based, user-scoped)
- [ ] T037 Add error handling for agent failures in `backend/src/chatbot/services/agent_service.py` (graceful degradation, user-friendly messages)

### F. Chat Endpoint (Stateless Lifecycle)

- [ ] T038 Implement stateless chat request handler in `backend/src/chatbot/api/routes/chat.py` (POST /api/{user_id}/chat)
- [ ] T039 Add authentication middleware: extract user_id from Better Auth token in `backend/src/chatbot/api/dependencies.py`
- [ ] T040 Implement conversation history loading in `backend/src/chatbot/api/routes/chat.py` (load by conversation_id or create new)
- [ ] T041 Implement message appending in `backend/src/chatbot/api/routes/chat.py` (user message → history)
- [ ] T042 Implement agent execution with context in `backend/src/chatbot/api/routes/chat.py` (pass full history + current message)
- [ ] T043 Implement response persistence in `backend/src/chatbot/api/routes/chat.py` (save assistant message + tool calls to DB)
- [ ] T044 Implement response serialization in `backend/src/chatbot/api/routes/chat.py` (conversation_id, response, tool_calls, status)
- [ ] T045 **CRITICAL**: Verify statelessness: NO in-memory state retained after response in `backend/src/chatbot/api/routes/chat.py`
- [ ] T046 Add request validation in `backend/src/chatbot/api/routes/chat.py` (conversation_id optional, message required)
- [ ] T047 Add response validation: all responses contain required fields in `backend/src/chatbot/api/routes/chat.py`
- [ ] T048 Create integration test for chat endpoint in `backend/tests/integration/test_chat_endpoint.py`

### G. Authentication & Security Validation

- [ ] T049 Implement JWT validation in `backend/src/chatbot/api/dependencies.py` (Better Auth token, user_id extraction)
- [ ] T050 Add user_id matching: URL user_id must match token identity in `backend/src/chatbot/api/routes/chat.py`
- [ ] T051 Return 401 Unauthorized for missing/invalid tokens in `backend/src/chatbot/api/routes/chat.py`
- [ ] T052 Return 403 Forbidden for user_id mismatch in `backend/src/chatbot/api/routes/chat.py`
- [ ] T053 Add user input sanitization in `backend/src/chatbot/api/routes/chat.py` (prevent injection attacks)
- [ ] T054 Mask internal errors from users in `backend/src/chatbot/api/routes/chat.py` (never expose stack traces)
- [ ] T055 Add CORS configuration respecting Phase-II auth boundary in `backend/src/chatbot/config/cors.py`
- [ ] T056 Create security unit tests in `backend/tests/unit/test_auth_validation.py` (token validation, user isolation)

### H. Conversation Persistence Service

- [ ] T057 Implement conversation creation in `backend/src/chatbot/services/conversation_service.py` (generate UUID, user_id scoped)
- [ ] T058 Implement conversation retrieval in `backend/src/chatbot/services/conversation_service.py` (load all messages, ordered)
- [ ] T059 Implement message persistence in `backend/src/chatbot/services/conversation_service.py` (insert with transaction)
- [ ] T060 Add user isolation in all queries in `backend/src/chatbot/services/conversation_service.py` (WHERE user_id = :user_id)
- [ ] T061 Create persistence layer unit tests in `backend/tests/unit/test_conversation_service.py`

**Checkpoint**: ✅ All foundational tasks complete - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Natural Language Task Creation (Priority: P1) 🎯 MVP

**Goal**: Users can create tasks via natural language (e.g., "Add a task to buy groceries") with AI confirmation before execution

**Independent Test**: User types "Add task: buy groceries" → AI confirms "Ready?" → User says "Yes" → Task created and appears in Phase-II TODO list

**User Isolation**: All operations scoped to authenticated user only

**Acceptance Criteria**:
- ✅ Agent detects intent: "create task" from user message
- ✅ Agent selects `add_task` tool with parsed title
- ✅ Agent confirms action before execution
- ✅ Task persisted to database with user_id
- ✅ Response includes task ID and title
- ✅ Task appears in Phase-II TODO list
- ✅ Error handling for empty title
- ✅ Conversation history persisted

### Backend Implementation

- [ ] T062 [US1] Verify add_task tool integration with agent in `backend/src/chatbot/services/agent_service.py` (intent detection: "add", "create", "new task")
- [ ] T063 [US1] Test add_task tool directly in `backend/tests/unit/test_add_task_tool.py` (valid title, empty title, user-scoped)
- [ ] T064 [US1] Create chat integration test for task creation in `backend/tests/integration/test_chat_create_task.py` (full flow)
- [ ] T065 [US1] Verify task appears in Phase-II query in `backend/tests/integration/test_phase2_regression.py` (Phase-II Task table unaffected)

### Frontend Implementation

- [ ] T066 [P] [US1] Create ChatWidget component in `frontend/src/chatbot/components/ChatWidget/ChatWidget.tsx` (FAB + modal)
- [ ] T067 [P] [US1] Create ChatPanel component in `frontend/src/chatbot/components/ChatWidget/ChatPanel.tsx` (message display)
- [ ] T068 [P] [US1] Create ChatInput component in `frontend/src/chatbot/components/ChatWidget/ChatInput.tsx` (user message input)
- [ ] T069 [US1] Implement chat service client in `frontend/src/chatbot/services/chatService.ts` (POST /api/{user_id}/chat)
- [ ] T070 [US1] Create ChatContext in `frontend/src/chatbot/contexts/ChatContext.tsx` (conversation state management)
- [ ] T071 [US1] Integrate ChatWidget into TasksPage in `frontend/src/pages/TasksPage.tsx` (mount ChatWidget, pass user_id)
- [ ] T072 [US1] Add ChatWidget to other authenticated pages in `frontend/src/pages/DashboardPage.tsx`
- [ ] T073 [US1] Create chat widget unit tests in `frontend/tests/unit/components/test_ChatWidget.tsx`

### Integration Testing (US1)

- [ ] T074 [US1] Create E2E test: type "Add task..." → receive confirmation → confirm → see task in Phase-II list in `frontend/tests/e2e/test_create_task_flow.ts`
- [ ] T075 [US1] Verify conversation history saved after US1 in `backend/tests/integration/test_conversation_persistence.py`

---

## Phase 4: User Story 2 - Natural Language Task Listing (Priority: P1)

**Goal**: Users can view tasks via natural language (e.g., "Show my tasks", "What's pending?") with formatted lists

**Independent Test**: User types "Show my tasks" → AI returns formatted list of all tasks

**User Isolation**: Only authenticated user's tasks shown

**Acceptance Criteria**:
- ✅ Agent detects intent: "list", "show", "what" tasks
- ✅ Agent selects `list_tasks` tool with optional filter
- ✅ Tool returns user's tasks (pending/completed/all)
- ✅ Response formatted for readability (numbered list, grouped by status)
- ✅ Empty task list handled gracefully
- ✅ Conversation history persisted

### Backend Implementation

- [ ] T076 [US2] Verify list_tasks tool integration with agent in `backend/src/chatbot/services/agent_service.py` (intent detection: "list", "show", "pending", "completed")
- [ ] T077 [US2] Test list_tasks tool directly in `backend/tests/unit/test_list_tasks_tool.py` (all filter, pending, completed, empty list)
- [ ] T078 [US2] Create chat integration test for task listing in `backend/tests/integration/test_chat_list_tasks.py` (full flow with multiple tasks)

### Frontend Implementation

- [ ] T079 [P] [US2] Create ChatMessage component for formatted lists in `frontend/src/chatbot/components/ChatWidget/ChatMessage.tsx` (render structured responses)
- [ ] T080 [US2] Add message rendering for task lists in `frontend/src/chatbot/components/ChatWidget/ChatPanel.tsx`
- [ ] T081 [US2] Create tests for list response formatting in `frontend/tests/unit/components/test_ChatMessage.tsx`

### Integration Testing (US2)

- [ ] T082 [US2] Create E2E test: type "Show my tasks" → see formatted list in chat in `frontend/tests/e2e/test_list_tasks_flow.ts`
- [ ] T083 [US2] Verify conversation includes list_tasks tool call in `backend/tests/integration/test_conversation_persistence.py`

---

## Phase 5: User Story 3 - Natural Language Task Completion (Priority: P1)

**Goal**: Users can mark tasks complete via natural language (e.g., "Mark task 1 as done") with AI confirmation

**Independent Test**: User types "Complete buying groceries" → AI confirms → Task marked complete in Phase-II

**User Isolation**: Only authenticated user's tasks can be completed

**Acceptance Criteria**:
- ✅ Agent detects intent: "complete", "mark done", "finish" task
- ✅ Agent selects `complete_task` tool with identified task ID
- ✅ If multiple matches, agent asks "Which task?" with list
- ✅ Agent confirms before execution (optional for idempotent operations)
- ✅ Task persisted as completed in database
- ✅ Phase-II TODO UI reflects completion
- ✅ Already-completed task handled gracefully
- ✅ Non-existent task returns helpful error

### Backend Implementation

- [ ] T084 [US3] Verify complete_task tool integration with agent in `backend/src/chatbot/services/agent_service.py` (intent detection, task matching)
- [ ] T085 [US3] Test complete_task tool directly in `backend/tests/unit/test_complete_task_tool.py` (valid ID, non-existent, already completed, idempotency)
- [ ] T086 [US3] Create chat integration test for task completion in `backend/tests/integration/test_chat_complete_task.py` (full flow)
- [ ] T087 [US3] Verify task marked complete in Phase-II query in `backend/tests/integration/test_phase2_regression.py`

### Frontend Implementation

- [ ] T088 [P] [US3] Add tool call indicators in ChatMessage for confirmations in `frontend/src/chatbot/components/ChatWidget/ChatMessage.tsx`
- [ ] T089 [US3] Create tests for confirmation display in `frontend/tests/unit/components/test_ChatMessage.tsx`

### Integration Testing (US3)

- [ ] T090 [US3] Create E2E test: type "Complete groceries" → confirmation → task marked done in Phase-II in `frontend/tests/e2e/test_complete_task_flow.ts`

**✅ Checkpoint: US1, US2, US3 Complete - MVP Functionality Delivered**

---

## Phase 6: User Story 4 - Natural Language Task Updating (Priority: P2)

**Goal**: Users can modify tasks via natural language (e.g., "Change task 1 to 'Buy milk'") with confirmation

**Independent Test**: User types "Change first task to 'Buy milk'" → AI confirms → Task title updated in Phase-II

**User Isolation**: Only authenticated user's tasks can be updated

**Acceptance Criteria**:
- ✅ Agent detects intent: "change", "update", "edit" task
- ✅ Agent selects `update_task` tool with target and changes
- ✅ If multiple matches, agent asks "Which task?" with list
- ✅ Agent confirms changes before execution
- ✅ Task persisted with updated fields
- ✅ Phase-II UI reflects updates immediately
- ✅ Validation: title not empty after update
- ✅ Non-existent task returns helpful error

### Backend Implementation

- [ ] T091 [US4] Verify update_task tool integration with agent in `backend/src/chatbot/services/agent_service.py` (intent detection, task matching, field extraction)
- [ ] T092 [US4] Test update_task tool directly in `backend/tests/unit/test_update_task_tool.py` (valid updates, empty title rejection, user-scoped)
- [ ] T093 [US4] Create chat integration test for task update in `backend/tests/integration/test_chat_update_task.py` (full flow)
- [ ] T094 [US4] Verify task updated in Phase-II query in `backend/tests/integration/test_phase2_regression.py`

### Frontend Implementation

- [ ] T095 [P] [US4] Update ChatMessage component for update confirmations in `frontend/src/chatbot/components/ChatWidget/ChatMessage.tsx`

### Integration Testing (US4)

- [ ] T096 [US4] Create E2E test: type "Change first task to..." → confirm → see update in Phase-II in `frontend/tests/e2e/test_update_task_flow.ts`

---

## Phase 7: User Story 5 - Natural Language Task Deletion (Priority: P2)

**Goal**: Users can delete tasks via natural language (e.g., "Delete the grocery task") with confirmation to prevent accidents

**Independent Test**: User types "Delete groceries task" → AI asks confirmation → User confirms → Task removed from Phase-II

**User Isolation**: Only authenticated user's tasks can be deleted

**Acceptance Criteria**:
- ✅ Agent detects intent: "delete", "remove", "get rid of" task
- ✅ Agent selects `delete_task` tool with identified task ID
- ✅ Agent ALWAYS asks confirmation for delete (destructive operation)
- ✅ If multiple matches, agent lists options before asking
- ✅ Task permanently deleted from database (no soft delete)
- ✅ Phase-II TODO list updated (task removed)
- ✅ Idempotent: second delete on same task returns error gracefully
- ✅ Non-existent task returns helpful error

### Backend Implementation

- [ ] T097 [US5] Verify delete_task tool integration with agent in `backend/src/chatbot/services/agent_service.py` (intent detection, mandatory confirmation)
- [ ] T098 [US5] Test delete_task tool directly in `backend/tests/unit/test_delete_task_tool.py` (valid delete, non-existent, user-scoped, idempotency)
- [ ] T099 [US5] Create chat integration test for task deletion in `backend/tests/integration/test_chat_delete_task.py` (full flow)
- [ ] T100 [US5] Verify task removed from Phase-II query in `backend/tests/integration/test_phase2_regression.py`

### Integration Testing (US5)

- [ ] T101 [US5] Create E2E test: type "Delete task" → confirmation → confirm → task gone from Phase-II in `frontend/tests/e2e/test_delete_task_flow.ts`

---

## Phase 8: User Story 6 - Persistent Conversation History (Priority: P2)

**Goal**: Users can close and reopen chat widget and see full conversation history with context continuity

**Independent Test**: User creates task → closes chat → reopens → sees full history and can continue conversation

**User Isolation**: Each user sees only their own conversation history

**Acceptance Criteria**:
- ✅ All messages persisted to database
- ✅ Conversation history loaded on widget reopen
- ✅ conversation_id persisted client-side
- ✅ History ordered chronologically (created_at ascending)
- ✅ Includes both user and assistant messages
- ✅ Tool calls and results visible in history
- ✅ Server restart does NOT lose history
- ✅ User isolation: can't access other users' histories

### Backend Implementation

- [ ] T102 [US6] Verify conversation persistence in `backend/src/chatbot/services/conversation_service.py` (load, append, persist)
- [ ] T103 [US6] Create persistence unit tests in `backend/tests/unit/test_conversation_persistence.py` (save, load, multi-message, transaction safety)
- [ ] T104 [US6] Create server restart test in `backend/tests/integration/test_stateless_behavior.py` (close request, restart app, fetch conversation - verify intact)

### Frontend Implementation

- [ ] T105 [P] [US6] Persist conversation_id to local storage in `frontend/src/chatbot/services/conversationService.ts`
- [ ] T106 [P] [US6] Load conversation history on widget mount in `frontend/src/chatbot/contexts/ChatContext.tsx`
- [ ] T107 [US6] Display loaded history in ChatPanel in `frontend/src/chatbot/components/ChatWidget/ChatPanel.tsx` (preserve scroll)
- [ ] T108 [US6] Create conversation context unit tests in `frontend/tests/unit/contexts/test_ChatContext.tsx`

### Integration Testing (US6)

- [ ] T109 [US6] Create E2E test: create task → close widget → reopen → verify history in `frontend/tests/e2e/test_conversation_persistence.ts`
- [ ] T110 [US6] Create multi-user isolation test in `backend/tests/integration/test_user_isolation.py` (User A and User B in chat, verify data boundaries)

---

## Phase 9: User Story 7 - Multi-Turn Conversation Context (Priority: P3)

**Goal**: AI understands context across multiple messages (e.g., "Delete the task I just created")

**Independent Test**: Create task → reference "the task I just created" → agent applies action to correct task

**User Isolation**: Only authenticated user's context used

**Acceptance Criteria**:
- ✅ Agent maintains context from conversation history
- ✅ Agent can reference "the task I created", "first task", etc.
- ✅ Ambiguous references resolved with helpful questions
- ✅ Context scoped to current conversation only
- ✅ Works with multi-turn interactions (3+ exchanges)

### Backend Implementation

- [ ] T111 [P] [US7] Verify agent uses full history in context in `backend/src/chatbot/services/agent_service.py`
- [ ] T112 [P] [US7] Create multi-turn context test in `backend/tests/integration/test_multi_turn_context.py` (create, reference, action)
- [ ] T113 [US7] Add context-aware test cases for ambiguous references in `backend/tests/integration/test_context_resolution.py`

### Frontend Implementation

- [ ] T114 [US7] Ensure conversation history passed to every agent execution in `frontend/src/chatbot/services/chatService.ts`
- [ ] T115 [US7] Create multi-turn UI test in `frontend/tests/e2e/test_multi_turn_flow.ts` (verify context display)

---

## Phase 10: Error Handling, UX & Edge Cases

**Goal**: System gracefully handles all error scenarios and edge cases without breaking Phase-II

**Acceptance Criteria**:
- ✅ Tool errors don't crash agent
- ✅ Missing tasks handled gracefully
- ✅ API downtime shows user-friendly message
- ✅ Confirmations clear and unambiguous
- ✅ Phase-II TODO CRUD always works (chat never blocks it)

### Backend Implementation

- [ ] T116 [P] Create tool error handler in `backend/src/chatbot/mcp/error_handler.py` (graceful fallback, user messages)
- [ ] T117 [P] Create API error responses in `backend/src/chatbot/api/error_responses.py` (4xx, 5xx with helpful text)
- [ ] T118 Test agent error handling in `backend/tests/integration/test_error_handling.py` (tool timeout, DB error, invalid input)
- [ ] T119 Test gibberish input handling in `backend/tests/integration/test_edge_cases.py` (unclear intent → clarification request)
- [ ] T120 Test concurrent update handling in `backend/tests/integration/test_concurrent_updates.py` (DB lock behavior, retry messages)
- [ ] T121 Test rate limiting in `backend/tests/integration/test_rate_limiting.py` (graceful degradation)
- [ ] T122 Test empty database scenario in `backend/tests/integration/test_empty_database.py` (helpful "no tasks" message)

### Frontend Implementation

- [ ] T123 [P] Add API error display in ChatPanel in `frontend/src/chatbot/components/ChatWidget/ChatPanel.tsx` (friendly message)
- [ ] T124 [P] Add loading state in ChatInput in `frontend/src/chatbot/components/ChatWidget/ChatInput.tsx` (prevent double-send)
- [ ] T125 Add network error recovery in ChatContext in `frontend/src/chatbot/contexts/ChatContext.tsx` (retry logic)
- [ ] T126 Create error scenario tests in `frontend/tests/integration/test_error_scenarios.ts` (API down, network timeout, invalid response)

---

## Phase 11: Chat Widget Responsive Design & Accessibility

**Goal**: Chat widget works smoothly on mobile/tablet/desktop with full accessibility

**Acceptance Criteria**:
- ✅ FAB doesn't block content on mobile
- ✅ Modal responsive on small screens
- ✅ Text wrapping works on all viewports
- ✅ Keyboard navigation: Tab, Enter, Escape
- ✅ Screen reader friendly (ARIA labels)
- ✅ Touch-friendly input (large targets)

### Frontend Implementation

- [ ] T127 [P] Create responsive FAB component in `frontend/src/chatbot/components/ChatWidget/ChatWidget.tsx` (mobile-optimized positioning)
- [ ] T128 [P] Create responsive modal in `frontend/src/chatbot/components/ChatWidget/ChatPanel.tsx` (full-width mobile, centered desktop)
- [ ] T129 Add keyboard navigation in ChatWidget in `frontend/src/chatbot/components/ChatWidget/ChatWidget.tsx` (Escape closes, Tab cycles, Enter sends)
- [ ] T130 Add ARIA labels and semantic HTML in ChatPanel in `frontend/src/chatbot/components/ChatWidget/ChatPanel.tsx` (role, aria-label, aria-live)
- [ ] T131 Create responsive design tests in `frontend/tests/e2e/test_responsive_design.ts` (mobile/tablet/desktop viewport tests)
- [ ] T132 Create accessibility audit in `frontend/tests/a11y/test_accessibility.ts` (WCAG 2.1 AA compliance)

---

## Phase 12: Phase-II Regression Testing (MANDATORY)

**Goal**: Verify zero regressions to Phase-II functionality

**Critical Gate**: ALL tests MUST PASS before Phase-III deployment

### Phase-II Verification Tests

- [ ] T133 Run Phase-II regression baseline in `backend/tests/integration/test_phase2_regression.py`
  - [ ] T133a: Phase-II auth flows (login, logout, session)
  - [ ] T133b: Phase-II Task CRUD endpoints (create, read, update, delete)
  - [ ] T133c: Phase-II database queries (verify no schema changes)
  - [ ] T133d: Phase-II UI routes (no new route conflicts)
  - [ ] T133e: Phase-II error handling (unchanged)
- [ ] T134 Verify task data integrity in `backend/tests/integration/test_data_integrity.py` (no task data loss or corruption)
- [ ] T135 Verify Phase-II tests pass in `backend/tests/integration/test_phase2_full_suite.py` (full Phase-II test suite execution)

### Phase-III + Phase-II Integration Tests

- [ ] T136 [P] Test task created via chat appears in Phase-II list in `backend/tests/integration/test_chat_phase2_integration.py`
- [ ] T137 [P] Test task updated via chat reflects in Phase-II in `backend/tests/integration/test_update_sync.py`
- [ ] T138 [P] Test task deleted via chat removed from Phase-II in `backend/tests/integration/test_delete_sync.py`
- [ ] T139 Test Phase-II task edited, then chat operates on updated version in `backend/tests/integration/test_phase2_to_chat_sync.py`
- [ ] T140 Test concurrent Phase-II + chat operations in `backend/tests/integration/test_concurrent_operations.py` (no conflicts)

---

## Phase 13: Performance Testing

**Goal**: Meet all performance targets from spec (SC-002, SC-004)

**Success Criteria**:
- ✅ Chat response latency: p95 ≤ 3 seconds
- ✅ MCP tool execution: ≤ 500ms
- ✅ Database query: ≤ 100ms
- ✅ Support 100 concurrent chat users

### Backend Performance Tests

- [ ] T141 Create latency test in `backend/tests/performance/test_chat_latency.py` (measure p95, p99)
- [ ] T142 Create tool execution benchmark in `backend/tests/performance/test_tool_performance.py` (each tool ≤ 500ms)
- [ ] T143 Create database query benchmark in `backend/tests/performance/test_db_queries.py` (conversation load ≤ 100ms)
- [ ] T144 Create load test in `backend/tests/performance/test_load_100_users.py` (100 concurrent users, measure throughput)
- [ ] T145 Document performance results in `PERFORMANCE_REPORT.md`

---

## Phase 14: Documentation & Deliverables

**Goal**: Complete documentation for operators, developers, users

### Backend Documentation

- [ ] T146 [P] Document MCP tools in `docs/MCP_TOOLS.md` (each tool contract, input/output, error cases)
- [ ] T147 [P] Document agent behavior in `docs/AGENT_BEHAVIOR.md` (system prompt, intent detection, tool selection rules)
- [ ] T148 [P] Document authentication in `docs/AUTHENTICATION.md` (Better Auth integration, user isolation)
- [ ] T149 [P] Document statelessness in `docs/STATELESS_DESIGN.md` (request lifecycle, no in-memory state)
- [ ] T150 Create API documentation in `docs/API.md` (POST /api/{user_id}/chat contract)

### Frontend Documentation

- [ ] T151 [P] Document ChatWidget component in `docs/CHATWIDGET.md` (component structure, props, state)
- [ ] T152 [P] Document chat service in `docs/CHAT_SERVICE.md` (API client, error handling)
- [ ] T153 [P] Document ChatContext in `docs/CHAT_CONTEXT.md` (state management, hooks)

### Project Documentation

- [ ] T154 Update main README in `README.md` (Phase-III section, setup, demo, limitations)
- [ ] T155 Create SETUP.md in `docs/SETUP.md` (environment setup, dev, staging, production)
- [ ] T156 Create DEPLOYMENT.md in `docs/DEPLOYMENT.md` (deployment steps, rollback, monitoring)
- [ ] T157 Create TROUBLESHOOTING.md in `docs/TROUBLESHOOTING.md` (common issues, solutions)
- [ ] T158 Create ARCHITECTURE.md in `docs/ARCHITECTURE.md` (system design, component diagram, data flow)

### Prompt History Records

- [ ] T159 [P] Record Phase-III constitution in `history/prompts/constitution/001-*.constitution.prompt.md` ✅ (complete)
- [ ] T160 [P] Record Phase-III specification in `history/prompts/1-ai-chatbot-integration/001-*.spec.prompt.md` ✅ (complete)
- [ ] T161 [P] Record Phase-III plan in `history/prompts/1-ai-chatbot-integration/002-*.plan.prompt.md` ✅ (complete)
- [ ] T162 Record Phase-III tasks in `history/prompts/1-ai-chatbot-integration/003-*.tasks.prompt.md` (to be created after implementation starts)

---

## Phase 15: Final Verification & Deployment Readiness

**Goal**: Prepare for production deployment

### Pre-Deployment Checks

- [ ] T163 Verify all tests pass (Phase-II + Phase-III) in `CI/CD_VERIFICATION.md`
- [ ] T164 Verify no Phase-II breakage in production environment
- [ ] T165 Load test on production database replica
- [ ] T166 Security review: no secrets in code, logs, or git history
- [ ] T167 Verify all environment variables documented and set
- [ ] T168 Create deployment runbook in `docs/DEPLOYMENT_RUNBOOK.md`

### Deployment

- [ ] T169 Deploy migrations to production (Alembic)
- [ ] T170 Deploy backend to production (docker, netlify, railway, etc.)
- [ ] T171 Deploy frontend to production (npm run build, deploy)
- [ ] T172 Smoke test: chat works, Phase-II still works, data integrity verified
- [ ] T173 Monitor logs and metrics for 24 hours
- [ ] T174 Document any issues and post-deployment adjustments

---

## Summary

**Total Tasks**: 174
**Task Count by User Story**:
- Setup & Foundation: 61 tasks (T001-T061)
- US1 (Task Creation): 14 tasks (T062-T075)
- US2 (Task Listing): 7 tasks (T076-T082)
- US3 (Task Completion): 7 tasks (T083-T090)
- US4 (Task Update): 6 tasks (T091-T096)
- US5 (Task Deletion): 5 tasks (T097-T101)
- US6 (Persistence): 9 tasks (T102-T110)
- US7 (Context): 5 tasks (T111-T115)
- Error Handling & UX: 7 tasks (T116-T122)
- Responsive & Accessibility: 6 tasks (T123-T132)
- Phase-II Regression: 8 tasks (T133-T140)
- Performance: 5 tasks (T141-T145)
- Documentation: 14 tasks (T146-T159)
- Final Verification: 12 tasks (T160-T174)

**Parallel Opportunities**: 45 tasks marked [P] can run in parallel once blocking dependencies complete

**MVP Scope** (First Deployable Increment):
- Phase 1: Setup (all tasks)
- Phase 2: Foundational (all tasks)
- Phase 3-5: US1, US2, US3 (Core CRUD)
- Phase 12-13: Phase-II regression + performance verification
**= Minimum 90 tasks to deploy MVP**

**Suggested Execution Order**:
1. Complete Phase 1-2 (Setup + Foundational) - **blocking for all stories**
2. Execute US1-3 in parallel (independent tasks within each story)
3. Execute US4-5 sequentially (build on foundational)
4. Add US6-7 for persistence and context
5. Run full regression tests before MVP deployment
6. Add documentation and final verification

**Ready for Implementation**: `/sp.implement` to execute tasks

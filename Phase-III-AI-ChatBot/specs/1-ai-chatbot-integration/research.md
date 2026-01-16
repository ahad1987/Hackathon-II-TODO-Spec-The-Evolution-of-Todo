# Phase 0 Research Findings: AI-Powered Todo Chatbot

**Date**: 2026-01-15 | **Status**: Complete

---

## 1. OpenAI Agents SDK Integration for Task-Based Agents

**Decision**: Use OpenAI Agents SDK with GPT-4 for intent detection and tool selection

**Rationale**:
- GPT-4 provides strong natural language understanding for task-based intents (create, read, update, delete, complete)
- Native tool integration simplifies MCP tool invocation
- Built-in error handling and retry logic
- Supports multi-turn conversations with context awareness
- Industry standard for AI chatbot applications

**Alternatives Considered**:
1. Fine-tuned smaller models (e.g., GPT-3.5) - rejected: required extensive training data for reliable task intent detection
2. Custom NLP pipeline (spaCy + rules) - rejected: harder to maintain, less flexible for edge cases
3. Anthropic Claude API - rejected: locked to OpenAI stack per constitution

**Implementation Approach**:
- Initialize Agents SDK with system prompt: "You are a helpful todo task assistant. Help users manage their tasks using natural language."
- Configure to use MCP tools exclusively (no direct API calls)
- Set up confirmation prompts for destructive operations (delete, complete)
- Implement retry logic for transient MCP tool failures

---

## 2. MCP SDK Implementation for Stateless Tool Definitions

**Decision**: Use official MCP SDK to define 5 stateless tools (add_task, list_tasks, complete_task, delete_task, update_task)

**Rationale**:
- Official MCP SDK provides standard tool definition format
- Ensures compatibility with OpenAI Agents SDK
- Stateless design (tools query/mutate database only) enables horizontal scaling
- Clear input/output schemas prevent data inconsistencies

**Alternatives Considered**:
1. Custom tool wrapper layer - rejected: reinvents MCP, harder to integrate
2. Direct agent database access - rejected: violates stateless principle, enables agent logic to bypass tools
3. GraphQL for tools - rejected: adds complexity, MCP simpler for discrete operations

**Implementation Approach**:
- Define each tool with JSON Schema input/output
- Implement tool handlers as database functions (SQLModel queries)
- Tools receive `user_id` parameter to enforce user scoping
- No in-memory state in tool handlers
- Idempotent operations where applicable (complete_task, list_tasks)

---

## 3. OpenAI ChatKit React Component Integration

**Decision**: Use official OpenAI ChatKit React component for chat UI, embedded in Phase-II React app

**Rationale**:
- Official library, well-maintained, documented
- Designed for OpenAI API integration (seamless with Agents SDK)
- Accessible (WCAG 2.1 AA compliant)
- Customizable styling (Phase-II branding)
- Responsive on mobile/tablet/desktop

**Alternatives Considered**:
1. Custom chat UI components - rejected: more work, no accessibility guarantees
2. Third-party libraries (React Chat Lib) - rejected: less integrated with OpenAI
3. Headless approach (API only) - rejected: requires more frontend work

**Implementation Approach**:
- Wrap ChatKit in custom ChatWidget component (FAB + modal)
- Use React Context for conversation state management
- Integrate with Phase-II auth context (reuse user_id)
- Keep ChatWidget isolated from Phase-II components (no prop drilling)
- CSS-in-JS for responsive styling

---

## 4. FastAPI Stateless Conversation Handling

**Decision**: Implement stateless request lifecycle: load history → process → persist → return → forget state

**Rationale**:
- Stateless design enables horizontal scaling (any server can process any request)
- Database is single source of truth (conversation recovery on server restart)
- Supports fault tolerance (request failures don't corrupt state)
- Simplifies deployment (no session affinity required)

**Alternatives Considered**:
1. In-memory conversation cache - rejected: violates stateless principle, breaks on server restart
2. Redis session store - rejected: adds external dependency, still not true stateless
3. Websocket persistent connections - rejected: breaks stateless principle, harder to scale

**Implementation Approach**:
- POST /api/{user_id}/chat endpoint (FastAPI async route)
- Load conversation by conversation_id (or create new)
- Append user message to loaded history
- Execute agent (processes history + current message)
- Persist assistant response to Message table
- Return response immediately
- All state persisted to database; none retained in memory

---

## 5. Conversation History in Stateless Systems

**Decision**: Store full conversation history in database (Conversation + Message tables); load per request

**Rationale**:
- Database persistence ensures history survives server restarts
- Loading per-request is simple, reliable (no caching complexity)
- Enables audit trail (all interactions logged)
- Supports multi-device access (fetch history from any device)

**Alternatives Considered**:
1. In-memory conversation buffer + periodic save - rejected: risky (data loss on crash), violates stateless
2. Minimal history (last N messages) + summarization - rejected: complex, loses context
3. Message queue (Kafka/RabbitMQ) for async persistence - rejected: adds infrastructure, introduces timing issues

**Implementation Approach**:
- Conversation table: user_id, id (UUID), created_at, updated_at
- Message table: user_id, id (UUID), conversation_id (FK), role ("user"/"assistant"), content (text), created_at
- Load all messages for conversation_id, ordered by created_at ascending
- Pass as context to agent
- Persist new messages after agent completes
- Use database transactions to ensure consistency

---

## 6. Phase-II Better Auth Token Structure & Scope

**Decision**: Extract user_id from Better Auth JWT token; use for all database queries

**Rationale**:
- Better Auth is already integrated in Phase-II
- JWT tokens contain user_id and can be validated without additional setup
- User scoping via user_id ensures data isolation
- No new authentication system required

**Alternatives Considered**:
1. Create separate Phase-III auth system - rejected: duplicate logic, breaks Phase-II consistency
2. OAuth2 / external auth provider - rejected: unnecessary, Better Auth already integrated
3. Session-based auth - rejected: Phase-II uses Better Auth (JWT-compatible)

**Implementation Approach**:
- Extract JWT token from Authorization header
- Validate token using Better Auth public key
- Extract user_id from token claims
- Pass user_id to all database queries
- Return 401 Unauthorized if token missing/invalid
- Verify user_id matches conversation/task owner

---

## 7. PostgreSQL Schema Extension Compatibility

**Decision**: Use Alembic migrations (Phase-II standard) for schema changes; backward-compatible only

**Rationale**:
- Alembic is Phase-II standard (already in use)
- Backward-compatible migrations prevent downtime
- Easy rollback if issues arise
- Can be applied to production without downtime

**Alternatives Considered**:
1. Direct SQL schema changes - rejected: risky, no version control
2. Liquibase (database-agnostic) - rejected: Phase-II uses Alembic
3. No migrations (hardcoded schema) - rejected: unsustainable, breaks production

**Implementation Approach**:
- Create Alembic migration for Conversation table (add only, no changes)
- Create Alembic migration for Message table (add only, no changes)
- Verify Task table remains untouched (no changes)
- Test migrations on staging copy of Phase-II database
- Plan rollback (down migrations ready)
- All migrations backward-compatible (no column deletions, only additions)

---

## 8. Phase-II API Structure & Integration Points

**Decision**: Identify integration points; create additive /api/{user_id}/chat endpoint; no Phase-II API changes

**Rationale**:
- Phase-II API stable and working; minimal risk by adding endpoints only
- Chat endpoint isolated (no interference with task, auth, user endpoints)
- Better Auth integration point clear (token validation)
- Database integration point clear (user_id scoping)

**Alternatives Considered**:
1. Modify existing Phase-II endpoints to include chat - rejected: too invasive, breaks Phase-II
2. Separate chat API service - rejected: unnecessary complexity, adds deployment burden
3. WebSocket for chat (Phase-II doesn't use) - rejected: adds complexity, breaks stateless

**Implementation Approach**:
- New endpoint: POST /api/{user_id}/chat (FastAPI route)
- Reuse Phase-II auth middleware (extract user_id from token)
- Reuse Phase-II database (SQLModel + Neon)
- Reuse Phase-II error handling (JSON responses, HTTP status codes)
- Test: No Phase-II endpoints modified, all tests pass

---

## 9. OpenAI API Rate Limiting & Cost

**Decision**: OpenAI Agents SDK handles rate limiting; exponential backoff for retries; cost monitoring

**Rationale**:
- OpenAI provides rate limit information in API responses
- SDK handles retries automatically
- Cost depends on GPT-4 token usage (approx $0.03 per 1K input tokens)
- Fair pricing for MVP scale (initial <10K conversations/day)

**Alternatives Considered**:
1. GPT-3.5 (cheaper) - rejected: less accurate for task intent detection
2. Caching agent responses - rejected: complex, may miss intent nuances
3. No rate limiting (accept API errors) - rejected: poor UX, blocking errors

**Implementation Approach**:
- Configure OpenAI client with retry policy (3 attempts, exponential backoff)
- Log API rate limit headers (monitoring)
- Return user-friendly "service busy" if rate limit hit
- Monitor token usage for cost tracking
- Set up alerts if token usage spikes

---

## 10. Frontend State Management for Chat Widget

**Decision**: Use React Context + hooks for chat state (conversation history, current message, loading state)

**Rationale**:
- React Context is Phase-II standard (no additional dependency)
- Simpler than Redux for chat widget scope
- Integrates cleanly with OpenAI ChatKit component
- Supports conversation persistence (load from API on widget mount)

**Alternatives Considered**:
1. Redux (Phase-II may use) - rejected: overkill for widget scope, adds complexity
2. Local storage (browser cache) - rejected: doesn't persist on server, races with API
3. Global state (no context) - rejected: tight coupling, harder to isolate widget

**Implementation Approach**:
- Create ChatContext with state: conversations (by ID), current_conversation_id, loading, error
- ChatWidget loads conversation on mount (or creates new)
- User input updates local state, calls /api/{user_id}/chat
- Response updates state with assistant message
- Context scoped to ChatWidget subtree (fully isolated)

---

## 11. MCP Tool Error Handling & Resilience

**Decision**: MCP tools return structured errors; agent catches and returns user-friendly messages

**Rationale**:
- Stateless agent should never crash on tool errors
- User receives helpful error message (e.g., "Task not found. Your tasks are: ...")
- Enables retry logic (idempotent operations)
- Supports degraded service (API errors gracefully)

**Alternatives Considered**:
1. Tool errors crash agent - rejected: poor UX, blocks chat
2. Agent silently catches all errors - rejected: hides real issues
3. No error handling (assume success) - rejected: data loss risk

**Implementation Approach**:
- Each MCP tool returns: { "status": "success" | "error", "data": {...}, "error_message": "..." }
- Agent parses response, checks status
- If error, agent asks user for clarification or lists available options
- If success, agent continues to next tool or responds to user
- All errors logged for debugging

---

## Summary Table

| Challenge | Decision | Rationale | Risk Mitigation |
|-----------|----------|-----------|-----------------|
| Intent detection | OpenAI Agents SDK + GPT-4 | Strong NLU, native tool integration | Good coverage of task intents; fallback clarification prompts |
| Tool execution | MCP SDK + stateless handlers | Standard protocol, isolation from agent | Unit tests per tool; idempotent operations |
| Chat UI | OpenAI ChatKit + React Context | Official, accessible, responsive | Isolated component, fully removable from Phase-II |
| Stateless backend | Load history → process → persist → forget | Horizontal scaling, fault tolerance | Database regression tests; server restart tests |
| Conversation storage | PostgreSQL (Phase-II shared) + Message table | Single source of truth, audit trail | Alembic migrations; backward-compatible schema |
| Auth & isolation | Better Auth token + user_id scoping | Reuse existing Phase-II system | Multi-user isolation tests; authorization checks |
| API integration | POST /api/{user_id}/chat (additive) | Minimal Phase-II changes, new endpoint | All Phase-II tests pass; no route conflicts |
| Rate limiting | OpenAI retry policy + exponential backoff | SDK handles automatically | Graceful degradation; user-friendly messages |
| Widget integration | React Context + ChatKit component | Phase-II standard, fully isolated | E2E tests; Phase-II regression tests |
| Error handling | Structured tool responses + agent fallback | Prevents agent crashes | Comprehensive error scenarios; user guidance |

---

**All unknowns resolved. Ready for Phase 1 design.**

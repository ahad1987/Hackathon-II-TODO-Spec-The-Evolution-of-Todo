---
id: 002
title: Phase III Technical Plan
stage: plan
date: 2026-01-15
surface: agent
model: claude-haiku-4-5-20251001
feature: ai-chatbot-integration
branch: 1-ai-chatbot-integration
user: Ahad
command: /sp.plan
labels: ["phase-iii", "plan", "technical-architecture", "mcp-design", "stateless-backend"]
links:
  spec: specs/1-ai-chatbot-integration/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/1-ai-chatbot-integration/plan.md
  - specs/1-ai-chatbot-integration/research.md
  - specs/1-ai-chatbot-integration/data-model.md
tests:
  - constitution-check-phase0
  - constitution-check-phase1
  - phase2-regression-scope
---

## Prompt

```text
Using the approved Phase-III Constitution and the completed Phase-III Specification, generate a detailed, implementation-ready Technical Plan for the Todo AI Chatbot.

This plan must enable smooth task decomposition and safe implementation without introducing regressions to the Phase-II Todo Web App.

Planning Objectives:
- Preserve full Phase-II functionality (zero regressions)
- Implement a fully functional AI-powered Todo Chatbot
- Follow Agentic Dev Stack workflow
- Maintain stateless backend architecture
- Use MCP tools exclusively for task operations
- Integrate OpenAI Agents SDK correctly
- Support database-persisted conversations

Plan Structure Requirements (with Chat Widget UI as primary UX):
- Foundation & Safety Setup (Phase-II regression protection, environment validation)
- Database Extensions (Conversation/Message models, backward-compatible migrations)
- MCP Server Design (tool definitions, stateless execution)
- AI Agent Design (intent detection, tool selection, confirmations)
- Chat API Implementation (stateless lifecycle, history loading/persistence)
- Chat Widget Integration (floating FAB, modal/slide-over, responsive)
- Security & Auth Validation (Better Auth, user isolation)
- Testing & Verification (Phase-II regression, tool validation, stateless behavior)
- Deployment Readiness (environment variables, production safety)

Planning Constraints & RAG/MCP Enforcement:
- No implementation details or task granularity
- Implementation-order aware
- Validation checkpoints per phase
- MCP Tools > Database > RAG priority order
- No prohibited RAG usage (CRUD, live state, decision-making)

Chat Widget Requirements:
- Floating action button (FAB) on authenticated pages
- Opens in slide-over/modal (no navigation away)
- Responsive (mobile/tablet/desktop)
- Uses /api/{user_id}/chat endpoint
- Fully isolated from Phase-II logic
- Removable without side effects
- Graceful API downtime handling
```

## Response snapshot

Created comprehensive Phase-III Technical Plan with:

**Executive Summary**:
Build stateless FastAPI chatbot with OpenAI Agents SDK, MCP tools, OpenAI ChatKit UI widget. Persist conversations in database. Zero Phase-II regressions. Horizontal scalability via stateless architecture.

**Technical Context**:
- Language: Python 3.11+
- Backend: FastAPI + OpenAI SDK + MCP SDK + SQLModel
- Database: Neon PostgreSQL (Phase-II shared)
- Auth: Better Auth (Phase-II integration)
- Frontend: React + OpenAI ChatKit
- Performance: 3sec chat latency, 500ms tools, 100 concurrent users

**Constitution Check** (7 Principles):
- ✅ Phase-II Integrity: Database extensions only, Phase-II APIs untouched
- ✅ Stateless Architecture: Load history → process → persist → forget
- ✅ Full CRUD via NL: 7 user stories with P1/P2/P3 prioritization
- ✅ Immutable API: POST /api/{user_id}/chat locked
- ✅ MCP Tooling: 5 tools (add/list/complete/delete/update), stateless
- ✅ Agent Behavior: Intent detection, confirmations, error handling
- ✅ Database Schema: Conversation, Message, Task unchanged

**Project Structure**:
- Backend: src/models/ (Conversation, Message), src/services/ (chat, MCP), src/api/routes/chat.py
- Frontend: components/ChatWidget/ (FAB + modal), services/chatService.ts, contexts/ChatContext.tsx
- Documentation: specs/1-ai-chatbot-integration/ (plan, research, data-model, contracts)
- Tests: Unit tests (chat service, MCP tools), integration tests (regression, persistence), contract tests

**6 Implementation Phases**:

**Phase 0: Research & Validation** (Complete)
- OpenAI Agents SDK for intent detection (GPT-4)
- MCP SDK for stateless tool definitions
- OpenAI ChatKit for React UI
- FastAPI stateless conversation handling
- Conversation history in database (load per request)
- Better Auth token structure (JWT + user_id)
- PostgreSQL schema extension (Alembic migrations)
- Phase-II API integration points

**Phase 1: Foundation & Safety Setup** (Design Complete)
- Database Schema Design: Conversation (user_id, id, created_at, updated_at), Message (user_id, id, conversation_id, role, content, created_at)
- MCP Tool Contracts: add_task, list_tasks, complete_task, delete_task, update_task (inputs, outputs, error cases, statelessness)
- Chat API Contract: POST /api/{user_id}/chat (request/response schema, error responses)
- Authentication & User Isolation: Token extraction, user_id scoping, authorization checks
- Stateless Request Lifecycle: Load → Append → Execute → Persist → Return → Release
- Chat Widget Design: FAB (bottom-right), modal/slide-over, responsive, accessible, removable
- Security & Auth: Token validation, CORS, input sanitization, error messages

Output Artifacts:
- `data-model.md` (entity definitions, relationships, validation)
- `contracts/chat-api.openapi.yml` (API contract, OpenAPI 3.0)
- `contracts/mcp-tools.schema.json` (MCP tool schemas, JSON Schema)
- `quickstart.md` (setup, integration, local dev guide)

**Phase 2: Backend MCP Server & Agent** (Planning)
- MCP Server Setup (tool registration, schema definition)
- Task Management Tools (add_task, list_tasks, complete_task, delete_task, update_task)
- OpenAI Agent Setup (intent detection, tool selection, multi-tool chaining)
- Conversation Persistence Service (creation, history loading, message persistence)
- Chat Request Handling (stateless lifecycle with error handling)
- Testing: Unit tests (tools), integration tests (chat), contract tests (schemas), edge cases

**Phase 3: Frontend Chat Widget** (Planning)
- ChatKit Component Setup (import, configure, styling)
- Chat Widget Component (FAB, modal, messages, input, responses)
- Chat Service & API Integration (chatService.ts, auth context, conversation persistence)
- Phase-II Integration (add to pages, layout mount, task context sharing)
- Responsive Design (mobile, tablet, desktop)
- Testing: Unit tests (widget), integration tests (regression, auth), E2E tests (full flow)

**Phase 4: Security & User Isolation Validation** (Planning)
- Authentication & Authorization (token validation, user_id scoping)
- Data Isolation (multi-user tests)
- Input Validation & Sanitization (injection prevention)
- API Security (CORS, rate limiting, error handling)
- Testing: Security unit tests, multi-user isolation tests, penetration testing

**Phase 5: Testing & Phase-II Regression Verification** (Planning)
- Phase-II Regression Tests (all Phase-II tests pass, CRUD works, auth works, API unchanged)
- Phase-III Functional Tests (all 7 user stories: P1 create/list/complete, P2 update/delete/persistence, P3 multi-turn)
- Stateless Behavior Tests (server restart recovery, concurrent requests, no state leakage)
- MCP Tool Tests (validation, schemas, error handling, idempotency)
- Chat Widget Tests (FAB appearance, modal open/close, history persistence, isolation)
- Integration Tests (chat widget + Phase-II, full CRUD chain)
- Performance Tests (3sec latency, 500ms tools, 100 concurrent, query time)
- Edge Case Tests (gibberish input, network timeout, concurrent updates, rate limiting, empty DB)

Gate: ✅ 100% Phase-II regression pass, ✅ All P1/P2 stories pass, ✅ Stateless verified, ✅ MCP tools validated, ✅ User isolation verified, ✅ Performance targets met, ✅ Chat widget isolated

**Phase 6: Deployment Readiness** (Planning)
- Environment Configuration (.env template, dev/staging/prod configs)
- Domain & Security Setup (ChatKit domain allowlist, CORS, secrets)
- Database Migrations (Alembic + rollback)
- Deployment Procedure (steps, rollback plan, monitoring, logging)
- Documentation (README, architecture, API, operational, user docs)

**RAG & MCP Tool Priority**:
```
MCP Tools (highest) > Database > RAG (lowest)
```
- MCP Tools: add_task, list_tasks, complete_task, delete_task, update_task (all mutations)
- Database: Conversation history, user context, message persistence (reads)
- RAG: Index specs/docs, retrieve context, answer capability questions (no CRUD, no live state)

**Safety & Regression Protection**:
Phase-II Integrity Checkpoints:
- ✅ No schema breaking changes (Conversation/Message additive, Task unchanged)
- ✅ No API contract changes (Phase-II unchanged, chat is new endpoint)
- ✅ No auth system changes (Better Auth unchanged, chat reuses)
- ✅ No frontend route changes (Phase-II routes unchanged, chat widget additive)
- ✅ Test suite passes (Phase-II tests pass before Phase-III)
- ✅ User data integrity (no modifications, no loss)

Constitutional Approvals: All 7 principles PASS Constitution Check. Implementation safe to proceed.

**Source Files Created**:
- `specs/1-ai-chatbot-integration/plan.md` (854 lines, complete plan)
- `specs/1-ai-chatbot-integration/research.md` (450+ lines, Phase 0 findings, 11 research areas, decision tables)
- `specs/1-ai-chatbot-integration/data-model.md` (400+ lines, entity definitions, relationships, validation, migrations)
- `history/prompts/1-ai-chatbot-integration/002-*.plan.prompt.md` (PHR created)

## Outcome

- ✅ Impact: Detailed, implementation-ready technical plan enabling safe Phase-II integration and task decomposition
- 🧪 Tests: Constitution Check (PASS all 7 principles), Phase-II regression scope validated, Phase 1 design complete
- 📁 Files:
  - `specs/1-ai-chatbot-integration/plan.md` (created)
  - `specs/1-ai-chatbot-integration/research.md` (created)
  - `specs/1-ai-chatbot-integration/data-model.md` (created)
  - `history/prompts/1-ai-chatbot-integration/002-*.plan.prompt.md` (PHR created)
- 🔁 Next prompts:
  1. `/sp.tasks` for work breakdown structure (Phase 2)
  2. `/sp.implement` for development execution
- 🧠 Reflection: Plan successfully addresses all planning objectives. 6 implementation phases clearly sequenced. Constitution Check confirms zero Phase-II regressions risk. Phase 1 design complete (research, data model, API contracts). RAG/MCP priority enforced. Chat widget UI integrated as primary UX. Safety gates and regression checkpoints explicit. Ready for task breakdown.

## Evaluation notes (flywheel)

- Failure modes observed: None - plan complete and comprehensive
- Graders run and results (PASS/FAIL): PASS - Constitution Check validated, all 7 principles pass
- Prompt variant (if applicable): N/A - initial creation
- Next experiment: User approval → proceed to `/sp.tasks` for work breakdown

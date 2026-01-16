# Phase III: AI Chatbot Constitution

<!--
Sync Impact Report
==================
Version Bump: 1.0.0 → 1.0.0 (initial Phase-III constitution)
Stage: INITIAL CREATION
Ratified: 2026-01-15
Principles Created: 7 core principles + 3 enforcement sections
All placeholders filled; no deferred items.
Templates Status:
  - spec-template.md: ✅ compatible
  - plan-template.md: ✅ compatible
  - tasks-template.md: ✅ compatible
  - phr-template.md: ✅ compatible
-->

## Constitutional Objectives (Non-Negotiable)

1. Build a fully functional AI-powered Todo Chatbot
2. Integrate seamlessly with Phase-II TODO Web App without breaking changes
3. Ensure zero regressions to Phase-II functionality
4. Support full CRUD operations via natural language
5. Enforce stateless backend architecture
6. Maintain production readiness and scalability

## Core Principles

### I. Phase-II Integrity (CRITICAL)

The existing Phase-II TODO Web App MUST remain fully functional at all times. No breaking changes are permitted to:
- Authentication system
- Database schema (backward-compatible extensions only)
- API contracts and endpoints
- Frontend routes and state management
- User data or workflows

**Enforcement**: Every Phase-III change must pass Phase-II regression testing before acceptance. If a change impacts Phase-II, it requires explicit architectural review and constitutional amendment.

### II. Stateless Server Architecture

All conversation and task state MUST persist in the database. The backend holds NO in-memory state.

**Rules**:
- Server restarts must not affect conversations or task operations
- Each API request must fetch required context from the database
- No session memory, no cached user state, no global variables holding user data
- All state transitions must be atomic and database-backed

**Rationale**: Enables horizontal scaling, fault tolerance, and deterministic behavior across service instances.

### III. Full CRUD via Natural Language

Users must be able to perform all todo operations through conversational AI:
- **Create**: "Add a task to buy groceries"
- **Read**: "Show me my tasks", "What's due today?"
- **Update**: "Mark task 5 as complete", "Change the title of my first task"
- **Delete**: "Remove the grocery task"

**Rules**:
- AI Agent MUST understand intent from free-form text
- Agent MUST confirm actions before execution
- Agent MUST provide clear feedback on success/failure
- Agent MUST never execute ambiguous or unsafe operations

### IV. Immutable API Contract

The Chat API endpoint is the primary integration point:

**Endpoint**: `POST /api/{user_id}/chat`

**Request**:
```json
{
  "conversation_id": "optional-uuid",
  "message": "user input text"
}
```

**Response**:
```json
{
  "conversation_id": "uuid",
  "response": "assistant message",
  "tool_calls": ["add_task", "complete_task"],
  "status": "success"
}
```

**Enforcement**: Breaking this contract is strictly forbidden. Any changes require versioning and migration plan.

### V. MCP Tooling Constitution (MANDATORY)

The MCP (Model Context Protocol) Server MUST expose exactly these tools:

- `add_task` - Create new todo
- `list_tasks` - Retrieve todos (filtered or all)
- `complete_task` - Mark todo as done
- `delete_task` - Remove todo
- `update_task` - Modify todo title/description

**Tool Rules**:
- Tools are stateless (database-backed only)
- Agent must never manipulate database directly
- All task operations MUST go through MCP tools
- Tools must return clear success/error responses
- Tool errors must not crash the agent

**Rationale**: Isolates AI agent from direct data access, ensures audit trail, enables tool reuse.

### VI. Agent Behavior Standards

The OpenAI Agent (via Agents SDK) MUST:

- Use natural language understanding to interpret user intent
- Select the correct MCP tool for the operation
- Chain multiple tools when necessary (e.g., list tasks then complete one)
- Confirm destructive actions before execution
- Handle errors gracefully with user-friendly messages
- Never hallucinate task IDs or modify tasks without explicit user intent
- Provide context-aware responses referencing specific tasks by title/ID

**Example Flow**:
1. User: "Delete my oldest task"
2. Agent: Calls `list_tasks` → identifies oldest → asks "Delete 'Grocery Shopping'? (Yes/No)"
3. User: "Yes"
4. Agent: Calls `delete_task` → confirms deletion

### VII. Database Schema & Persistence

The following models MUST exist and MUST NOT be altered incompatibly:

**Task**
- `user_id`: Foreign key to user (from Phase-II auth)
- `id`: UUID primary key
- `title`: Task name
- `description`: Optional details
- `completed`: Boolean status
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Conversation**
- `user_id`: Foreign key to user
- `id`: UUID primary key
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Message**
- `user_id`: Foreign key to user
- `id`: UUID primary key
- `conversation_id`: Foreign key to conversation
- `role`: "user" or "assistant"
- `content`: Message text
- `created_at`: Timestamp

**Constraint**: No schema changes without Phase-II compatibility assessment and data migration plan.

## Technology Stack (Locked & Immutable)

### Frontend
- **UI Framework**: OpenAI ChatKit (official React component library)
- **Integration**: Embedded within existing Phase-II frontend
- **Requirements**: Responsive, accessible, production-ready
- **No modifications** to existing Phase-II components

### Backend
- **Language/Framework**: Python + FastAPI
- **AI Engine**: OpenAI Agents SDK (official)
- **Tool Protocol**: MCP SDK (Model Context Protocol, official)
- **ORM**: SQLModel
- **No async/await** for state management (request-response only)

### Database
- **Provider**: Neon Serverless PostgreSQL (Phase-II compatible)
- **ORM**: SQLModel (type-safe SQL)
- **Migrations**: Alembic-compatible schema changes
- **No schema breaking changes** without migration path

### Authentication
- **System**: Better Auth (Phase-II integrated)
- **Constraint**: All API requests MUST authenticate via existing Phase-II user tokens
- **Scope**: AI chatbot inherits user context from Phase-II sessions

## Conversation Lifecycle (Stateless Flow)

Every request MUST follow this order:

1. **Receive**: User message + conversation_id (optional)
2. **Authenticate**: Verify user token (Phase-II Better Auth)
3. **Load**: Fetch conversation history from database
4. **Append**: Add new user message to history
5. **Run**: Execute OpenAI Agent with MCP tools + conversation context
6. **Persist**: Store assistant response in database
7. **Return**: Send response to client
8. **Forget**: Release all in-memory state

**Critical**: No state retained after response. Each request is independent.

## Deployment & Security Constitution

### Configuration Management
- All secrets stored in `.env` (never hardcoded)
- Environment-specific configs: `.env.local` (development), `.env.production` (production)
- Document required environment variables in README

### Domain & CORS
- ChatKit domain allowlist enforced (no cross-domain token leaks)
- CORS headers respect Phase-II authentication boundary
- API endpoints protected by user authentication

### Secret Management
- OpenAI API key required (stored in `.env`)
- Database credentials isolated per environment
- No credentials in git history, code, or logs

### Scaling & Reliability
- Stateless design enables horizontal scaling
- Database is single source of truth
- No server affinity required
- Automatic rollback on deployment failure

## Phase-II Regression Test Requirements

Every Phase-III change MUST pass these verification gates:

- [ ] Existing TODO UI renders without errors
- [ ] CRUD endpoints (GET /tasks, POST /tasks, etc.) behave identically
- [ ] Authentication flows unchanged (login, logout, session)
- [ ] Database migrations are backward-compatible
- [ ] API rate limiting unaffected
- [ ] Existing tests pass (Phase-II test suite)
- [ ] User data integrity maintained

**Enforcement**: No code merges without explicit Phase-II regression sign-off.

## Development Workflow (ENFORCED)

All Phase-III work MUST follow:

1. **Specification** (Spec-Kit Plus format) - define requirements
2. **Planning** (Architecture + design decisions) - design solution
3. **Tasking** (Breakdown into testable items) - identify work
4. **Implementation** (Claude Code execution) - build with oversight
5. **Review** (Phase-II regression + acceptance) - verify quality

**Deviation Rule**: Any deviation from this workflow is a constitutional violation.

## MCP Tool Specifications

Each tool MUST adhere to these contracts:

### add_task
- **Input**: `title` (required), `description` (optional), `user_id`
- **Output**: `{ "id": "uuid", "status": "created" }`
- **Error Cases**: Missing title, user not found, database error
- **Idempotency**: Multiple identical requests should fail gracefully (prevent duplicates)

### list_tasks
- **Input**: `user_id`, `filter` (optional: "completed", "pending", "all")
- **Output**: `{ "tasks": [...], "count": int }`
- **Error Cases**: User not found, invalid filter
- **Ordering**: Default by created_at descending (newest first)

### complete_task
- **Input**: `task_id`, `user_id`
- **Output**: `{ "id": "uuid", "status": "completed" }`
- **Error Cases**: Task not found, task already completed, unauthorized user
- **Idempotency**: Completing twice returns success (no-op)

### delete_task
- **Input**: `task_id`, `user_id`
- **Output**: `{ "id": "uuid", "status": "deleted" }`
- **Error Cases**: Task not found, unauthorized user
- **Permanent**: No soft deletes; data is unrecoverable

### update_task
- **Input**: `task_id`, `user_id`, `updates` (title/description fields)
- **Output**: `{ "id": "uuid", "status": "updated", "changes": {...} }`
- **Error Cases**: Task not found, unauthorized user, invalid fields
- **Validation**: Title must not be empty; description is optional

## Success Criteria (Acceptance Gates)

The project is considered **complete** only if ALL of these pass:

- ✅ Users can create, read, update, delete todos via natural language chat
- ✅ AI agent responds contextually and confirms actions
- ✅ All conversations persist across server restarts
- ✅ Phase-II TODO app remains fully functional
- ✅ Database schema is clean and indexed appropriately
- ✅ System handles >100 concurrent users without degradation
- ✅ No state loss or data corruption on failures
- ✅ All environment-specific configs properly separated
- ✅ Error messages are user-friendly and actionable
- ✅ Security: No data leaks, proper authentication boundaries
- ✅ Code is clean, testable, documented per constitution

## Governance

### Amendment Procedure
- Amendments require explicit user intent with documented rationale
- Changes must be reflected in specification, plan, and tasks
- Version updates follow semantic versioning (MAJOR.MINOR.PATCH):
  - **MAJOR**: Backward-incompatible changes (API contract breaks, schema migrations, auth changes)
  - **MINOR**: New principles or capability additions (new MCP tools, new conversation features)
  - **PATCH**: Clarifications, wording, non-semantic refinements

### Compliance Verification
- Code reviews confirm adherence to all principles
- Phase-II regression tests validate integrity
- Architecture reviews verify stateless design
- Database migrations must include rollback plan

### Enforcement Checkpoints
- Every spec review confirms Phase-II safety
- Every plan confirms stateless architecture
- Every task confirms MCP tool consistency
- Every implementation passes Phase-II tests before merge

### Conflict Resolution
If Phase-III requirements conflict with Phase-II integrity, **Phase-II protection takes absolute priority**. Modifications MUST be additive and backward-compatible.

---

**Version**: 1.0.0 | **Ratified**: 2026-01-15 | **Last Amended**: 2026-01-15

**Next Steps**:
1. User approval of this constitution
2. Create Phase-III Feature Specification
3. Generate Technical Plan
4. Break into Tasks
5. Begin Implementation

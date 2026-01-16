# Data Model: AI-Powered Todo Chatbot

**Date**: 2026-01-15 | **Status**: Final Design

---

## Entity Definitions

### 1. Conversation Model

**Purpose**: Represents a chat session between a user and the AI assistant. Groups related messages together.

**Database Table**: `conversation`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique conversation identifier (generated on creation) |
| `user_id` | UUID | FK → user, NOT NULL | Foreign key to Phase-II user (ensures user isolation) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Conversation creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last message timestamp (updated when messages added) |

**Indexes**:
- Primary key on `id`
- Unique constraint: `(user_id, id)` (enables per-user conversation queries)
- Index on `user_id` (for fast user conversation lookup)
- Index on `created_at` (for ordering conversations by recency)

**Relationships**:
- One Conversation has many Messages (1:N relationship)
- Each Conversation belongs to one User (N:1 relationship)

**Constraints**:
- `user_id` must exist in Phase-II user table (referential integrity)
- No deletion allowed (archive strategy: set `deleted_at` timestamp if needed later)
- `created_at` immutable (never updated after creation)

**State Transitions**:
- NEW → ACTIVE (on creation)
- ACTIVE → CLOSED (soft delete: set `deleted_at`, not in plan but future-proof)

**Example Data**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "12345678-1234-1234-1234-123456789012",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:35:00Z"
}
```

---

### 2. Message Model

**Purpose**: Represents a single message in a conversation. Stores both user input and assistant responses.

**Database Table**: `message`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique message identifier (generated per message) |
| `user_id` | UUID | FK → user, NOT NULL | Foreign key to Phase-II user (enables user-scoped queries) |
| `conversation_id` | UUID | FK → conversation, NOT NULL | Foreign key to parent conversation (groups messages) |
| `role` | ENUM | NOT NULL, CHECK IN ('user', 'assistant') | Message source: "user" (user input) or "assistant" (AI response) |
| `content` | TEXT | NOT NULL | Message body (user question or assistant response) |
| `tool_calls` | JSONB | NULL | (Optional) Array of MCP tool calls executed by agent (for assistant messages only) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Message creation timestamp (UTC) |

**Indexes**:
- Primary key on `id`
- Foreign key index on `conversation_id` (for message retrieval per conversation)
- Foreign key index on `user_id` (for user-scoped queries)
- Composite index on `(conversation_id, created_at)` (for ordered message retrieval)

**Relationships**:
- Many Messages belong to one Conversation (N:1)
- Many Messages belong to one User (N:1)

**Constraints**:
- `conversation_id` must exist in Conversation table (referential integrity)
- `user_id` must match conversation owner (enforce at application level)
- `user_id` must exist in Phase-II user table (referential integrity)
- `role` must be one of: "user", "assistant" (enum)
- `content` must not be empty (enforced at application level)

**Validation Rules**:
- `role = "user"`: content is user query (100–5000 characters)
- `role = "assistant"`: content is agent response (arbitrary length)
- `tool_calls` (optional, assistant messages only): JSON array of tool execution records

**Example Data (User Message)**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "12345678-1234-1234-1234-123456789012",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "user",
  "content": "Add a task to buy groceries",
  "tool_calls": null,
  "created_at": "2026-01-15T10:30:15Z"
}
```

**Example Data (Assistant Message)**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440002",
  "user_id": "12345678-1234-1234-1234-123456789012",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "assistant",
  "content": "I'll add 'Buy groceries' to your tasks. Ready? (Yes/No)",
  "tool_calls": [
    {
      "tool": "add_task",
      "status": "pending_confirmation"
    }
  ],
  "created_at": "2026-01-15T10:30:30Z"
}
```

---

### 3. Task Model (Phase-II Extension)

**Purpose**: Represents a todo item. Extends Phase-II Task model (backward-compatible).

**Database Table**: `task` (existing Phase-II table)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique task identifier (from Phase-II) |
| `user_id` | UUID | FK → user, NOT NULL | Foreign key to Phase-II user (ensures user isolation) |
| `title` | VARCHAR(255) | NOT NULL | Task title/name (1–255 characters) |
| `description` | TEXT | NULL | Optional detailed description |
| `completed` | BOOLEAN | NOT NULL, DEFAULT FALSE | Task status (false = pending, true = completed) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Task creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last modification timestamp (UTC) |
| `[Phase-II fields]` | ... | ... | All existing Phase-II Task fields preserved (backward-compatible) |

**Indexes** (existing):
- Primary key on `id`
- Index on `user_id` (for user task lookup)
- Index on `completed` (for status filtering)
- Composite index on `(user_id, completed)` (for user task filtering)
- Index on `created_at` (for ordering)

**Relationships**:
- Many Tasks belong to one User (N:1)
- Tasks referenced by MCP tools (add_task, list_tasks, complete_task, delete_task, update_task)

**Constraints**:
- `user_id` must exist in Phase-II user table (referential integrity)
- `title` must not be empty (enforced at application level)
- `completed` must be boolean (true/false)
- **NO SCHEMA CHANGES** to existing fields (backward-compatible only)

**Validation Rules** (MCP Tool Enforcement):
- `title`: required, 1–255 characters, non-empty, no XSS injection
- `description`: optional, max 5000 characters
- `completed`: boolean only (true/false)

**Example Data**:
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440003",
  "user_id": "12345678-1234-1234-1234-123456789012",
  "title": "Buy groceries",
  "description": "Get organic vegetables and milk",
  "completed": false,
  "created_at": "2026-01-15T10:30:45Z",
  "updated_at": "2026-01-15T10:30:45Z"
}
```

---

## Relationships & Constraints

### Entity Relationship Diagram

```
User (Phase-II)
  ├─ 1:N ─ Conversation
  │         ├─ 1:N ─ Message
  │         │         └─ references Tool Calls (JSON)
  │         └─ (user_id FK)
  │
  └─ 1:N ─ Task (existing Phase-II)
           └─ (user_id FK)
```

### Data Flow

**Chat Request → Response Flow**:
1. User sends message via ChatWidget (POST /api/{user_id}/chat)
2. System loads conversation history from Message table (WHERE conversation_id = :id AND user_id = :user_id)
3. Agent processes history + current message, invokes MCP tools
4. MCP tools query/mutate Task table (WHERE user_id = :user_id) — all operations user-scoped
5. System persists agent response to Message table (new Message row)
6. Response includes tool call results + agent-generated text
7. ChatWidget displays response and updates conversation history

**User Isolation**: All queries filtered by `user_id` at application layer:
- Conversation query: `WHERE user_id = :user_id`
- Message query: `WHERE user_id = :user_id AND conversation_id = :conversation_id`
- Task query (via MCP tools): `WHERE user_id = :user_id`

---

## Database Migration Strategy

### Alembic Migrations (Phase-II Standard)

**Migration 1: Create Conversation Table**
```sql
CREATE TABLE conversation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversation_user_id ON conversation(user_id);
CREATE INDEX idx_conversation_created_at ON conversation(created_at);
```

**Migration 2: Create Message Table**
```sql
CREATE TABLE message (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    tool_calls JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_message_conversation_id ON message(conversation_id);
CREATE INDEX idx_message_user_id ON message(user_id);
CREATE INDEX idx_message_conversation_created ON message(conversation_id, created_at);
```

**Backward Compatibility**:
- No modifications to existing Task table
- New tables added (additive only)
- Existing Phase-II data unaffected
- Migrations reversible (down scripts provided)

**Rollback Procedure**:
- Drop Message table
- Drop Conversation table
- No data loss (Phase-II tables unchanged)

---

## Data Validation & Constraints

### Application-Level Validation

**Conversation Model**:
- `user_id`: Must exist in Phase-II user table (verify before creation)
- Cannot be deleted (soft delete strategy if needed)

**Message Model**:
- `user_id`: Must match conversation owner (enforce on insert)
- `conversation_id`: Must exist and belong to user (foreign key + application check)
- `role`: Must be "user" or "assistant" (enum/check constraint)
- `content`: Must not be empty, max 10000 characters (application validation)
- `tool_calls` (optional): Must be valid JSON array if present

**Task Model** (via MCP Tools):
- `title`: Required, 1–255 characters (MCP tool validates)
- `description`: Optional, max 5000 characters (MCP tool validates)
- `completed`: Boolean only (database constraint)
- `user_id`: Must match authenticated user (application enforces)

### Error Cases & Handling

| Scenario | Validation | Error Response |
|----------|-----------|-----------------|
| User creates conversation | user_id exists in user table | 401 Unauthorized if invalid |
| Message added to conversation | conversation_id exists + belongs to user | 404 Not Found if missing |
| Task created via MCP | title not empty, user_id valid | Tool returns error message |
| Task updated via MCP | title not empty, task exists, user owns it | Tool returns error message |
| Task deleted via MCP | task exists, user owns it | Tool returns confirmation |
| Empty user message | content not empty | Chat rejects, asks for clarification |
| Invalid user_id | user_id in token matches authenticated user | 401 Unauthorized |

---

## Performance Considerations

### Query Optimization

**Conversation Retrieval** (frequent):
- Index on `user_id` for user's conversations
- Index on `created_at` for ordering
- Expected: <100ms for typical user (< 100 conversations)

**Message Retrieval** (frequent):
- Composite index on `(conversation_id, created_at)` for ordered retrieval
- Index on `user_id` for backup filtering
- Expected: <50ms for typical conversation (< 1000 messages)

**Task Retrieval** (via MCP tools):
- Existing Phase-II indexes on Task table
- `(user_id, completed)` for filtering
- Expected: <100ms for typical user (< 10K tasks)

### Scalability

- **Conversations per user**: Unlimited (indexed by user_id)
- **Messages per conversation**: Unlimited (indexed by conversation_id)
- **Concurrent users**: 100+ (stateless backend, database pool scales)
- **Retention**: Indefinite (no archival in MVP; can add in Phase IV)

---

## Summary

**New Entities**:
- ✅ Conversation: groups messages per user
- ✅ Message: stores user/assistant messages + tool calls

**Extended Entities**:
- ✅ Task: unchanged, used by MCP tools for CRUD operations

**User Isolation**:
- ✅ All queries filtered by `user_id`
- ✅ Referential integrity enforced
- ✅ Foreign keys prevent cross-user access

**Backward Compatibility**:
- ✅ No Phase-II Task table modifications
- ✅ Additive migrations only
- ✅ Reversible (rollback supported)

**Ready for API contract definition and implementation.**

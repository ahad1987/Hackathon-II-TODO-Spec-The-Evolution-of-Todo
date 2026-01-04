# Data Model: Phase I - In-Memory Python Console Todo App

**Date**: 2026-01-05
**Feature**: Phase I - In-Memory Python Console Todo App
**Status**: Phase 1 Complete

---

## Domain Model

### Task Entity

The **Task** is the core domain object representing a single todo item.

#### Attributes

| Attribute | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `id` | int | Yes | Auto-incremented, unique, never reused | Unique identifier assigned at creation; sequential from 1 |
| `title` | str | Yes | 1–100 characters, no leading/trailing whitespace | Brief summary of the task; displayed in list view |
| `description` | str \| None | No | 0–500 characters, defaults to empty string | Optional additional details; shown in list view if present |
| `status` | Enum["incomplete", "complete"] | Yes | Always "incomplete" OR "complete" | Current state of the task; defaults to "incomplete" |
| `created_at` | datetime | Yes | ISO 8601 timestamp (YYYY-MM-DDTHH:MM:SS) | When the task was created; used for sorting in Phase II |

#### Validation Rules

| Field | Rule | Error Message | Source |
|-------|------|---------------|---------
| title | Required (non-empty, non-whitespace) | "Title cannot be empty" | FR-001 |
| title | Max 100 characters | "Title exceeds 100 characters" | Spec assumption |
| title | Strip leading/trailing whitespace | N/A (automatic) | Spec assumption |
| description | Optional; if provided, max 500 characters | "Description exceeds 500 characters" | Spec assumption |
| description | Strip leading/trailing whitespace | N/A (automatic) | Spec assumption |
| status | Must be "incomplete" or "complete" | "Invalid status value" | FR-006, FR-007 |
| id | Numeric; must exist in store | "Task ID must be numeric", "Task ID {id} not found" | FR-011 |

#### State Transitions

```
┌─────────────────────────────────────────┐
│  New Task (id assigned, status created) │
│  ├─ id = next_id (e.g., 1, 2, 3)       │
│  ├─ title = user input (trimmed)        │
│  ├─ description = user input or None    │
│  ├─ status = "incomplete"               │
│  └─ created_at = current timestamp      │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  Complete Transition (command: complete) │
│  └─ status: "incomplete" → "complete"   │
└─────────────────────────────────────────┘
           ↕ (bidirectional)
┌─────────────────────────────────────────┐
│  Incomplete Transition (cmd: incomplete)│
│  └─ status: "complete" → "incomplete"   │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  Update Transition (command: update)    │
│  ├─ title ← new value (optional)        │
│  ├─ description ← new value (optional)  │
│  ├─ status unchanged                    │
│  └─ id unchanged                        │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  Delete Transition (command: delete)    │
│  └─ Task removed from store entirely    │
│     (id never reused; id sequence       │
│      continues incrementally)            │
└─────────────────────────────────────────┘
```

#### Example Task JSON Representation (Phase II)

```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "incomplete",
  "created_at": "2026-01-05T10:30:00"
}
```

---

## Storage Layer: TaskStore

The **TaskStore** class manages the in-memory collection of tasks and ID generation.

### Attributes

| Attribute | Type | Purpose | Initialization |
|-----------|------|---------|-----------------|
| `tasks` | dict[int, Task] | All tasks indexed by ID | {} (empty dict) |
| `next_id` | int | Next available ID for new tasks | 1 |

### Methods

#### `add_task(title: str, description: str | None = None) -> Task`

**Behavior**:
1. Validate title (non-empty, max 100 chars)
2. Validate description (max 500 chars if provided)
3. Create Task with id=next_id, status="incomplete", created_at=now
4. Store in tasks dict: tasks[next_id] = task
5. Increment next_id
6. Return Task

**Error Cases**:
- Title is empty → raise ValueError("Title cannot be empty")
- Description exceeds 500 chars → raise ValueError("Description exceeds 500 characters")

**Example**:
```python
task = store.add_task("Buy milk", "2% fat")
# → Task(id=1, title="Buy milk", description="2% fat", status="incomplete", created_at=...)
store.next_id  # → 2
```

#### `get_task(task_id: int) -> Task | None`

**Behavior**:
1. Look up task_id in tasks dict
2. Return Task if found; None if not found

**Error Cases**:
- task_id is not numeric → caller should validate and raise ValueError
- task_id not in dict → return None (or raise TaskNotFound if stricter behavior needed)

**Example**:
```python
task = store.get_task(1)
# → Task(id=1, ...)

task = store.get_task(999)
# → None (or TaskNotFound)
```

#### `list_tasks() -> list[Task]`

**Behavior**:
1. Return list of all Task objects in dict
2. Order: insertion order (Python 3.7+ dicts maintain order)

**Example**:
```python
tasks = store.list_tasks()
# → [Task(id=1, ...), Task(id=2, ...), ...]
```

#### `update_task(task_id: int, title: str | None = None, description: str | None = None) -> Task`

**Behavior**:
1. Get task (raise TaskNotFound if not exists)
2. If title provided: validate and update task.title
3. If description provided: validate and update task.description
4. If neither provided: raise ValueError("Must provide title or description")
5. Return updated Task

**Error Cases**:
- task_id not found → raise TaskNotFound(f"Task ID {task_id} not found")
- Both title and description None → raise ValueError("Provide new title or --desc <description>")
- Title exceeds 100 chars → raise ValueError("Title exceeds 100 characters")
- Description exceeds 500 chars → raise ValueError("Description exceeds 500 characters")

**Example**:
```python
task = store.update_task(1, title="Buy organic milk")
# → Task(id=1, title="Buy organic milk", description="2% fat", status="incomplete", ...)

task = store.update_task(1, description="Skim milk")
# → Task(id=1, title="Buy organic milk", description="Skim milk", status="incomplete", ...)
```

#### `delete_task(task_id: int) -> None`

**Behavior**:
1. Check if task_id exists
2. Remove from tasks dict: del tasks[task_id]
3. Do NOT decrement next_id (IDs continue sequentially; never reused)

**Error Cases**:
- task_id not found → raise TaskNotFound(f"Task ID {task_id} not found")

**Example**:
```python
store.delete_task(2)
# tasks[2] removed; next_id stays at 4 (doesn't go back to 3)
```

#### `complete_task(task_id: int) -> Task`

**Behavior**:
1. Get task (raise TaskNotFound if not exists)
2. Set task.status = "complete"
3. Return updated Task

**Error Cases**:
- task_id not found → raise TaskNotFound(f"Task ID {task_id} not found")

**Example**:
```python
task = store.complete_task(1)
# → Task(id=1, ..., status="complete", ...)
```

#### `incomplete_task(task_id: int) -> Task`

**Behavior**:
1. Get task (raise TaskNotFound if not exists)
2. Set task.status = "incomplete"
3. Return updated Task

**Error Cases**:
- task_id not found → raise TaskNotFound(f"Task ID {task_id} not found")

**Example**:
```python
task = store.incomplete_task(1)
# → Task(id=1, ..., status="incomplete", ...)
```

---

## Exception Hierarchy

```
Exception (Python built-in)
├── ValueError
│   ├── (Python built-in for invalid values)
│   └── Used for: title empty, exceeds max length, description exceeds max length
│
└── Custom Exceptions (in services/todo_service.py)
    ├── TaskNotFound(Exception)
    │   └── Raised when task_id doesn't exist in store
    │
    └── InvalidTaskID(ValueError)
        └── Raised when task_id is non-numeric or invalid format
```

---

## CLI Command → Service Method Mapping

| Command | Service Method(s) | Input Args | Output |
|---------|------------------|-----------|--------|
| `add <title> [description]` | store.add_task(title, description) | title (required), description (optional) | Task object (formatted for display) |
| `list` | store.list_tasks() | None | List of all Task objects (formatted for display) |
| `update <id> [title] [--desc description]` | store.update_task(task_id, title, description) | id (required), title (optional), --desc description (optional) | Updated Task object (formatted for display) |
| `delete <id>` | store.delete_task(task_id) | id (required) | None (confirmation message) |
| `complete <id>` | store.complete_task(task_id) | id (required) | Updated Task object (formatted for display) |
| `incomplete <id>` | store.incomplete_task(task_id) | id (required) | Updated Task object (formatted for display) |
| `exit` | (main loop termination) | None | None (app exits) |

---

## Display Format & Rendering

### Welcome Menu (on startup)

```
Welcome to Todo App
Available commands:
  add <title> [description]       Add a new task
  list                            View all tasks
  update <id> [title] [--desc]    Update a task
  delete <id>                     Delete a task
  complete <id>                   Mark task as complete
  incomplete <id>                 Mark task as incomplete
  exit                            Exit the app
```

### List Display (when user enters `list` command)

**When tasks exist**:

```
ID │ Status │ Title                    │ Description
───┼────────┼──────────────────────────┼─────────────────────
 1 │   ☐    │ Buy groceries            │ Milk, eggs, bread
 2 │   ✓    │ Review PR                │
 3 │   ☐    │ Fix bug in login         │ Check email flow
```

**When no tasks exist**:

```
No tasks yet. Add one with: add <title> [description]
```

### Confirmation Messages

| Action | Message |
|--------|---------|
| Add task | "Task added with ID: {id}" |
| Update task | "Task {id} updated" |
| Delete task | "Task {id} deleted" |
| Mark complete | "Task {id} marked complete (✓)" |
| Mark incomplete | "Task {id} marked incomplete (☐)" |

### Error Messages

| Scenario | Message |
|----------|---------|
| Empty title | "Title cannot be empty" |
| Title too long | "Title exceeds 100 characters" |
| Description too long | "Description exceeds 500 characters" |
| Task ID not found | "Task ID {id} not found" |
| Invalid task ID | "Task ID must be numeric" |
| Add command missing title | "Title is required. Usage: add <title> [description]" |
| Update command missing id | "Task ID is required. Usage: update <id> [title] [--desc description]" |
| Update command missing both title and desc | "Provide new title or --desc <description>. Usage: update <id> [title] [--desc description]" |
| Delete command missing id | "Task ID is required. Usage: delete <id>" |
| Unknown command | "Unknown command '{command}'. Available: add, list, update, delete, complete, incomplete, exit" |

---

## Phase II Extensibility Points

The Task entity and TaskStore are designed to evolve seamlessly into Phase II:

### Database Layer Replacement

Phase II will replace in-memory dict with database queries:

```python
# Phase I: In-memory
def get_task(self, task_id: int) -> Task:
    return self.tasks.get(task_id)

# Phase II: Database (same interface)
def get_task(self, task_id: int) -> Task:
    task_row = self.db.query(Task).filter(Task.id == task_id).first()
    return task_row
```

### API Serialization

Task attributes map directly to JSON (Phase II REST API):

```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "incomplete",
  "created_at": "2026-01-05T10:30:00"
}
```

### Service Methods as Endpoints

Each TaskStore method becomes an API endpoint (Phase II):

```
POST /tasks                    → add_task()
GET /tasks                     → list_tasks()
PATCH /tasks/{id}             → update_task()
DELETE /tasks/{id}            → delete_task()
POST /tasks/{id}/complete     → complete_task()
POST /tasks/{id}/incomplete   → incomplete_task()
```

### ORM Attributes (Phase II)

Task class can extend with ORM attributes without breaking Phase I:

```python
# Phase I: Simple data class
class Task:
    id: int
    title: str
    description: str
    status: str
    created_at: datetime

# Phase II: SQLAlchemy ORM
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # NEW
```

---

## Summary

The Task entity and TaskStore provide:
- ✅ Clean domain model with validation rules
- ✅ Simple in-memory storage (dict-based)
- ✅ All CRUD operations as named methods
- ✅ Error handling with custom exceptions
- ✅ Direct CLI command mapping
- ✅ Ready for Phase II database layer replacement
- ✅ Extensible for Phase III AI integration
- ✅ Supports all 5 core principles (Correctness, Simplicity, Determinism, Spec-Driven, Incremental Design)

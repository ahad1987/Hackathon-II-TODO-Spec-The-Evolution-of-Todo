# Implementation Plan: Phase I - In-Memory Python Console Todo App

**Branch**: `001-cli-todo-app` | **Date**: 2026-01-05 | **Spec**: [specs/001-cli-todo-app/spec.md](spec.md)

**Input**: Feature specification with 5 user stories (Add, List, Update, Delete, Complete/Incomplete), 14 functional requirements, and 8 measurable success criteria.

## Summary

Implement a Python 3.13+ command-line todo application with in-memory storage, deterministic behavior, and modular architecture designed for Phase II extensibility. All five core CRUD operations must execute synchronously with clear error handling, graceful input validation, and human-readable output. The codebase will be architecturally clean, enabling seamless evolution into Phase II (FastAPI + Database) without redesign.

## Technical Context

**Language/Version**: Python 3.13+ (specified in constitution)
**Primary Dependencies**: Python standard library only (no third-party packages)
**Storage**: In-memory only (lists and dictionaries; no file I/O, no database)
**Testing**: Python unittest/pytest compatible structure (tests can use stdlib or standard test runners)
**Target Platform**: Linux/macOS/Windows CLI (stdin/stdout)
**Project Type**: Single-process CLI application
**Performance Goals**: All commands execute in <100ms (local in-memory operations); support 100+ tasks without degradation
**Constraints**: No async/await, no external APIs, no AI integration, no persistence; deterministic and reproducible behavior
**Scale/Scope**: Single-user, in-memory session; data resets on exit; no multi-process or distributed concerns

## Constitution Check

**GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.**

### Five Core Principles Alignment

| Principle | Requirement | Alignment | Status |
|-----------|-------------|-----------|--------|
| **Correctness** | All logic works exactly as specified; no deviations; deterministic output | In-memory state, simple functions, no hidden side effects | ✅ PASS |
| **Simplicity** | Clean, minimal, readable code; prefer straightforward implementations | Single-process, no async, no frameworks; modular functions <30 LOC | ✅ PASS |
| **Determinism** | Predictable behavior; no hidden side effects; explicit state changes | Synchronous execution, no concurrency, no external state | ✅ PASS |
| **Spec-Driven Development** | Implement strictly per spec; no scope creep; requirements are source of truth | Five user stories directly map to code modules; no speculative features | ✅ PASS |
| **Incremental Design** | Phase I extensible for Phase II+; modular structure; minimal coupling | Data model abstraction supports Phase II entities; CLI interface independent from storage | ✅ PASS |

### Technology Stack Constraints Alignment

| Constraint | Requirement | Implementation | Status |
|-----------|-------------|------------------|--------|
| **Language** | Python 3.13+, stdlib only | No third-party packages; standard library modules only | ✅ PASS |
| **Storage** | In-memory only, no file I/O, no DB | Lists/dicts for tasks; no filesystem access | ✅ PASS |
| **Architecture** | Single-process, synchronous | One main loop processing commands serially | ✅ PASS |
| **CLI Interface** | stdin/stdout, clear prompts | read() / print() for I/O; help text on startup | ✅ PASS |
| **Commands** | add, list, update, delete, complete, incomplete, exit | Seven command handlers, all implemented | ✅ PASS |
| **Error Handling** | Helpful messages for invalid input; graceful degradation | Try/except blocks; user-friendly error messages; no unhandled exceptions | ✅ PASS |

**GATE STATUS**: ✅ PASS — No constitution violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/001-cli-todo-app/
├── spec.md                     # Feature specification (5 user stories, 14 FRs)
├── plan.md                     # This file (implementation architecture)
├── research.md                 # Phase 0: Technical decisions and rationale
├── data-model.md               # Phase 1: Domain model (Task entity, state transitions)
├── quickstart.md               # Phase 1: Development setup and run instructions
├── contracts/                  # Phase 1: Command interface contracts (CLI input/output)
│   ├── add-task.md             # add <title> [description] contract
│   ├── list-tasks.md           # list contract
│   ├── update-task.md          # update <id> [title] [--desc description] contract
│   ├── delete-task.md          # delete <id> contract
│   ├── complete-task.md        # complete <id> contract
│   ├── incomplete-task.md      # incomplete <id> contract
│   └── exit.md                 # exit contract
├── checklists/
│   └── requirements.md         # Specification quality validation (PASS)
└── tasks.md                    # Phase 2 (output of /sp.tasks command)
```

### Source Code (repository root)

```text
src/
├── main.py                     # Application entry point and CLI main loop
├── models/
│   └── task.py                 # Task entity (id, title, description, status)
├── services/
│   └── todo_service.py         # Core business logic (add, list, update, delete, complete)
├── cli/
│   └── commands.py             # Command handlers (parse input, call services, format output)
└── lib/
    └── validation.py           # Input validation helpers (parse_id, parse_command, etc.)

tests/
├── unit/
│   ├── test_task_model.py      # Task entity tests
│   ├── test_todo_service.py    # Service logic tests
│   └── test_validation.py      # Input validation tests
├── integration/
│   └── test_cli_commands.py    # End-to-end CLI command tests
└── contract/
    └── test_cli_contracts.py   # Contract tests (input/output formats match spec)
```

**Structure Decision**: Selected **Option 1: Single project** (DEFAULT). Rationale:
- Phase I is a single-process CLI app with one codebase
- Clean separation: models (data), services (business logic), cli (user interface), lib (utilities)
- tests directory mirrors src structure for parallel test discovery
- Modular design enables Phase II extraction: models→API objects, services→endpoints, CLI→web interface
- No monolithic single file; each module has single responsibility per constitution's Simplicity principle

## Architecture Overview

### Domain Model

The **Task** entity is the core of the application:

```python
Task:
  id: int                    # Auto-incremented, unique, never reused
  title: str                 # Required, 1–100 characters, no leading/trailing whitespace
  description: str | None    # Optional, 0–500 characters, defaults to empty string
  status: "incomplete" | "complete"  # Defaults to "incomplete"
  created_at: datetime       # Timestamp when task was created (for future Phase II sorting)
```

**State Transitions**:
- **New Task**: id, title, description, status="incomplete", created_at=now
- **Complete**: status → "complete" (immutable ID, title, description)
- **Incomplete**: status → "incomplete" (reverts from "complete")
- **Update**: title and/or description can be modified; id, status, created_at unchanged
- **Delete**: Task removed entirely; id never reused

### In-Memory Storage Ownership

**TaskStore** (service layer) maintains:
- `tasks`: Dict[int, Task] — All tasks indexed by ID
- `next_id`: int — Next available ID for new tasks (never decremented, persists sequentially)

**Why this design**:
- Dict for O(1) lookup by ID (supports fast update/delete operations)
- next_id ensures sequential IDs that never reuse deleted IDs (per spec requirement FR-012)
- No global variables; tasks are owned and managed by a single service instance
- Supports Phase II: tasks dict can become a database query; next_id becomes SQL sequence

### Core Operations

**Add Task** (FR-001, FR-002):
- Input: title (required), description (optional)
- Process: Validate title; create new Task with next_id; increment next_id; store in dict
- Output: Confirmation message with assigned ID
- Error: "Title is required. Usage: add <title> [description]"

**List Tasks** (FR-003):
- Input: None
- Process: Iterate dict; format each task with status indicator (✓/☐)
- Output: Formatted table or list of all tasks with ID, title, status, description
- Empty case: "No tasks yet. Add one with: add <title> [description]"

**Update Task** (FR-004):
- Input: id (required), title (optional), --desc description (optional)
- Process: Validate ID exists; validate at least one field provided; update Task
- Output: Confirmation message "Task {id} updated"
- Errors: "Task ID not found", "Provide new title or --desc <description>"

**Delete Task** (FR-005):
- Input: id (required)
- Process: Validate ID exists; remove Task from dict
- Output: Confirmation message "Task {id} deleted"
- Error: "Task ID not found"

**Mark Complete** (FR-006):
- Input: id (required)
- Process: Validate ID exists; set status="complete"
- Output: Confirmation "Task {id} marked complete (✓)"
- Error: "Task ID not found"

**Mark Incomplete** (FR-007):
- Input: id (required)
- Process: Validate ID exists; set status="incomplete"
- Output: Confirmation "Task {id} marked incomplete (☐)"
- Error: "Task ID not found"

**Exit** (FR-008):
- Input: exit command
- Process: Terminate main loop
- Output: "Goodbye!"
- Note: Data is lost (in-memory only; confirmed in spec)

### CLI Command Interface

Main loop pattern:
```
1. Display prompt ("todo> " or similar)
2. Read user input
3. Parse command (first word is command, remaining words are args)
4. Route to command handler
5. Call service layer
6. Format and display output
7. Repeat until `exit` command
```

**Command Parsing** (validation.py):
- Split input into [command, *args]
- Lowercase command for case-insensitive matching
- Validate command exists
- Validate argument count per command
- Return parsed command object or error

**Error Handling** (FR-009):
- Invalid command: "Unknown command. Available: add, list, update, delete, complete, incomplete, exit"
- Missing args: Show usage pattern for that command
- Invalid ID: "Task ID must be numeric" or "Task ID not found"
- No unhandled exceptions; all errors caught and formatted

**Startup Menu** (FR-010):
```
Welcome to Todo App
Available commands:
  add <title> [description]     Add a new task
  list                          View all tasks
  update <id> [title] [--desc]  Update a task
  delete <id>                   Delete a task
  complete <id>                 Mark task as complete
  incomplete <id>               Mark task as incomplete
  exit                          Exit the app
```

### Validation & Input Handling (FR-011)

**Task ID Validation**:
- Must be numeric (convert to int; raise ValueError if non-numeric)
- Must exist in tasks dict (check if ID in dict; raise KeyError if not)
- Clear error message: "Task ID {value} is invalid" or "Task ID {id} not found"

**Task Title Validation**:
- Required (cannot be empty or whitespace-only)
- Strip leading/trailing whitespace
- Max 100 characters
- Error: "Title cannot be empty"

**Task Description Validation**:
- Optional
- Strip leading/trailing whitespace
- Max 500 characters
- Error: "Description exceeds 500 characters"

**Command Arguments Validation**:
- `add`: 1–2 args required (title mandatory, description optional)
- `list`: 0 args
- `update`: 2–4 args (id, then title or --desc flag)
- `delete`, `complete`, `incomplete`: 1 arg (id only)
- `exit`: 0 args

## Implementation Order

**Phase 0: Setup** (Prepare project structure)
1. Create `src/` directory structure
2. Create `tests/` directory structure
3. Create `__init__.py` files for Python packages
4. Initialize `main.py` with entry point stub

**Phase 1: Domain Model** (Core data structures)
1. Implement `models/task.py` — Task class with id, title, description, status, created_at
2. Implement `services/todo_service.py` — TodoStore class managing tasks dict and next_id
3. Write unit tests for Task and TodoStore

**Phase 2: CLI Utilities** (Input parsing and validation)
1. Implement `lib/validation.py` — parse_id(), parse_title(), validate_args(), parse_command()
2. Write unit tests for validation helpers

**Phase 3: Command Handlers** (Business logic to UI)
1. Implement `cli/commands.py` — Command handlers for add, list, update, delete, complete, incomplete, exit
2. Each handler: parse args → call service → format output
3. Write integration tests for each command

**Phase 4: Main Application Loop** (CLI entry point)
1. Implement `main.py` — Startup menu, main loop, command routing
2. Call TodoStore initialization
3. Handle exceptions gracefully
4. Write end-to-end tests

**Phase 5: Testing & Verification**
1. Run all unit tests (models, services, validation)
2. Run integration tests (CLI commands)
3. Manual testing: all 5 user stories (Add, List, Update, Delete, Complete/Incomplete)
4. Manual testing: edge cases (empty input, invalid IDs, rapid commands)
5. Verify success criteria (100ms latency, 100+ tasks, help text visible)

## Phase-Extension Readiness Points

**For Phase II (FastAPI + Database)**:

1. **Domain Model Abstraction**: Task class is decoupled from storage; Phase II can extend with ORM attributes (pk, timestamps, indexes) without changing business logic.

2. **Service Layer Independence**: TodoService methods (add_task, list_tasks, etc.) take Task inputs and return Task outputs; Phase II can inject database instead of in-memory dict.

3. **CLI/API Separation**: Commands in cli/commands.py call service methods only; Phase II can create new api/ folder with endpoints that call same service methods.

4. **Error Handling Pattern**: Exceptions are caught and formatted at CLI layer; Phase II can replace with HTTP status codes while keeping service logic unchanged.

5. **No Persistence Logic**: Phase I has zero file I/O or caching; Phase II adds database connection and transaction handling cleanly.

**For Phase III (AI Chatbot)**:

1. **Service Layer Interface**: Existing TodoService methods can be called from chat intent handlers (e.g., "Complete task 1" → service.complete_task(1)).

2. **Task Entity Stability**: Task attributes are stable (id, title, description, status); no breaking changes needed.

**For Phase IV (Kubernetes)**:

1. **Stateless CLI Design**: Phase I is stateless (data reset on exit); Phase IV deployment is trivial (no shared state between pods).

2. **Modular Services**: Service classes are testable and mockable; Phase IV can instrument with logging/metrics at service boundaries.

## Manual Verification Steps

After implementation, verify:

1. **Startup**: Run `python src/main.py`; see welcome menu with all 7 commands.
2. **Add Task**: Enter `add "Buy milk"` → Confirm "Task added with ID: 1".
3. **List Tasks**: Enter `list` → See task with ID 1, title "Buy milk", status "☐".
4. **Add Multiple**: Add 3 more tasks; verify IDs increment (2, 3, 4).
5. **Update Task**: Enter `update 2 "Buy eggs"` → Confirm updated.
6. **List Again**: Verify task 2 has new title.
7. **Complete Task**: Enter `complete 1` → See "Task 1 marked complete (✓)".
8. **List Shows Status**: Task 1 now shows "✓", others show "☐".
9. **Mark Incomplete**: Enter `incomplete 1` → Confirm reverted.
10. **Delete Task**: Enter `delete 3` → Confirm "Task 3 deleted".
11. **List After Delete**: Task 3 gone; IDs 1, 2, 4 remain.
12. **Error Handling**: Enter `delete 999` → See "Task ID 999 not found".
13. **Invalid Command**: Enter `foo` → See helpful error with available commands.
14. **Help Text**: On startup, user can see all commands and usage without external docs.
15. **Exit Command**: Enter `exit` → App terminates cleanly.
16. **Data Reset**: Run app again → No tasks (confirming in-memory only).

## Testing Strategy

**Unit Tests** (tests/unit/):
- Task entity creation, attribute assignment
- TodoStore add, update, delete operations
- ID generation and sequential assignment
- Validation functions (parse_id, parse_title, etc.)
- Status transitions (complete/incomplete)

**Integration Tests** (tests/integration/):
- End-to-end CLI command flows
- Command input parsing and execution
- Output formatting and status indicators
- Error messages for invalid input

**Contract Tests** (tests/contract/):
- Input/output format compliance with spec
- Status indicators (✓ vs ☐) correct
- Error messages match spec requirements
- Help text visible and complete

**Success Criteria Validation**:
- Performance: Time each operation (should be <100ms on any modern machine)
- Scale: Create 100+ tasks; verify no errors or slowdown
- Correctness: All 5 user stories pass independently
- Code quality: No circular dependencies; functions <30 LOC; clear naming

## Non-Functional Requirements

**Performance**:
- Target: <100ms per command (easily achieved with in-memory dict)
- No optimization needed in Phase I; scalable design for Phase II

**Reliability**:
- No crashes on invalid input (all exceptions caught)
- Graceful exit on `exit` command
- No data corruption or inconsistent states

**Maintainability**:
- Modular functions with single responsibility
- Clear naming (add_task, complete_task, etc.)
- Docstrings on public functions
- Comments only where intent is non-obvious

**Extensibility**:
- Service layer supports Phase II database injection
- Task entity attributes stable for all future phases
- CLI commands independent from storage implementation

## Out of Scope (Phase II and Beyond)

- File persistence, database backends
- User authentication or multi-user support
- Rich terminal UI (colors, tables, animations)
- Recurrence, reminders, categories, tags
- Search, filtering, sorting
- API or web interface
- Email notifications, integrations
- Performance optimization (indexing, caching)

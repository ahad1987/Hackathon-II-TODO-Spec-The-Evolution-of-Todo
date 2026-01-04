# Research: Phase I - In-Memory Python Console Todo App

**Date**: 2026-01-05
**Feature**: Phase I - In-Memory Python Console Todo App
**Status**: Phase 0 Complete

---

## Research Questions & Findings

### 1. Python Standard Library for CLI Applications

**Question**: What is the best approach to build a CLI application using only Python standard library?

**Decision**: Use `sys.stdin` and `print()` for I/O; parse commands manually with string operations.

**Rationale**:
- **sys.stdin**: `input()` function (built-in) is sufficient for reading user input
- **print()**: Built-in function outputs to stdout; no need for external libraries
- **Manual parsing**: Split user input by whitespace; match first token to command
- Eliminates dependency on click, typer, or argparse (third-party libraries)
- Matches Phase I constraint: "standard library only"

**Alternatives Considered**:
- **click library**: Popular CLI framework, but violates stdlib-only constraint
- **typer library**: Modern alternative, but also violates stdlib-only constraint
- **argparse module**: Part of stdlib, but adds unnecessary complexity for Phase I's simple commands
- **Decision**: Direct stdin/stdout is simplest and sufficient for 7 commands

**Implementation Pattern**:
```python
while True:
    command_line = input("todo> ").strip()
    if not command_line:
        print_help()
        continue

    parts = command_line.split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    # Route to command handler
    if command == "add":
        handle_add(args)
    elif command == "list":
        handle_list(args)
    ...
```

---

### 2. In-Memory Data Storage Structure

**Question**: What is the best data structure to store tasks in memory with O(1) lookup by ID?

**Decision**: Use Python `dict` (hash map) with ID as key; Task objects as values.

**Rationale**:
- **O(1) lookup**: Finding task by ID is instant (dict key access)
- **O(1) insertion/deletion**: Adding/removing tasks is instant
- **Ordered preservation** (Python 3.7+): Dict maintains insertion order (useful for Phase II sorting)
- **Serializable to JSON**: Dict/list structures easily convert to JSON (Phase II API compatibility)
- **Simple and readable**: No external ORM or data structure library needed

**Alternatives Considered**:
- **List of tuples**: O(n) lookup; requires iteration for find-by-id
- **Custom linked list**: Overkill for in-memory app; no performance benefit
- **SQLite in-memory**: Violates "standard library only" constraint (even with sqlite3, adds SQL complexity)
- **Decision**: Dict is simplest, fastest, and most extensible

**Implementation Pattern**:
```python
class TodoStore:
    def __init__(self):
        self.tasks: dict[int, Task] = {}  # {id: Task}
        self.next_id: int = 1              # Sequence generator

    def add_task(self, title: str, description: str = None) -> Task:
        task = Task(id=self.next_id, title=title, description=description)
        self.tasks[self.next_id] = task
        self.next_id += 1
        return task

    def get_task(self, task_id: int) -> Task | None:
        return self.tasks.get(task_id)
```

---

### 3. Task ID Generation: Sequential vs UUID

**Question**: Should task IDs be sequential integers or UUIDs?

**Decision**: Use sequential integers (1, 2, 3, ...).

**Rationale**:
- **User-friendly**: Sequential IDs are easier to remember and type ("delete 5" vs "delete a1b2c3d4...")
- **Spec requirement**: Spec says "Task ID is numeric" (FR-012 requires sequential, never reused)
- **Phase I simplicity**: No need for globally unique IDs in single-session app
- **Phase II extensibility**: Sequential IDs map naturally to database primary keys
- **Deterministic**: Same operations always produce same IDs (supports testing and reproducibility)

**Alternatives Considered**:
- **UUID**: More robust for distributed systems, but unnecessary for Phase I; violates simplicity principle
- **Random integers**: Non-deterministic; harder to test and debug
- **Decision**: Sequential integers from 1, never decremented or reused

**Implementation Pattern**:
- On app startup: next_id = 1
- When adding task: assign id = next_id; increment next_id
- When deleting task: do NOT recycle id (next_id stays the same or increases)
- On app exit: all IDs lost (data reset; expected behavior in Phase I)

---

### 4. Task Status Representation

**Question**: How should task status (complete/incomplete) be stored and displayed?

**Decision**: Store as string enum ("complete" | "incomplete"); display with symbols (✓ | ☐).

**Rationale**:
- **Enum clarity**: String values are self-documenting ("complete" is clearer than boolean True)
- **Future extensibility**: Phase II/III might add status values like "in-progress", "blocked", "archived"
- **Display symbols**: ✓ and ☐ are universally understood; human-readable and compact
- **Parsing**: When user enters "complete" command, it's immediately clear what's happening
- **Validation**: Easy to validate input (only allow "complete" or "incomplete")

**Alternatives Considered**:
- **Boolean**: True/False is ambiguous (true = complete? or true = incomplete?); less extensible
- **Integer codes**: 0/1 or 1/2/3; not readable without lookup table
- **Decision**: String enum with symbolic display

**Implementation Pattern**:
```python
class TaskStatus(Enum):
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"

class Task:
    def __init__(self, ...):
        self.status: TaskStatus = TaskStatus.INCOMPLETE

    def display_status(self) -> str:
        return "✓" if self.status == TaskStatus.COMPLETE else "☐"

# When listing:
print(f"{task.display_status()} {task.id}: {task.title}")
```

---

### 5. Input Parsing: Split vs Regex

**Question**: How should CLI commands be parsed from user input?

**Decision**: Use string split() with special handling for quoted strings; avoid regex.

**Rationale**:
- **Simplicity**: `input().split()` is straightforward and stdlib-only
- **Readability**: Easy to understand; no complex regex patterns
- **Spec commands are simple**: Only 7 commands with mostly single-word arguments
- **Quote handling**: For multi-word titles/descriptions, use quotes in input (e.g., `add "Buy milk" "2% fat"`); parse with shlex.split() from stdlib

**Alternatives Considered**:
- **Regular expressions**: Overkill for simple commands; harder to debug
- **Full argument parser (argparse)**: Adds complexity; Phase I doesn't need subcommands or flags
- **Manual character-by-character parsing**: Verbose and error-prone
- **Decision**: `shlex.split()` from stdlib (handles quotes correctly without regex complexity)

**Implementation Pattern**:
```python
import shlex

def parse_command(input_line: str) -> tuple[str, list[str]]:
    """Parse user input into command and arguments."""
    try:
        parts = shlex.split(input_line.strip())
        if not parts:
            return None, []
        command = parts[0].lower()
        args = parts[1:]
        return command, args
    except ValueError as e:
        # Mismatched quotes
        return None, []

# Usage:
command, args = parse_command(input_line)
if command == "add":
    # args[0] is title, args[1] (if present) is description
    add_task(args[0], args[1] if len(args) > 1 else None)
```

---

### 6. Error Handling: Exceptions vs Return Codes

**Question**: How should errors be communicated to the user (exceptions or return codes)?

**Decision**: Use exceptions internally; catch at CLI layer; format user-friendly messages.

**Rationale**:
- **Clean separation**: Service layer raises exceptions (InvalidTaskID, TaskNotFound, InvalidTitle)
- **CLI handles display**: Commands catch exceptions, format messages for user
- **No silent failures**: Exceptions force explicit error handling
- **Phase II compatibility**: Web API layer can convert exceptions to HTTP status codes

**Alternatives Considered**:
- **Return codes (0 for success, non-zero for error)**: Requires tuples (success, value) or similar; harder to distinguish error types
- **All-try/except at main loop**: Hides where errors originate; harder to debug
- **Decision**: Custom exceptions in service; catch and format at CLI

**Implementation Pattern**:
```python
# In services/todo_service.py
class TaskNotFound(Exception):
    pass

class InvalidTaskID(Exception):
    pass

def get_task(self, task_id: int) -> Task:
    if task_id not in self.tasks:
        raise TaskNotFound(f"Task ID {task_id} not found")
    return self.tasks[task_id]

# In cli/commands.py
def handle_delete(args, store):
    try:
        if len(args) != 1:
            print("Task ID is required. Usage: delete <id>")
            return
        task_id = int(args[0])
        store.delete_task(task_id)
        print(f"Task {task_id} deleted")
    except ValueError:
        print("Task ID must be numeric")
    except TaskNotFound as e:
        print(str(e))
```

---

### 7. Testing Strategy: Unit vs Integration

**Question**: What testing approach validates correctness while remaining simple?

**Decision**: Combination of unit tests (models, services, validation) and integration tests (CLI commands).

**Rationale**:
- **Unit tests**: Verify individual functions (add_task, validate_id, parse_command) work correctly
- **Integration tests**: Verify CLI commands execute end-to-end (input → service → output)
- **No mocking needed**: In-memory storage is fast; real objects can be used in tests
- **Python stdlib unittest**: Built-in module; no pytest dependency required (but pytest compatible)
- **Test discovery**: Standard directory structure (tests/) allows automatic test discovery

**Alternatives Considered**:
- **Integration tests only**: Slower feedback; harder to isolate bugs
- **Mocking everything**: Adds complexity; doesn't test real behavior
- **Manual testing only**: No automated verification; errors found late
- **Decision**: Unit + integration tests using stdlib unittest; pytest-compatible structure

**Implementation Pattern**:
```python
# tests/unit/test_todo_service.py
import unittest
from src.services.todo_service import TodoStore, TaskNotFound

class TestTodoStore(unittest.TestCase):
    def setUp(self):
        self.store = TodoStore()

    def test_add_task(self):
        task = self.store.add_task("Buy milk")
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Buy milk")
        self.assertEqual(task.status, "incomplete")

    def test_delete_task_raises_not_found(self):
        with self.assertRaises(TaskNotFound):
            self.store.delete_task(999)

# tests/integration/test_cli_commands.py
import unittest
from src.main import TodoApp

class TestCLICommands(unittest.TestCase):
    def setUp(self):
        self.app = TodoApp()

    def test_add_and_list_workflow(self):
        # Execute add command
        self.app.execute_command("add Buy milk")
        # Execute list command
        output = self.app.execute_command("list")
        self.assertIn("Buy milk", output)
```

---

### 8. Help Text & User Guidance

**Question**: How should help text be presented without external documentation?

**Decision**: Display welcome menu at startup; embed usage text in error messages.

**Rationale**:
- **Startup menu**: Shows all 7 commands with one-line descriptions; user sees options immediately
- **Error messages with usage**: When user enters invalid input, show usage for that command
- **No separate help file**: Everything needed is in the app itself
- **Discoverable**: User doesn't need to read external README to get started (Phase I focus)

**Alternatives Considered**:
- **External help file**: Violates "self-contained" principle; user must find and read it
- **`help` command**: Adds complexity; unnecessary if menu is shown at startup
- **Minimal output**: Users confused about available commands
- **Decision**: Welcome menu + contextual error messages

**Implementation Pattern**:
```python
def print_welcome_menu():
    print("""
Welcome to Todo App
Available commands:
  add <title> [description]       Add a new task
  list                            View all tasks
  update <id> [title] [--desc]    Update a task
  delete <id>                     Delete a task
  complete <id>                   Mark task as complete
  incomplete <id>                 Mark task as incomplete
  exit                            Exit the app
""")

def handle_add(args, store):
    if len(args) < 1:
        print("Title is required. Usage: add <title> [description]")
        return
    # ... rest of logic
```

---

## Summary: All Questions Resolved

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | CLI I/O approach | stdin/stdout with input()/print() | Simplicity; stdlib only |
| 2 | Data structure | Dict with ID keys | O(1) lookup; simple; extensible |
| 3 | ID generation | Sequential integers | User-friendly; deterministic; spec-compliant |
| 4 | Status representation | String enum with symbols | Clear; extensible; human-readable |
| 5 | Command parsing | shlex.split() | Simple; handles quotes; no regex |
| 6 | Error handling | Exceptions caught at CLI layer | Clean separation; user-friendly messages |
| 7 | Testing | Unit + Integration with unittest | Comprehensive coverage; fast feedback |
| 8 | Help text | Welcome menu + contextual errors | Self-contained; discoverable; no external docs |

All technical decisions support the five core principles (Correctness, Simplicity, Determinism, Spec-Driven, Incremental Design) and Constitution constraints (Python 3.13+, stdlib only, in-memory, single-process, synchronous).

**Phase 0 Status**: ✅ COMPLETE — Ready for Phase 1 design (data model, contracts, quickstart).

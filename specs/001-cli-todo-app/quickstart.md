# Quickstart: Phase I - In-Memory Python Console Todo App

**Date**: 2026-01-05
**Feature**: Phase I - In-Memory Python Console Todo App
**Status**: Development Setup Guide

---

## Project Setup

### Prerequisites

- **Python 3.13+** (check with `python --version`)
- **UV** (Python package manager; install from https://docs.astral.sh/uv/)
- **Git** (for version control; already initialized in this repo)

### Clone & Navigate

```bash
cd /path/to/Hackathon-2-Phase-I
```

The project structure is already initialized. Files to be created during implementation:

```
src/
├── __init__.py
├── main.py                     # Entry point (TODO: implement in Phase 4)
├── models/
│   ├── __init__.py
│   └── task.py                 # Task entity (TODO: implement in Phase 1)
├── services/
│   ├── __init__.py
│   └── todo_service.py         # TodoStore class (TODO: implement in Phase 1)
├── cli/
│   ├── __init__.py
│   └── commands.py             # Command handlers (TODO: implement in Phase 3)
└── lib/
    ├── __init__.py
    └── validation.py           # Validation helpers (TODO: implement in Phase 2)

tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_task_model.py      # (TODO: implement in Phase 1)
│   ├── test_todo_service.py    # (TODO: implement in Phase 1)
│   └── test_validation.py      # (TODO: implement in Phase 2)
├── integration/
│   ├── __init__.py
│   └── test_cli_commands.py    # (TODO: implement in Phase 3)
└── contract/
    ├── __init__.py
    └── test_cli_contracts.py   # (TODO: implement in Phase 3)
```

---

## Development Workflow

### 1. Phase 1: Domain Model (Task Entity & TodoStore)

**Objectives**:
- Implement Task class with id, title, description, status, created_at
- Implement TodoStore class with tasks dict and next_id
- Implement CRUD methods: add_task, get_task, list_tasks, update_task, delete_task, complete_task, incomplete_task
- Write unit tests for Task and TodoStore

**File**: `src/models/task.py`

```python
# Pseudocode (TODO: implement)
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"

class Task:
    def __init__(self, id: int, title: str, description: str = None):
        self.id = id
        self.title = title
        self.description = description or ""
        self.status = TaskStatus.INCOMPLETE
        self.created_at = datetime.now()

    def mark_complete(self):
        self.status = TaskStatus.COMPLETE

    def mark_incomplete(self):
        self.status = TaskStatus.INCOMPLETE
```

**File**: `src/services/todo_service.py`

```python
# Pseudocode (TODO: implement)
class TaskNotFound(Exception):
    pass

class TodoStore:
    def __init__(self):
        self.tasks = {}
        self.next_id = 1

    def add_task(self, title: str, description: str = None) -> Task:
        # Validate, create, store, increment next_id
        pass

    def get_task(self, task_id: int) -> Task:
        # Return tasks[task_id] or None
        pass

    def list_tasks(self) -> list:
        # Return list(tasks.values())
        pass

    def update_task(self, task_id: int, title: str = None, description: str = None) -> Task:
        # Validate, update, return
        pass

    def delete_task(self, task_id: int) -> None:
        # Remove from dict; do NOT decrement next_id
        pass

    def complete_task(self, task_id: int) -> Task:
        # Mark task.status = COMPLETE
        pass

    def incomplete_task(self, task_id: int) -> Task:
        # Mark task.status = INCOMPLETE
        pass
```

**Test File**: `tests/unit/test_todo_service.py`

```python
# Pseudocode (TODO: implement)
import unittest
from src.services.todo_service import TodoStore, TaskNotFound

class TestTodoStore(unittest.TestCase):
    def setUp(self):
        self.store = TodoStore()

    def test_add_task_assigns_id(self):
        task = self.store.add_task("Buy milk")
        self.assertEqual(task.id, 1)

    def test_add_task_increments_id(self):
        task1 = self.store.add_task("Buy milk")
        task2 = self.store.add_task("Buy eggs")
        self.assertEqual(task2.id, 2)

    def test_delete_task_does_not_reuse_id(self):
        self.store.add_task("Task 1")
        self.store.add_task("Task 2")
        self.store.delete_task(1)
        task3 = self.store.add_task("Task 3")
        self.assertEqual(task3.id, 3)  # Not 1

    def test_complete_task_marks_status(self):
        task = self.store.add_task("Buy milk")
        self.store.complete_task(task.id)
        updated = self.store.get_task(task.id)
        self.assertEqual(updated.status, "complete")

    def test_delete_task_not_found(self):
        with self.assertRaises(TaskNotFound):
            self.store.delete_task(999)
```

**Run Tests**:

```bash
python -m pytest tests/unit/test_todo_service.py -v
# or
python -m unittest tests.unit.test_todo_service
```

---

### 2. Phase 2: Validation Helpers

**Objectives**:
- Implement parse_id, parse_title, parse_description, parse_command functions
- Validate input according to constraints (max lengths, numeric IDs, etc.)
- Write unit tests

**File**: `src/lib/validation.py`

```python
# Pseudocode (TODO: implement)
import shlex

def parse_command(input_line: str) -> tuple:
    """Parse user input into command and arguments."""
    try:
        parts = shlex.split(input_line.strip())
        if not parts:
            return None, []
        command = parts[0].lower()
        args = parts[1:]
        return command, args
    except ValueError:
        return None, []

def validate_task_id(value: str) -> int:
    """Convert string to int; raise ValueError if invalid."""
    try:
        task_id = int(value)
        if task_id <= 0:
            raise ValueError("Task ID must be positive")
        return task_id
    except ValueError as e:
        raise ValueError(f"Task ID must be numeric: {e}")

def validate_title(value: str) -> str:
    """Validate task title."""
    value = value.strip() if value else ""
    if not value:
        raise ValueError("Title cannot be empty")
    if len(value) > 100:
        raise ValueError("Title exceeds 100 characters")
    return value

def validate_description(value: str) -> str:
    """Validate task description."""
    value = value.strip() if value else ""
    if len(value) > 500:
        raise ValueError("Description exceeds 500 characters")
    return value
```

**Test File**: `tests/unit/test_validation.py`

```python
# Pseudocode (TODO: implement)
import unittest
from src.lib.validation import validate_title, validate_task_id

class TestValidation(unittest.TestCase):
    def test_validate_title_empty(self):
        with self.assertRaises(ValueError):
            validate_title("")

    def test_validate_title_whitespace_only(self):
        with self.assertRaises(ValueError):
            validate_title("   ")

    def test_validate_title_max_length(self):
        with self.assertRaises(ValueError):
            validate_title("x" * 101)

    def test_validate_task_id_non_numeric(self):
        with self.assertRaises(ValueError):
            validate_task_id("abc")

    def test_validate_task_id_valid(self):
        result = validate_task_id("5")
        self.assertEqual(result, 5)
```

---

### 3. Phase 3: Command Handlers

**Objectives**:
- Implement command handler functions (handle_add, handle_list, handle_update, etc.)
- Parse CLI arguments; call service methods; format output
- Write integration tests for CLI commands

**File**: `src/cli/commands.py`

```python
# Pseudocode (TODO: implement)
from src.services.todo_service import TodoStore, TaskNotFound
from src.lib.validation import validate_task_id, validate_title

def handle_add(args, store):
    """Handle: add <title> [description]"""
    try:
        if len(args) < 1:
            print("Title is required. Usage: add <title> [description]")
            return
        title = validate_title(args[0])
        description = validate_description(args[1]) if len(args) > 1 else None
        task = store.add_task(title, description)
        print(f"Task added with ID: {task.id}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def handle_list(args, store):
    """Handle: list"""
    try:
        tasks = store.list_tasks()
        if not tasks:
            print("No tasks yet. Add one with: add <title> [description]")
        else:
            print(f"ID │ Status │ Title")
            print(f"───┼────────┼──────────────────────────")
            for task in tasks:
                status = "✓" if task.status == "complete" else "☐"
                print(f" {task.id} │   {status}    │ {task.title}")
    except Exception as e:
        print(f"Error: {e}")

def handle_delete(args, store):
    """Handle: delete <id>"""
    try:
        if len(args) != 1:
            print("Task ID is required. Usage: delete <id>")
            return
        task_id = validate_task_id(args[0])
        store.delete_task(task_id)
        print(f"Task {task_id} deleted")
    except ValueError as e:
        print(f"Error: {e}")
    except TaskNotFound as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# ... handle_update, handle_complete, handle_incomplete, etc.
```

**Test File**: `tests/integration/test_cli_commands.py`

```python
# Pseudocode (TODO: implement)
import unittest
from src.services.todo_service import TodoStore
from src.cli.commands import handle_add, handle_list, handle_delete

class TestCLICommands(unittest.TestCase):
    def setUp(self):
        self.store = TodoStore()

    def test_add_command_creates_task(self):
        # Call handle_add with mock output (capture print)
        # Verify task created in store
        pass

    def test_list_command_displays_tasks(self):
        # Add tasks
        # Call handle_list
        # Verify output contains task titles and IDs
        pass

    def test_delete_command_removes_task(self):
        # Add task
        # Call handle_delete
        # Verify task removed from store
        pass
```

---

### 4. Phase 4: Main Application Loop

**Objectives**:
- Implement main.py with welcome menu and command loop
- Route commands to handlers
- Handle exit gracefully

**File**: `src/main.py`

```python
# Pseudocode (TODO: implement)
from src.services.todo_service import TodoStore
from src.cli.commands import (
    handle_add, handle_list, handle_update,
    handle_delete, handle_complete, handle_incomplete
)
from src.lib.validation import parse_command

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

def main():
    store = TodoStore()
    print_welcome_menu()

    while True:
        try:
            user_input = input("todo> ").strip()
            if not user_input:
                continue

            command, args = parse_command(user_input)
            if command is None:
                print("Invalid input. Please try again.")
                continue

            if command == "add":
                handle_add(args, store)
            elif command == "list":
                handle_list(args, store)
            elif command == "update":
                handle_update(args, store)
            elif command == "delete":
                handle_delete(args, store)
            elif command == "complete":
                handle_complete(args, store)
            elif command == "incomplete":
                handle_incomplete(args, store)
            elif command == "exit":
                print("Goodbye!")
                break
            else:
                print(f"Unknown command '{command}'. Available: add, list, update, delete, complete, incomplete, exit")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
```

**Run the App**:

```bash
python src/main.py
```

---

## Testing All Phases

### Run All Tests

```bash
python -m pytest tests/ -v
# or
python -m unittest discover -s tests -p "test_*.py"
```

### Run Specific Test Suite

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Contract tests
python -m pytest tests/contract/ -v
```

---

## Manual Verification Checklist

After implementation, run through these steps:

- [ ] Start app: `python src/main.py` → See welcome menu
- [ ] Add task: `add "Buy milk"` → Confirm "Task added with ID: 1"
- [ ] List tasks: `list` → See task with ID 1, status ☐
- [ ] Add more: `add "Buy eggs"` and `add "Buy bread"` → IDs increment to 2, 3
- [ ] Update: `update 2 "Buy free-range eggs"` → Confirm updated
- [ ] List again: `list` → See updated title for task 2
- [ ] Complete: `complete 1` → Confirm "Task 1 marked complete (✓)"
- [ ] List shows status: Task 1 now shows ✓, others show ☐
- [ ] Incomplete: `incomplete 1` → Confirm reverted to ☐
- [ ] Delete: `delete 3` → Confirm "Task 3 deleted"
- [ ] List after delete: Task 3 gone; IDs 1, 2, 4 remain
- [ ] Error: `delete 999` → See "Task ID 999 not found"
- [ ] Invalid command: `foo` → See helpful error message
- [ ] Exit: `exit` → App terminates; "Goodbye!" message
- [ ] Restart app: `python src/main.py` → No tasks (confirming in-memory only)

---

## Performance Validation

All operations should complete in <100ms (specification requirement SC-001):

```bash
# Add 100 tasks and measure time
time python -c "
from src.main import *
store = TodoStore()
for i in range(100):
    store.add_task(f'Task {i}')
print(f'Created {len(store.tasks)} tasks')
"
# Expected: <100ms total
```

---

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'src'`:

Make sure you're running from the project root:
```bash
cd /path/to/Hackathon-2-Phase-I
python src/main.py  # Correct
```

NOT:
```bash
cd src
python main.py      # Wrong; breaks imports
```

### Python Version

Verify Python 3.13+:
```bash
python --version
# Should show: Python 3.13.X or later
```

---

## Next Steps

Once Phase I is complete and all tests pass:

1. **Review & Sign Off**: Get approval that implementation matches spec
2. **Commit to Feature Branch**: `git commit -m "feat: implement Phase I CLI todo app"`
3. **Create Pull Request**: `git push origin 001-cli-todo-app && gh pr create`
4. **Plan Phase II**: Extend with FastAPI backend and persistent database
5. **Plan Phase III**: Add AI chatbot interface
6. **Plan Phase IV**: Containerize with Docker and Kubernetes
7. **Plan Phase V**: Deploy to cloud with event-driven architecture

---

## Reference

- **Specification**: `specs/001-cli-todo-app/spec.md`
- **Implementation Plan**: `specs/001-cli-todo-app/plan.md`
- **Data Model**: `specs/001-cli-todo-app/data-model.md`
- **Constitution**: `.specify/memory/constitution.md`
- **Research**: `specs/001-cli-todo-app/research.md`

# Contract: Add Task Command

**Command**: `add <title> [description]`
**Priority**: P1 (MVP)
**Related Spec**: FR-001, FR-002, US1

## Purpose

Allow users to quickly capture a new task idea with a title and optional description. System assigns a unique ID and confirms creation.

## Input Format

```
add <title> [description]
```

| Part | Type | Required | Constraints | Example |
|------|------|----------|-------------|---------|
| `<title>` | string | Yes | 1–100 characters, no leading/trailing whitespace | "Buy milk" |
| `[description]` | string | No | 0–500 characters, no leading/trailing whitespace | "2% fat" |

## Input Parsing

- Split user input by whitespace (using shlex.split for quote handling)
- Command: first token lowercased
- Title: second token
- Description: third token (if present; may contain spaces if quoted)

### Examples

```
add "Buy milk"                              → title="Buy milk", description=None
add "Buy milk" "2% fat"                     → title="Buy milk", description="2% fat"
add "Buy organic milk from whole foods"     → title="Buy organic milk from whole foods" (quotes allow spaces)
add                                         → ERROR (missing title)
```

## Processing

1. Parse input into command and arguments
2. Validate title (non-empty, max 100 chars, trim whitespace)
3. Validate description (max 500 chars, trim whitespace) if provided
4. Call service.add_task(title, description)
5. Assign auto-incremented ID (1, 2, 3, ...)
6. Set status = "incomplete"
7. Set created_at = current timestamp
8. Store in memory

## Output Format: Success

```
Task added with ID: {id}
```

Example:
```
Task added with ID: 1
```

## Output Format: Error

### Missing Title
```
Title is required. Usage: add <title> [description]
```

### Title Too Long
```
Title exceeds 100 characters
```

### Description Too Long
```
Description exceeds 500 characters
```

## Return to Main Loop

After success or error, return to main menu prompt:
```
todo>
```

## Acceptance Criteria (from Spec)

- ✅ System confirms "Task added with ID: {id}"
- ✅ Task is stored in memory with status "incomplete"
- ✅ Task ID is auto-incremented
- ✅ Description is optional
- ✅ Invalid input (missing title) shows helpful error with usage

## Example Interaction

```
todo> add "Buy groceries" "Milk, eggs, bread"
Task added with ID: 1

todo> add "Review PR"
Task added with ID: 2

todo> add
Title is required. Usage: add <title> [description]

todo>
```

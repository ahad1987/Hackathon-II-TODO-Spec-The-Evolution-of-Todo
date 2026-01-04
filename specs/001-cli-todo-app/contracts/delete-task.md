# Contract: Delete Task Command

**Command**: `delete <id>`
**Priority**: P2
**Related Spec**: FR-005, US4

## Purpose

Allow users to remove a task from their todo list permanently.

## Input Format

```
delete <id>
```

| Part | Type | Required | Constraints | Example |
|------|------|----------|-------------|---------|
| `<id>` | integer | Yes | Numeric, must exist | 2 |

## Processing

1. Parse input into id
2. Validate id (numeric, exists)
3. Call service.delete_task(id)
4. Remove task entirely from storage
5. Do NOT decrement next_id (IDs continue sequentially, never reused)

## Output Format: Success

```
Task {id} deleted
```

Example:
```
Task 2 deleted
```

## Output Format: Error

### Task ID Not Found
```
Task ID {id} not found
```

### Task ID Not Provided
```
Task ID is required. Usage: delete <id>
```

### Task ID Not Numeric
```
Task ID must be numeric
```

## Return to Main Loop

After success or error, return to main menu prompt:
```
todo>
```

## Acceptance Criteria (from Spec)

- ✅ Task removed from list by ID
- ✅ Helpful error if ID not found
- ✅ Helpful error if ID missing
- ✅ IDs not reused (sequential assignment continues)

## Example Interaction

```
todo> add "Task 1"
Task added with ID: 1

todo> add "Task 2"
Task added with ID: 2

todo> add "Task 3"
Task added with ID: 3

todo> delete 2
Task 2 deleted

todo> list
ID │ Status │ Title
───┼────────┼────────────
 1 │   ☐    │ Task 1
 3 │   ☐    │ Task 3

todo> add "Task 4"
Task added with ID: 4

todo> list
ID │ Status │ Title
───┼────────┼────────────
 1 │   ☐    │ Task 1
 3 │   ☐    │ Task 3
 4 │   ☐    │ Task 4

todo> delete 999
Task ID 999 not found

todo> delete
Task ID is required. Usage: delete <id>

todo>
```

## Edge Cases

- Deleting non-existent ID: Show error
- Deleting already deleted ID: Show "not found" error
- New task after deletion: Gets next sequential ID (not reusing deleted ID)

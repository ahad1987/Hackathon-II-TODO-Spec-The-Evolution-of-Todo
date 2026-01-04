# Contract: Mark Task Complete Command

**Command**: `complete <id>`
**Priority**: P2
**Related Spec**: FR-006, US5

## Purpose

Allow users to mark a task as completed and show visual progress with a ✓ indicator.

## Input Format

```
complete <id>
```

| Part | Type | Required | Constraints | Example |
|------|------|----------|-------------|---------|
| `<id>` | integer | Yes | Numeric, must exist | 1 |

## Processing

1. Parse input into id
2. Validate id (numeric, exists)
3. Call service.complete_task(id)
4. Set task.status = "complete"
5. Keep id, title, description, created_at unchanged

## Output Format: Success

```
Task {id} marked complete (✓)
```

Example:
```
Task 1 marked complete (✓)
```

## Output Format: Error

### Task ID Not Found
```
Task ID {id} not found
```

### Task ID Not Provided
```
Task ID is required. Usage: complete <id>
```

### Task ID Not Numeric
```
Task ID must be numeric
```

## Visual Indicator in List

When listing tasks, completed tasks show ✓:

```
ID │ Status │ Title
───┼────────┼────────────
 1 │   ✓    │ Task 1  (completed)
 2 │   ☐    │ Task 2  (incomplete)
```

## Return to Main Loop

After success or error, return to main menu prompt:
```
todo>
```

## Acceptance Criteria (from Spec)

- ✅ Task status changes to "complete"
- ✅ Visual indicator ✓ shown in list view
- ✅ Confirmation message includes (✓) symbol
- ✅ Error if task ID not found
- ✅ Error if task ID missing

## Example Interaction

```
todo> add "Buy milk"
Task added with ID: 1

todo> add "Review PR"
Task added with ID: 2

todo> list
ID │ Status │ Title
───┼────────┼────────────
 1 │   ☐    │ Buy milk
 2 │   ☐    │ Review PR

todo> complete 1
Task 1 marked complete (✓)

todo> list
ID │ Status │ Title
───┼────────┼────────────
 1 │   ✓    │ Buy milk
 2 │   ☐    │ Review PR

todo> complete 999
Task ID 999 not found

todo> complete
Task ID is required. Usage: complete <id>

todo>
```

## Related Commands

- `incomplete <id>`: Revert completed task back to incomplete
- `list`: Shows completed tasks with ✓ indicator

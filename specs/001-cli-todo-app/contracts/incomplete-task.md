# Contract: Mark Task Incomplete Command

**Command**: `incomplete <id>`
**Priority**: P2
**Related Spec**: FR-007, US5

## Purpose

Allow users to revert a completed task back to incomplete status, removing the ✓ indicator.

## Input Format

```
incomplete <id>
```

| Part | Type | Required | Constraints | Example |
|------|------|----------|-------------|---------|
| `<id>` | integer | Yes | Numeric, must exist | 1 |

## Processing

1. Parse input into id
2. Validate id (numeric, exists)
3. Call service.incomplete_task(id)
4. Set task.status = "incomplete"
5. Keep id, title, description, created_at unchanged

## Output Format: Success

```
Task {id} marked incomplete (☐)
```

Example:
```
Task 1 marked incomplete (☐)
```

## Output Format: Error

### Task ID Not Found
```
Task ID {id} not found
```

### Task ID Not Provided
```
Task ID is required. Usage: incomplete <id>
```

### Task ID Not Numeric
```
Task ID must be numeric
```

## Visual Indicator in List

When listing tasks, incomplete tasks show ☐:

```
ID │ Status │ Title
───┼────────┼────────────
 1 │   ☐    │ Task 1  (reverted to incomplete)
 2 │   ✓    │ Task 2  (still complete)
```

## Return to Main Loop

After success or error, return to main menu prompt:
```
todo>
```

## Acceptance Criteria (from Spec)

- ✅ Task status reverts to "incomplete"
- ✅ Visual indicator ☐ shown in list view
- ✅ Confirmation message includes (☐) symbol
- ✅ Error if task ID not found
- ✅ Error if task ID missing

## Example Interaction

```
todo> add "Buy milk"
Task added with ID: 1

todo> complete 1
Task 1 marked complete (✓)

todo> list
ID │ Status │ Title
───┼────────┼────────────
 1 │   ✓    │ Buy milk

todo> incomplete 1
Task 1 marked incomplete (☐)

todo> list
ID │ Status │ Title
───┼────────┼────────────
 1 │   ☐    │ Buy milk

todo> incomplete 999
Task ID 999 not found

todo> incomplete
Task ID is required. Usage: incomplete <id>

todo>
```

## Related Commands

- `complete <id>`: Mark task as complete with ✓ indicator
- `list`: Shows incomplete tasks with ☐ indicator

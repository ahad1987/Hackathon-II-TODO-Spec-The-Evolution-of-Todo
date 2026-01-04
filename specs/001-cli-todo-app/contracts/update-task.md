# Contract: Update Task Command

**Command**: `update <id> [title] [--desc description]`
**Priority**: P2
**Related Spec**: FR-004, US3

## Purpose

Allow users to modify an existing task's title and/or description.

## Input Format

```
update <id> [title] [--desc description]
```

| Part | Type | Required | Constraints | Example |
|------|------|----------|-------------|---------|
| `<id>` | integer | Yes | Numeric, must exist | 1 |
| `[title]` | string | No | 1–100 characters (if provided) | "Buy organic milk" |
| `[--desc description]` | string | No | 0–500 characters; requires --desc flag | --desc "2% fat" |

## Input Parsing

- Command: first token = "update"
- ID: second token (numeric)
- Title: third token (if not starting with "--")
- Description: after "--desc" flag

### Examples

```
update 1 "Buy organic milk"                           → id=1, title="Buy organic milk", description=None
update 1 --desc "Very urgent"                         → id=1, title=None, description="Very urgent"
update 1 "Buy organic milk" --desc "2% fat"           → id=1, title="Buy organic milk", description="2% fat"
update 1                                              → ERROR (no title or --desc)
update                                                → ERROR (missing id)
update abc "Title"                                    → ERROR (id not numeric)
```

## Processing

1. Parse input into id, title, description
2. Validate id (numeric, exists)
3. Validate at least one of title or description provided
4. Validate title (max 100 chars, trim) if provided
5. Validate description (max 500 chars, trim) if provided
6. Call service.update_task(id, title, description)
7. Keep id, status, created_at unchanged

## Output Format: Success

```
Task {id} updated
```

Example:
```
Task 1 updated
```

## Output Format: Error

### Task ID Not Found
```
Task ID {id} not found
```

### Task ID Not Numeric
```
Task ID must be numeric
```

### Missing Both Title and Description
```
Provide new title or --desc <description>. Usage: update <id> [title] [--desc description]
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

- ✅ Title can be updated with new value
- ✅ Description can be added or modified with --desc flag
- ✅ Both can be updated in one command
- ✅ Error if task ID not found
- ✅ Error if neither title nor description provided

## Example Interaction

```
todo> add "Buy groceries" "Milk, eggs"
Task added with ID: 1

todo> update 1 "Buy organic groceries"
Task 1 updated

todo> update 1 --desc "2% milk, free-range eggs, whole wheat bread"
Task 1 updated

todo> list
ID │ Status │ Title                  │ Description
───┼────────┼────────────────────────┼─────────────────────────────
 1 │   ☐    │ Buy organic groceries  │ 2% milk, free-range eggs...

todo> update 999 "Title"
Task ID 999 not found

todo> update 1
Provide new title or --desc <description>. Usage: update <id> [title] [--desc description]

todo>
```

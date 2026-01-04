# Contract: List Tasks Command

**Command**: `list`
**Priority**: P1 (MVP)
**Related Spec**: FR-003, US2

## Purpose

Display all tasks with ID, title, description, and status indicator. Users see complete list of their todos at a glance.

## Input Format

```
list
```

No arguments required.

## Processing

1. Call service.list_tasks()
2. For each task, format with ID, status indicator (✓/☐), title, and description

## Output Format: Tasks Exist

```
ID │ Status │ Title                    │ Description
───┼────────┼──────────────────────────┼─────────────────────
 1 │   ☐    │ Buy groceries            │ Milk, eggs, bread
 2 │   ✓    │ Review PR                │
 3 │   ☐    │ Fix bug in login         │ Check email flow
```

**Status Indicator**:
- ☐ = "incomplete"
- ✓ = "complete"

**Formatting Rules**:
- Left-align ID with padding
- Left-align status symbol
- Wrap long titles/descriptions or truncate with indication
- Show description if present; omit if empty

## Output Format: No Tasks

```
No tasks yet. Add one with: add <title> [description]
```

## Return to Main Loop

After display, return to main menu prompt:
```
todo>
```

## Acceptance Criteria (from Spec)

- ✅ All tasks displayed with ID, title, status (✓/☐), description
- ✅ Empty case shows helpful message with usage
- ✅ Multi-line descriptions formatted readably
- ✅ All tasks displayed without pagination

## Example Interaction

```
todo> add "Buy groceries" "Milk, eggs, bread"
Task added with ID: 1

todo> add "Review PR"
Task added with ID: 2

todo> complete 2
Task 2 marked complete (✓)

todo> list
ID │ Status │ Title           │ Description
───┼────────┼─────────────────┼──────────────────────
 1 │   ☐    │ Buy groceries   │ Milk, eggs, bread
 2 │   ✓    │ Review PR       │

todo>
```

## Edge Cases

- **Empty list**: Show helpful message
- **No description**: Show blank after pipe
- **Long title**: Wrap or truncate with ellipsis (…)
- **Long description**: Wrap or truncate with ellipsis (…)

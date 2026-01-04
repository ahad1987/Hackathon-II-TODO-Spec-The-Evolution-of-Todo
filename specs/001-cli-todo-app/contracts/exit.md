# Contract: Exit Command

**Command**: `exit`
**Priority**: P1
**Related Spec**: FR-008

## Purpose

Allow users to cleanly exit the todo application. Data is lost (in-memory only; expected behavior).

## Input Format

```
exit
```

No arguments required.

## Processing

1. Parse input as "exit" command
2. Break main loop
3. Close application
4. All in-memory data is discarded (expected; Phase I specification)

## Output Format: Success

```
Goodbye!
```

Then exit the application.

## Return to Main Loop

Command does NOT return to main loop; application terminates.

## Acceptance Criteria (from Spec)

- ✅ Application terminates cleanly on `exit` command
- ✅ Goodbye message displayed
- ✅ No data saved (in-memory only; confirming expected behavior)
- ✅ Process exits with status 0 (success)

## Example Interaction

```
todo> add "Buy milk"
Task added with ID: 1

todo> list
ID │ Status │ Title
───┼────────┼────────────
 1 │   ☐    │ Buy milk

todo> exit
Goodbye!

$ (back to shell prompt)

$ python src/main.py

Welcome to Todo App
Available commands:
  add <title> [description]       Add a new task
  list                            View all tasks
  update <id> [title] [--desc]    Update a task
  delete <id>                     Delete a task
  complete <id>                   Mark task as complete
  incomplete <id>                 Mark task as incomplete
  exit                            Exit the app

todo> list
No tasks yet. Add one with: add <title> [description]

todo>
```

## Notes

- Data reset on restart confirms in-memory only behavior (as specified)
- Phase II will add persistence; exit command will no longer lose data

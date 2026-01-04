---
description: "Task list for Phase I in-memory Python console todo application"
---

# Tasks: Phase I - In-Memory Python Console Todo App

**Input**: Design documents from `/specs/001-cli-todo-app/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md (required), contracts/ (required)

**Tests**: No automated tests requested in specification; manual verification steps included at end of each user story phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions
- Checkbox: `- [ ]` for incomplete tasks

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below reflect Phase I structure

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Project structure and shared infrastructure

- [ ] T001 Create directory structure: `src/`, `src/models/`, `src/services/`, `src/cli/`, `src/lib/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [ ] T002 Create `__init__.py` files in all Python packages: `src/__init__.py`, `src/models/__init__.py`, `src/services/__init__.py`, `src/cli/__init__.py`, `src/lib/__init__.py`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`, `tests/contract/__init__.py`
- [ ] T003 Create `src/main.py` with function stubs: `main()`, `print_welcome_menu()`, command routing logic
- [ ] T004 [P] Create skeleton files with docstrings: `src/models/task.py`, `src/services/todo_service.py`, `src/cli/commands.py`, `src/lib/validation.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Foundational components that all user stories depend on:

- [ ] T005 Implement Task entity in `src/models/task.py`: Class with `id`, `title`, `description`, `status`, `created_at` attributes; TaskStatus enum with "incomplete" and "complete" values; methods: `__init__()`, `mark_complete()`, `mark_incomplete()`
- [ ] T006 Implement TodoStore class in `src/services/todo_service.py`: Initialize `tasks` dict and `next_id` counter; exception classes: `TaskNotFound`, `InvalidTaskID`
- [ ] T007 [P] Implement TodoStore CRUD core methods in `src/services/todo_service.py`: `add_task(title, description)`, `get_task(task_id)`, `list_tasks()`, `update_task(task_id, title, description)`, `delete_task(task_id)`, `complete_task(task_id)`, `incomplete_task(task_id)`
- [ ] T008 [P] Implement validation helpers in `src/lib/validation.py`: `parse_command(input_line)`, `validate_task_id(value)`, `validate_title(value)`, `validate_description(value)`
- [ ] T009 Implement main loop stub in `src/main.py`: `print_welcome_menu()`, main `while True` loop with input/output, basic command routing (no handlers yet)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Add a New Todo Task (Priority: P1) 🎯 MVP

**Goal**: Users can create tasks with title and optional description; system assigns unique sequential IDs

**Independent Test**: Run app → `add "Buy milk"` → See "Task added with ID: 1" → Run `list` → See task with ID 1, status ☐ → Exit app → Restart → Confirm task is gone (in-memory only)

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement `handle_add()` in `src/cli/commands.py`: Parse args; validate title and description; call `store.add_task()`; print confirmation; handle errors with helpful messages
- [ ] T011 [US1] Integrate `handle_add()` into main loop in `src/main.py`: Route `add` command to `handle_add(args, store)`
- [ ] T012 [US1] Test User Story 1 manually: Start app → Add task with title only → Add task with title and description → Verify IDs increment (1, 2, 3, ...) → Verify confirmation messages → Verify error for missing title → Verify data resets on exit

**Checkpoint**: User Story 1 fully functional and independently testable

---

## Phase 4: User Story 2 - View All Tasks (Priority: P1) 🎯 MVP

**Goal**: Users can see all tasks with ID, title, description, and status indicator (✓ for complete, ☐ for incomplete)

**Independent Test**: Add 3 tasks → `list` → See all 3 with IDs, titles, status indicators → Mark one complete → `list` → See updated status with ✓ → Delete one → `list` → See only 2 remaining

### Implementation for User Story 2

- [ ] T013 [P] [US2] Implement `handle_list()` in `src/cli/commands.py`: Call `store.list_tasks()`; format output with table (ID, Status, Title, Description); handle empty case with helpful message
- [ ] T014 [US2] Implement task display formatting: Status symbols (☐ for incomplete, ✓ for complete); readable table layout with headers; handle multi-line descriptions
- [ ] T015 [US2] Integrate `handle_list()` into main loop in `src/main.py`: Route `list` command to `handle_list(args, store)`
- [ ] T016 [US2] Test User Story 2 manually: Add 3 tasks with varied descriptions → `list` → Verify all tasks displayed with correct IDs, titles, descriptions, status → `list` with empty list → Verify "No tasks yet" message → Verify formatting is readable

**Checkpoint**: User Stories 1 AND 2 fully functional; can add and view tasks

---

## Phase 5: User Story 3 - Update an Existing Task (Priority: P2)

**Goal**: Users can modify task title and/or description by ID

**Independent Test**: Create task with ID 1 → `update 1 "New title"` → Verify updated → `update 1 --desc "New description"` → Verify updated → `list` → See updated task → Error handling: `update 999 "Title"` → See "Task ID 999 not found"

### Implementation for User Story 3

- [ ] T017 [P] [US3] Implement `handle_update()` in `src/cli/commands.py`: Parse args (id, title, --desc description); validate at least one field provided; call `store.update_task()`; print confirmation; handle errors (ID not found, missing fields)
- [ ] T018 [US3] Integrate `handle_update()` into main loop in `src/main.py`: Route `update` command to `handle_update(args, store)`
- [ ] T019 [US3] Test User Story 3 manually: Create task → Update title only → Verify updated → Update description only → Verify updated → Update both → Verify both updated → Error: update with no fields → See error message → Error: update nonexistent ID → See "not found" message

**Checkpoint**: User Stories 1, 2, AND 3 fully functional

---

## Phase 6: User Story 4 - Delete a Task (Priority: P2)

**Goal**: Users can remove tasks by ID; deleted IDs are never reused

**Independent Test**: Create tasks 1, 2, 3 → `delete 2` → `list` → See tasks 1, 3 only → Add new task → Verify it gets ID 4 (not 2) → Error: `delete 999` → See "Task ID 999 not found"

### Implementation for User Story 4

- [ ] T020 [P] [US4] Implement `handle_delete()` in `src/cli/commands.py`: Parse args (id); validate ID exists; call `store.delete_task()`; print confirmation; handle errors (ID not found, missing ID)
- [ ] T021 [US4] Integrate `handle_delete()` into main loop in `src/main.py`: Route `delete` command to `handle_delete(args, store)`
- [ ] T022 [US4] Test User Story 4 manually: Create tasks 1, 2, 3 → Delete task 2 → `list` → Verify only 1, 3 remain → Add new task → Verify it gets ID 4 → Error: delete nonexistent ID → See error message → Error: delete without ID → See usage message

**Checkpoint**: User Stories 1, 2, 3, AND 4 fully functional (CRUD complete)

---

## Phase 7: User Story 5 - Mark a Task as Complete/Incomplete (Priority: P2)

**Goal**: Users can toggle task status between complete (✓) and incomplete (☐)

**Independent Test**: Create task → `complete 1` → See "Task 1 marked complete (✓)" → `list` → See ✓ indicator → `incomplete 1` → See "Task 1 marked incomplete (☐)" → `list` → See ☐ indicator → Error: `complete 999` → See "Task ID 999 not found"

### Implementation for User Story 5

- [ ] T023 [P] [US5] Implement `handle_complete()` in `src/cli/commands.py`: Parse args (id); validate ID exists; call `store.complete_task()`; print confirmation with (✓); handle errors
- [ ] T024 [P] [US5] Implement `handle_incomplete()` in `src/cli/commands.py`: Parse args (id); validate ID exists; call `store.incomplete_task()`; print confirmation with (☐); handle errors
- [ ] T025 [US5] Integrate `handle_complete()` and `handle_incomplete()` into main loop in `src/main.py`: Route `complete` and `incomplete` commands
- [ ] T026 [US5] Test User Story 5 manually: Create task → Complete it → Verify status changes to ✓ in list → Incomplete it → Verify status changes back to ☐ → Mark multiple tasks complete/incomplete → Verify all status changes → Error: complete nonexistent ID → See error message

**Checkpoint**: All user stories (1-5) fully functional; app supports all 5 core features (Add, List, Update, Delete, Complete/Incomplete)

---

## Phase 8: Exit Command & Main Loop Completion

**Purpose**: Complete CLI experience with exit command and help menu

- [ ] T027 [P] Implement `handle_exit()` in `src/cli/commands.py`: Break main loop; print "Goodbye!"; exit cleanly
- [ ] T028 Finalize main loop in `src/main.py`: Route `exit` command; handle invalid commands with helpful error message; implement welcome menu display on startup
- [ ] T029 Implement error handling in main loop: Catch KeyboardInterrupt (Ctrl+C); display "Goodbye!" and exit gracefully; catch unexpected exceptions and prompt user
- [ ] T030 Verify welcome menu in `src/main.py`: Display on startup with all 7 commands and descriptions; format clearly for user discovery

---

## Phase 9: Complete Verification & Polish

**Purpose**: Validate Phase I compliance and ensure all features work together

- [ ] T031 Manual end-to-end verification: Start app → See welcome menu → Execute full workflow: add 5 tasks with varied titles/descriptions → list all → update one → complete one → list to verify status → delete one → list to verify deletion → mark incomplete → list to verify revert → exit → Restart app → Verify all data lost (in-memory only, expected)
- [ ] T032 Verify error handling: Test all error cases: missing arguments, invalid IDs, non-numeric IDs, title too long, description too long, unknown commands → Verify helpful error messages for each
- [ ] T033 Verify all FRs met: Confirm FR-001 through FR-014 all working: sequential IDs (never reused), optional descriptions, status indicators, graceful error handling, help text, input validation, data reset on exit
- [ ] T034 Verify 5 core acceptance criteria from spec:
  - User Story 1 (Add): Task created with auto-incremented ID, status "incomplete", confirmation message
  - User Story 2 (List): All tasks displayed with correct IDs, status symbols, descriptions
  - User Story 3 (Update): Title and/or description updated; ID/status unchanged
  - User Story 4 (Delete): Task removed; new tasks get sequential IDs (no reuse)
  - User Story 5 (Complete/Incomplete): Status toggles; visual indicator changes in list
- [ ] T035 Verify success criteria: All commands execute in <100ms (local in-memory, guaranteed); no runtime errors; 100+ tasks supported without degradation; commands intuitive with clear usage output

---

## Phase 10: README & Documentation

**Purpose**: Provide setup and run instructions for users

- [ ] T036 Create `README.md` at repository root: Project description, Phase I scope, setup instructions (Python 3.13+, UV), run instructions (`python src/main.py`), usage examples, Phase II roadmap note
- [ ] T037 Create `CLAUDE.md` at repository root: Claude Code usage instructions, how to extend Phase I code for Phase II, development workflow, testing guidance

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories CAN proceed in parallel after Foundational is done
  - Or sequentially in priority order (US1 → US2 → US3 → US4 → US5)
  - Recommended: US1 & US2 together (MVP), then US3, US4, US5
- **Exit & Main Loop (Phase 8)**: Depends on at least one user story (suggest after US1)
- **Verification & Polish (Phase 9)**: Depends on all user stories complete
- **Documentation (Phase 10)**: Depends on everything else complete

### User Story Dependencies

- **User Story 1 (Add) (P1)**: No dependencies on other stories; start after Foundational
- **User Story 2 (List) (P1)**: No dependencies on other stories; can start in parallel with US1
- **User Story 3 (Update) (P2)**: No dependencies on other stories; can start after Foundational
- **User Story 4 (Delete) (P2)**: No dependencies on other stories; can start after Foundational
- **User Story 5 (Complete/Incomplete) (P2)**: No dependencies on other stories; can start after Foundational

### Parallel Opportunities

- **Phase 1 (Setup)**: All T001-T004 can be done in parallel or sequentially
- **Phase 2 (Foundational)**: T005, T006, T007, T008 can be parallelized (different files); T009 depends on T008
- **Phase 3-7 (User Stories)**:
  - Within each story: Commands (T010, T013, T017, T020, T023) can run in parallel; integration tasks (T011, T014, T018, T021, T025) depend on command tasks
  - Between stories: All stories can run fully in parallel after Foundational (Phase 2)
  - Recommended parallelization: US1 & US2 together, then US3, US4, US5 in parallel
- **Phase 9 (Verification)**: All verification tasks (T031-T035) must run sequentially after all implementations

---

## Parallel Example: US1 & US2 Together

```
FOUNDATIONAL PHASE (BLOCKING):
T005-T009 → Foundation Ready

Then parallelize US1 & US2:

Developer A: US1 (Add Task)        Developer B: US2 (View Tasks)
T010 (handle_add)                  T013 (handle_list)
T011 (integrate add)               T014 (formatting)
T012 (test manually)               T015 (integrate list)
                                   T016 (test manually)

Both stories complete & integrated independently; MVP achievable after both done
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T009)
3. Complete Phase 3: User Story 1 (T010-T012) & Phase 4: User Story 2 (T013-T016) **in parallel**
4. Complete Phase 8: Exit & Main Loop (T027-T030)
5. **STOP and VALIDATE**: User can add tasks, view tasks, exit app
6. Deploy/Demo if ready

### Full Phase I (All 5 Features)

1. Complete Setup + Foundational (as above)
2. Complete User Stories 1 & 2 (MVP)
3. Complete User Stories 3, 4, 5 **in parallel**
4. Complete Exit & Main Loop (if not done)
5. Complete Verification & Polish
6. Generate README & Documentation
7. All Phase I requirements met; ready for Phase II planning

### Recommended Task Sequence (If Sequential)

1. T001-T004 (Setup)
2. T005-T009 (Foundational)
3. T010-T012 (US1)
4. T013-T016 (US2)
5. T017-T019 (US3)
6. T020-T022 (US4)
7. T023-T026 (US5)
8. T027-T030 (Exit & Main Loop)
9. T031-T035 (Verification)
10. T036-T037 (Documentation)

Total: **37 atomic, executable tasks**

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Manual verification steps provided (no automated tests requested)
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All file paths are exact; copy-paste ready for implementation
- Tasks reference spec requirements (FR-001 through FR-014) for traceability

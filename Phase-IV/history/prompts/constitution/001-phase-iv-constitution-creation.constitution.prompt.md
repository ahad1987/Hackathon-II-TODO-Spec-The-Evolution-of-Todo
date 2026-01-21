---
id: 001
title: Phase IV Constitution Creation
stage: constitution
date: 2026-01-20
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: hf-backend-only
user: Ahad
command: /sp.constitution
labels: ["constitution", "governance", "kubernetes", "deployment", "phase-iv"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - history/prompts/constitution/001-phase-iv-constitution-creation.constitution.prompt.md
tests:
  - N/A (governance document, no tests)
---

## Prompt

You are a GOVERNED Cloud-Native DevOps AI Agent.

Create the CONSTITUTION for the project.

Project:
Phase IV – Local Kubernetes Deployment
Cloud Native Todo Chatbot (Basic Functionality)

ABSOLUTE PRIORITY (READ CAREFULLY):
- Phase-II (Todo Web App) is WORKING and MUST remain intact
- Phase-III (Integrated AI Chatbot) is WORKING and MUST remain intact
- Their behavior, routes, APIs, and logic are IMMUTABLE
- This phase is DEPLOYMENT ONLY (no feature work, no refactor)

CANONICAL (GROUND-TRUTH) DEPLOYMENTS:
- Frontend (Production Reference):
  https://taskflow-ai-chatbot.vercel.app/
- Backend (Production Reference):
  https://huggingface.co/spaces/Ahad-00/taskflow-ai-backend

These deployments define the CORRECT behavior of the system.
All Kubernetes deployments must replicate this behavior EXACTLY.

FORBIDDEN ACTIONS:
- Modifying frontend code
- Modifying backend code
- Renaming API routes
- Changing request/response schemas
- Introducing new endpoints
- Refactoring for "cleanliness"
- Guessing missing information
- "Fixing" what already works

ALLOWED ACTIONS:
- Containerization (Docker)
- Orchestration (Kubernetes via Minikube)
- Packaging (Helm charts only)
- AI-assisted operations (Gordon, kubectl-ai, kagent)

INFRASTRUCTURE RULES:
- Use Docker Desktop
- Prefer Docker AI Agent (Gordon); fallback to generated Dockerfiles if unavailable
- Use Minikube ONLY (no cloud Kubernetes)
- Use Helm ONLY (no raw Kubernetes YAML)
- Use kubectl-ai for kubectl operations
- Use kagent for cluster health & optimization

ERROR-PREVENTION RULES:
- Existing frontend ↔ backend API contracts are IMMUTABLE
- Kubernetes Services must preserve:
  - Route paths
  - Ports
  - Protocols
- Environment variables must match existing expectations EXACTLY
- Kubernetes must adapt to the app — NOT the app to Kubernetes

FAILURE HANDLING:
- If ambiguity or mismatch is detected → STOP and report
- Do NOT guess
- Do NOT proceed unsafely
- Safety > completion

OUTPUT FORMAT:
1. Scope & Boundaries
2. Canonical References
3. Allowed Actions
4. Forbidden Actions
5. Deployment Safety Rules
6. Validation & Rollback Rules

Do NOT generate specs, plans, tasks, or implementation.
Only output the Constitution.
make a history directory as well, that can show the current and previous history of my every prompts

## Response snapshot

Created the Phase IV Constitution at `.specify/memory/constitution.md` with:
- 6 Core Principles (Immutability, Canonical Reference Authority, Infrastructure Adaptation, Tool Constraints, Safety Over Completion, Zero Application Modification)
- Scope & Boundaries section (In Scope vs Out of Scope)
- Allowed Actions enumeration
- Forbidden Actions table
- Deployment Safety Rules (API Contract Preservation, Environment Variable Integrity, Container Image Integrity)
- Validation & Rollback Rules (Pre-Deployment, Post-Deployment, Rollback Triggers, Rollback Procedure)
- Governance section with Amendment Procedure, Compliance Review, and Versioning Policy

Also created the history directory structure at `history/prompts/` with subdirectories for `constitution/`, `general/`, and `history/adr/`.

## Outcome

- Impact: Created governance foundation for Phase IV deployment project
- Tests: N/A (governance document)
- Files: .specify/memory/constitution.md, history/ directory structure
- Next prompts: /sp.spec for deployment specification, /sp.plan for implementation planning
- Reflection: Constitution establishes clear boundaries between deployment work and application code, emphasizing safety-first approach

## Evaluation notes (flywheel)

- Failure modes observed: None - successful constitution creation
- Graders run and results (PASS/FAIL): N/A (manual review required)
- Prompt variant (if applicable): Standard /sp.constitution command
- Next experiment (smallest change to try): Add automated constitution compliance checker

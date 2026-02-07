---
id: 001
title: TaskFlow AI Project Constitution
stage: constitution
date: 2026-01-22
surface: agent
model: claude-sonnet-4-5
feature: none
branch: 001-k8s-deployment
user: TaskFlow Deploy
command: /sp.constitution
labels: ["governance", "principles", "phase-iv", "kubernetes", "dapr", "workflow"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
tests:
 - None
---

## Prompt

You are operating under **Speckit Plus governance**.

This document is the **PROJECT CONSTITUTION**.
It overrides all future prompts and instructions.

---

## CORE PRINCIPLES

* Phase IV functionality is **immutable** and must not regress
* All changes must be **additive only**
* Event-driven architecture is mandatory
* Kafka access is allowed **ONLY via Dapr Pub/Sub**
* Kubernetes is the base runtime
* Local success (Minikube) **must precede** any cloud deployment

---

## ABSOLUTE RULES (NON-NEGOTIABLE)

1. Do NOT modify existing APIs unless explicitly approved
2. Do NOT introduce direct Kafka clients
3. Do NOT bypass Dapr abstractions
4. Do NOT refactor unrelated code
5. Do NOT proceed without **human approval** at every stage
6. Do NOT guess — ask
7. Existing database schemas and data **must remain valid**

   * Only backward-compatible, additive migrations allowed
8. Applications must start and function even if **Dapr sidecar is temporarily unavailable**
9. After every major change, you MUST verify that all Phase IV
   services, endpoints, and deployments still work exactly as before
10. Every major change must define a **rollback strategy**

---

## WORKFLOW LAW

You MUST follow this order exactly:

**Constitution → Specification → Plan → Tasks → Implementation**

Violation of this constitution is considered failure.

Acknowledge and confirm compliance.
STOP and wait.

## Response snapshot

**Constitution Created: Version 1.0.0**

I have successfully created the TaskFlow AI Constitution at `.specify/memory/constitution.md` with the following structure:

### Core Principles (7 principles defined):
1. **Phase IV Immutability** - Existing functionality must never regress
2. **Additive-Only Changes** - Build on top, never replace
3. **Event-Driven Architecture** - Mandatory for inter-service communication
4. **Dapr Abstraction Layer** - Kafka access only via Dapr Pub/Sub
5. **Kubernetes Runtime** - Base deployment environment
6. **Local-First Validation** - Minikube success before cloud deployment
7. **Human-in-the-Loop Governance** - Approval required at every stage

### Additional Sections:
- **Deployment & Runtime Requirements** (Database integrity, resilience, verification)
- **Development Workflow** (Workflow law, absolute rules, change approval)
- **Governance** (Amendment procedure, version policy, compliance review)

### Validation Results:
✅ All template files validated for consistency
✅ plan-template.md Constitution Check section aligns
✅ spec-template.md requirements sections align
✅ tasks-template.md task categorization aligns
✅ No unresolved placeholders remaining
✅ Semantic versioning applied: 1.0.0 (initial version)

### Files Updated:
- `.specify/memory/constitution.md` (created/overwritten with v1.0.0)

## Outcome

- ✅ Impact: Project constitution established with 7 core principles, deployment requirements, workflow law, and governance rules. Version 1.0.0 ratified on 2026-01-22.
- 🧪 Tests: N/A (governance document)
- 📁 Files: 1 file created (.specify/memory/constitution.md)
- 🔁 Next prompts: /sp.specify (to create feature specifications), /sp.plan (to create implementation plans following workflow law)
- 🧠 Reflection: Constitution successfully encodes all user-provided constraints including Phase IV immutability, additive-only changes, Dapr-only Kafka access, K8s runtime, local-first validation, and human approval gates. Workflow law explicitly defined.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual validation PASS (all placeholders resolved, version coherent, templates consistent)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Next step is /sp.specify to create first feature specification following the workflow law

# Data Model: Phase IV Local Kubernetes Deployment

**Date**: 2026-01-20
**Context**: This is a deployment-only project. The data model is IMMUTABLE and defined by the existing Phase-II and Phase-III applications.

---

## Overview

Phase IV does NOT create new data entities. It deploys existing applications with their established data models. This document references the existing data structures for context.

---

## Existing Data Entities (Read-Only Reference)

### User Entity
**Source**: Phase-II Backend (`src/models/user.py`)

**Fields**:
- `id` (UUID, primary key)
- `email` (string, unique, max 255 characters)
- `password_hash` (string, bcrypt hashed)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Relationships**:
- One-to-many with Task
- One-to-many with Conversation

**Validation Rules** (enforced by application):
- Email must match regex pattern
- Password minimum 8 characters
- Email uniqueness enforced at database level

---

### Task Entity
**Source**: Phase-II Backend (`src/models/task.py`)

**Fields**:
- `id` (UUID, primary key)
- `user_id` (UUID, foreign key to User)
- `title` (string, required, 1-255 characters)
- `description` (string, optional, max 5000 characters)
- `completed` (boolean, default false)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Relationships**:
- Many-to-one with User (via user_id)

**Validation Rules** (enforced by application):
- Title required, length 1-255
- Description optional, max 5000 characters
- User isolation enforced (users can only access their own tasks)

---

### Conversation Entity
**Source**: Phase-III Backend (`src/chatbot/models/conversation.py`)

**Fields**:
- `id` (UUID, primary key)
- `user_id` (UUID, foreign key to User)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Relationships**:
- Many-to-one with User (via user_id)
- One-to-many with Message

**Purpose**: Groups related chatbot messages into conversation threads

---

### Message Entity
**Source**: Phase-III Backend (`src/chatbot/models/message.py`)

**Fields**:
- `id` (UUID, primary key)
- `conversation_id` (UUID, foreign key to Conversation)
- `role` (string, enum: "user" | "assistant")
- `content` (text, message content)
- `tool_calls` (JSON, optional, serialized tool execution data)
- `created_at` (timestamp)

**Relationships**:
- Many-to-one with Conversation (via conversation_id)

**Purpose**: Stores individual chatbot messages and tool execution history

---

## Kubernetes-Specific Data (NEW for Phase IV)

### ConfigMap Data
**Purpose**: Non-sensitive configuration for deployed services

**Backend ConfigMap** (`taskflow-backend-config`):
- `API_PREFIX`: `/api/v1`
- `API_TITLE`: `Todo API`
- `API_VERSION`: `0.1.0`
- `ENVIRONMENT`: `development`
- `DEBUG`: `False`
- `JWT_ALGORITHM`: `HS256`
- `JWT_EXPIRY`: `86400` (24 hours)
- `PASSWORD_HASH_ALGORITHM`: `bcrypt`
- `PASSWORD_HASH_ROUNDS`: `12`

**Frontend ConfigMap** (`taskflow-frontend-config`):
- `NEXT_PUBLIC_API_URL`: `http://taskflow-backend-service:8000` (internal cluster DNS)
- `NODE_ENV`: `production`

### Secret Data
**Purpose**: Sensitive credentials for deployed services

**Backend Secret** (`taskflow-backend-secrets`):
- `DATABASE_URL`: PostgreSQL connection string (user-provided)
- `BETTER_AUTH_SECRET`: JWT signing secret, min 32 characters (user-provided)
- `ANTHROPIC_API_KEY`: Claude API key for chatbot (user-provided)
- `CORS_ORIGINS`: Comma-separated allowed origins (includes Minikube endpoint)

**Frontend Secret** (`taskflow-frontend-secrets`):
- `BETTER_AUTH_SECRET`: Must match backend secret exactly
- `BETTER_AUTH_URL`: Authentication callback URL (Minikube NodePort endpoint)

---

## Service Discovery Data

### Backend Service
**DNS Name**: `taskflow-backend-service` or `taskflow-backend-service.default.svc.cluster.local`
**Port**: `8000`
**Type**: `ClusterIP` (internal only)

**Endpoints Exposed**:
- `GET /health`
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/tasks`
- `POST /api/v1/tasks`
- `PUT /api/v1/tasks/{task_id}`
- `DELETE /api/v1/tasks/{task_id}`
- `POST /api/v1/chat`

### Frontend Service
**DNS Name**: `taskflow-frontend-service`
**Port**: `3000`
**Type**: `NodePort` (external access)
**NodePort Range**: `30000-32767` (Kubernetes assigns automatically)

---

## Data Flow

### Authentication Flow
1. User submits credentials to frontend
2. Frontend sends POST to `http://taskflow-backend-service:8000/api/v1/auth/login`
3. Backend validates credentials against `users` table
4. Backend generates JWT using `BETTER_AUTH_SECRET`
5. Frontend stores JWT and includes in Authorization header for subsequent requests

### Task Management Flow
1. User creates task in frontend UI
2. Frontend sends POST to `http://taskflow-backend-service:8000/api/v1/tasks` with JWT
3. Backend validates JWT (extracts user_id)
4. Backend inserts task with user_id into `tasks` table
5. Backend returns task object to frontend

### Chatbot Flow
1. User sends message in ChatWidget
2. Frontend sends POST to `http://taskflow-backend-service:8000/api/v1/chat` with JWT
3. Backend creates/loads conversation from `conversations` table
4. Backend saves user message to `messages` table
5. Backend invokes Anthropic Claude API with conversation history
6. Backend executes MCP tools (add_task, list_tasks, etc.) if Claude requests
7. Backend saves assistant response to `messages` table
8. Backend returns response to frontend

---

## Database Schema (Existing)

**Database**: PostgreSQL
**Connection**: Via `DATABASE_URL` environment variable
**Schema Management**: Alembic migrations (already applied in Phase-II/III)

**Tables**:
- `users` (id, email, password_hash, created_at, updated_at)
- `tasks` (id, user_id, title, description, completed, created_at, updated_at)
- `conversations` (id, user_id, created_at, updated_at)
- `messages` (id, conversation_id, role, content, tool_calls, created_at)

**Indexes**:
- `users.email` (unique)
- `tasks.user_id` (for user isolation queries)
- `conversations.user_id` (for user conversation lookups)
- `messages.conversation_id` (for conversation history queries)

---

## Validation Rules (Application-Enforced)

### User Validation
- Email format validation via regex
- Password minimum length: 8 characters
- Email uniqueness check before insert

### Task Validation
- Title required (1-255 characters)
- Description optional (max 5000 characters)
- User_id must match authenticated user (enforced by middleware)

### Message Validation
- Role must be "user" or "assistant"
- Content required (non-empty)
- Conversation_id must exist and belong to authenticated user

---

## Phase IV Deployment Considerations

### Data Persistence
- Database remains EXTERNAL to Kubernetes cluster
- No Persistent Volume Claims required for application state
- Stateless containers can be restarted without data loss

### Data Migration
- NO database migrations in Phase IV scope
- Existing schema is used as-is
- Connection string updated in SECRET to point to accessible database

### Data Validation
- Application code performs all validation (immutable)
- Kubernetes deployment does NOT add validation layers
- ConfigMaps/Secrets provide configuration, not business logic

---

## Summary

Phase IV introduces NO new data entities. All data structures are pre-existing and IMMUTABLE. The deployment adds:
- **ConfigMap data** for non-sensitive configuration
- **Secret data** for credentials
- **Service discovery** metadata for Kubernetes networking

All application data models, relationships, and validation rules remain exactly as implemented in Phase-II and Phase-III.

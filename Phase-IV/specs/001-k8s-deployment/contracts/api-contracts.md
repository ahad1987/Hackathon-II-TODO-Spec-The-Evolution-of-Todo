# API Contracts: Phase IV Local Kubernetes Deployment

**Date**: 2026-01-20
**Context**: IMMUTABLE API contracts from Phase-II and Phase-III applications
**Base URL**: `http://taskflow-backend-service:8000` (Kubernetes internal DNS)

---

## Overview

These API contracts are **IMMUTABLE** and defined by the existing Phase-II (Todo Web App) and Phase-III (AI Chatbot) backend. Kubernetes deployment MUST preserve these contracts exactly.

---

## Authentication Endpoints

### 1. Health Check
**Endpoint**: `GET /health`
**Authentication**: None
**Purpose**: System health monitoring

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "chat_registered": true
}
```

---

### 2. User Signup
**Endpoint**: `POST /api/v1/auth/signup`
**Authentication**: None
**Purpose**: Create new user account

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response** (201 Created):
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2026-01-20T10:30:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "User registered successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid email format, weak password, or duplicate email
- `500 Internal Server Error`: Database or server error

---

### 3. User Login
**Endpoint**: `POST /api/v1/auth/login`
**Authentication**: None
**Purpose**: Authenticate user and return JWT token

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2026-01-20T10:30:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Login successful"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid email or password
- `500 Internal Server Error`: Database or server error

---

### 4. User Logout
**Endpoint**: `POST /api/v1/auth/logout`
**Authentication**: Required (JWT in Authorization header)
**Purpose**: Logout user (stub implementation in Phase-II)

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "status": "pending",
  "message": "Logout endpoint created (T022 stub). Implementation in T099."
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `500 Internal Server Error`: Server error

---

### 5. Get Current User
**Endpoint**: `GET /api/v1/auth/me`
**Authentication**: Required (JWT in Authorization header)
**Purpose**: Retrieve authenticated user's information

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "created_at": "2026-01-20T10:30:00Z"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: User no longer exists
- `500 Internal Server Error`: Database or server error

---

### 6. Refresh Token
**Endpoint**: `POST /api/v1/auth/refresh`
**Authentication**: Refresh token (cookie or request body)
**Purpose**: Renew access token using refresh token

**Request Body** (optional if in cookies):
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Token refreshed successfully"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired refresh token
- `500 Internal Server Error`: Server error

---

## Task Management Endpoints

### 7. List Tasks
**Endpoint**: `GET /api/v1/tasks`
**Authentication**: Required (JWT in Authorization header)
**Purpose**: Retrieve all tasks for authenticated user

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Complete project documentation",
    "description": "Write comprehensive docs for Phase IV",
    "completed": false,
    "created_at": "2026-01-20T10:35:00Z",
    "updated_at": "2026-01-20T10:35:00Z"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Review deployment strategy",
    "description": null,
    "completed": true,
    "created_at": "2026-01-19T14:20:00Z",
    "updated_at": "2026-01-20T09:15:00Z"
  }
]
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `500 Internal Server Error`: Database or server error

---

### 8. Create Task
**Endpoint**: `POST /api/v1/tasks`
**Authentication**: Required (JWT in Authorization header)
**Purpose**: Create a new task for authenticated user

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body**:
```json
{
  "title": "Complete project documentation",
  "description": "Write comprehensive docs for Phase IV"
}
```

**Response** (201 Created):
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Complete project documentation",
  "description": "Write comprehensive docs for Phase IV",
  "completed": false,
  "created_at": "2026-01-20T10:35:00Z",
  "updated_at": "2026-01-20T10:35:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Title missing or exceeds 255 characters, description exceeds 5000 characters
- `401 Unauthorized`: Missing or invalid JWT token
- `500 Internal Server Error`: Database or server error

---

### 9. Update Task
**Endpoint**: `PUT /api/v1/tasks/{task_id}`
**Authentication**: Required (JWT in Authorization header)
**Purpose**: Update task title, description, or completion status

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body** (all fields optional):
```json
{
  "title": "Updated task title",
  "description": "Updated description",
  "completed": true
}
```

**Response** (200 OK):
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Updated task title",
  "description": "Updated description",
  "completed": true,
  "created_at": "2026-01-20T10:35:00Z",
  "updated_at": "2026-01-20T11:45:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Validation error (title/description too long)
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Task belongs to another user
- `404 Not Found`: Task does not exist
- `500 Internal Server Error`: Database or server error

---

### 10. Delete Task
**Endpoint**: `DELETE /api/v1/tasks/{task_id}`
**Authentication**: Required (JWT in Authorization header)
**Purpose**: Permanently delete a task

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (204 No Content):
```
(Empty body)
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Task belongs to another user
- `404 Not Found`: Task does not exist
- `500 Internal Server Error`: Database or server error

---

## Chatbot Endpoint

### 11. Chat with AI Assistant
**Endpoint**: `POST /api/v1/chat`
**Authentication**: Required (JWT in Authorization header)
**Purpose**: Send message to AI chatbot and receive response

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body**:
```json
{
  "conversation_id": "880e8400-e29b-41d4-a716-446655440000",
  "message": "Create a task to finish the deployment documentation"
}
```

**Note**: Omit `conversation_id` to start a new conversation

**Response** (200 OK):
```json
{
  "conversation_id": "880e8400-e29b-41d4-a716-446655440000",
  "response": "I've created a task for you: 'Finish the deployment documentation'. The task has been added to your task list.",
  "tool_calls": ["add_task"],
  "status": "success"
}
```

**Error Responses**:
- `400 Bad Request`: Message empty or exceeds 10,000 characters
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Conversation ID provided but doesn't exist or doesn't belong to user
- `500 Internal Server Error`: Chatbot service error, database error, or Anthropic API error

**Tool Execution**:
The chatbot can execute the following MCP tools:
- `add_task`: Create a new task
- `list_tasks`: Retrieve user's tasks
- `update_task`: Modify an existing task
- `delete_task`: Remove a task
- `complete_task`: Mark task as completed

Tool executions are reflected in the `tool_calls` array in the response.

---

## CORS Configuration

**Allowed Origins** (configured via `CORS_ORIGINS` environment variable):
- `http://localhost:3000` (development)
- `http://localhost:3001` (alternative development port)
- `http://localhost:5173` (Vite development)
- `https://mytodoappv2.vercel.app` (Phase-II production)
- `https://stately-dieffenbachia-b565a9.netlify.app` (alternative Phase-II)
- `https://taskflow-ai-chatbot.vercel.app` (Phase-III production)
- **Minikube endpoint** (must be added for local deployment)

**Allowed Methods**: All (`*`)
**Allowed Headers**: All (`*`)
**Allow Credentials**: `true`

---

## Authentication Mechanism

**Type**: JWT (JSON Web Token)
**Header**: `Authorization: Bearer <token>`
**Algorithm**: HS256 (HMAC-SHA256)
**Secret**: `BETTER_AUTH_SECRET` environment variable (minimum 32 characters)
**Expiry**: 86400 seconds (24 hours) by default
**Issuer**: Backend FastAPI application

**Token Payload**:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "exp": 1737468600,
  "iat": 1737382200
}
```

**Token Validation**:
- Performed by `AuthenticationMiddleware` on all protected routes
- Extracts `sub` (subject) claim as `user_id`
- Verifies signature using `BETTER_AUTH_SECRET`
- Checks expiration (`exp` claim)

---

## Error Response Format

All error responses follow this structure:

```json
{
  "error": "Brief error description",
  "code": "ERROR_CODE",
  "message": "Detailed user-friendly message"
}
```

**Common Error Codes**:
- `SIGNUP_ERROR`: User registration failed
- `INVALID_CREDENTIALS`: Login failed (wrong email/password)
- `USER_NOT_FOUND`: User does not exist
- `USER_RETRIEVAL_ERROR`: Failed to retrieve user info
- `NO_REFRESH_TOKEN`: Refresh token not provided
- `INVALID_REFRESH_TOKEN`: Refresh token invalid or expired
- `TOKEN_REFRESH_ERROR`: Token refresh failed
- `TASK_FETCH_ERROR`: Failed to retrieve tasks
- `TASK_CREATION_ERROR`: Failed to create task
- `TASK_UPDATE_ERROR`: Failed to update task
- `TASK_DELETION_ERROR`: Failed to delete task
- `INTERNAL_ERROR`: Unhandled exception

---

## Kubernetes-Specific Considerations

### Service Discovery
- Frontend MUST call backend using internal DNS: `http://taskflow-backend-service:8000`
- Backend service name: `taskflow-backend-service` (ClusterIP)
- Port: `8000` (must not be changed)

### CORS Updates
- `CORS_ORIGINS` must include the Minikube NodePort endpoint for frontend
- Example: `http://192.168.49.2:30080` (IP and port depend on Minikube setup)

### Health Check Endpoints
- `/health` used for liveness and readiness probes
- Must return `200 OK` with `"status": "healthy"` for healthy state
- Backend may return `"chat_registered": false` if chatbot module fails to load

### Environment Variable Dependencies
- `DATABASE_URL`: Backend cannot start without valid PostgreSQL connection
- `BETTER_AUTH_SECRET`: Authentication will fail if not set or too short
- `ANTHROPIC_API_KEY`: Chatbot endpoint will error without valid key

---

## Contract Validation Strategy

**Pre-Deployment**:
1. Verify no application code changes (`git status` clean)
2. Confirm API routes in code match this document
3. Validate environment variables are configured

**Post-Deployment**:
1. Call each endpoint from frontend container
2. Compare responses byte-for-byte with production
3. Test authentication flow (signup → login → JWT validation)
4. Test task CRUD operations
5. Test chatbot interaction and tool execution

**Rollback Trigger**:
- Any endpoint returns different status code than documented
- Any response structure differs from this contract
- Authentication mechanism fails in a way not seen in production

---

## Summary

These 11 API endpoints are **IMMUTABLE** and form the contract between frontend and backend. Kubernetes deployment MUST:
- Preserve all route paths exactly
- Preserve port 8000 for backend
- Maintain JWT authentication mechanism
- Ensure CORS configuration includes Minikube endpoint
- Not modify request/response schemas

Any deviation triggers immediate rollback per Constitutional mandate.

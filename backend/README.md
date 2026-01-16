---
title: Todo Backend API
emoji: 📝
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Todo Backend API

Full-stack Todo application backend built with FastAPI.

## Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `GET /docs` - Swagger documentation
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task

## Tech Stack

- FastAPI
- PostgreSQL (Neon)
- SQLModel
- JWT Authentication

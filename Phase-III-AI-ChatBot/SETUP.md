# Phase-III AI Chatbot - Setup & Installation Guide

**Version**: 1.0
**Date**: 2026-01-15
**Status**: Phase 2 Complete, Ready for User Stories

---

## Prerequisites

### System Requirements
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or Neon serverless)
- Git

### API Keys Required
- OpenAI API key (for GPT-4 Agent)
- Better Auth configuration (inherited from Phase-II)

---

## Backend Setup

### 1. Install Python Dependencies

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# For development (with testing dependencies)
pip install -r requirements-dev.txt
```

### 2. Environment Configuration

Create `.env` file in `backend/` directory:

```env
# Database
DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
# For Neon serverless: postgresql+psycopg://user:password@host/dbname

# OpenAI API
OPENAI_API_KEY=sk-...

# Better Auth (inherited from Phase-II)
AUTH_SECRET=your_secret_key

# Server
ENVIRONMENT=development  # or production
DEBUG=true

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# Logging
LOG_LEVEL=INFO
```

### 3. Database Initialization

```bash
# Create tables (Phase-II + Phase-III)
python src/main.py --init-db

# Run Alembic migrations (Phase-III)
alembic upgrade head

# Verify database
python -c "from src.database import init_sync_db; init_sync_db()"
```

### 4. Verify Installation

```bash
# Test imports
python -c "from src.chatbot.services import ConversationService, AgentService; print('✓ Imports OK')"

# Run unit tests
pytest backend/tests/unit/ -v

# Run integration tests (requires database)
pytest backend/tests/integration/ -v
```

### 5. Start Backend Server

```bash
# Development (with auto-reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8000
```

**Verify** at `http://localhost:8000/health`

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend

npm install
# or
yarn install
```

### 2. Environment Configuration

Create `.env` file in `frontend/` directory:

```env
# API
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Features
VITE_ENABLE_CHAT=true
VITE_ENABLE_DEBUG=true

# OpenAI ChatKit (from npm package)
VITE_OPENAI_API_KEY=sk-...  # Optional: for ChatKit theming
```

### 3. Verify Installation

```bash
npm run build  # Should compile without errors
```

### 4. Start Development Server

```bash
npm run dev
```

**Access** at `http://localhost:5173`

---

## API Verification

### Test Authentication

```bash
# Get health check
curl http://localhost:8000/health

# Expected response:
# {"status": "ok", "database": "connected"}
```

### Test Chat Endpoint

```bash
# Create a test user (via Phase-II)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass"}'

# Expected response:
# {"user_id": "uuid", "token": "jwt-token", ...}

# Save the token
TOKEN="your-jwt-token-here"

# Make a chat request
curl -X POST http://localhost:8000/api/{user_id}/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Add a task to buy milk"}'

# Expected response:
# {
#   "conversation_id": "uuid",
#   "response": "Task created: 'buy milk'",
#   "tool_calls": ["add_task"],
#   "status": "success"
# }
```

---

## Database Setup (Details)

### Phase-II Tables (Read-Only for Phase-III)

```sql
-- Users table (Phase-II, unchanged)
SELECT * FROM users;

-- Tasks table (Phase-II, unchanged)
SELECT * FROM tasks WHERE user_id = '{user_id}';
```

### Phase-III Tables (New)

```sql
-- Conversations (new)
SELECT * FROM conversation WHERE user_id = '{user_id}';

-- Messages (new)
SELECT * FROM message WHERE user_id = '{user_id}';
```

### Verify Migrations

```bash
# Check migration status
alembic current
alembic history

# Verify tables exist
psql $DATABASE_URL -c "\dt"
```

---

## Testing

### Unit Tests

```bash
# All unit tests
pytest backend/tests/unit/ -v

# Specific test file
pytest backend/tests/unit/test_mcp_tools.py -v

# Specific test class
pytest backend/tests/unit/test_auth_validation.py::TestJWTValidation -v

# Coverage report
pytest backend/tests/unit/ --cov=src.chatbot --cov-report=html
```

### Integration Tests

```bash
# All integration tests
pytest backend/tests/integration/ -v

# Statelessness verification (CRITICAL)
pytest backend/tests/integration/test_statelessness.py -v

# Chat flow tests
pytest backend/tests/integration/test_chat_full_flow.py -v

# Phase-II regression tests
pytest backend/tests/integration/test_phase2_regression.py -v
```

### E2E Tests (Coming Phase 3-5)

```bash
# Will test full user flows including frontend
# Requires running backend + frontend
```

---

## Development Workflow

### Making Changes

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Implement changes**:
   - Write code in appropriate module
   - Follow existing patterns
   - Add/update tests

3. **Run tests**:
   ```bash
   pytest backend/tests/ -v
   ```

4. **Commit changes**:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature
   # Then create PR on GitHub
   ```

### Code Standards

- **Python**: PEP 8, type hints
- **Tests**: pytest, >80% coverage target
- **Commits**: Descriptive messages, atomic changes
- **PR Reviews**: Before merge to main

---

## Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError: No module named 'src'`
- **Solution**: Ensure you're in `backend/` directory with correct Python path
  ```bash
  export PYTHONPATH="${PYTHONPATH}:$(pwd)"
  ```

**Issue**: `Error connecting to database`
- **Solution**: Verify DATABASE_URL and database is running
  ```bash
  psql $DATABASE_URL -c "SELECT 1"
  ```

**Issue**: `OpenAI API key error`
- **Solution**: Verify OPENAI_API_KEY in .env
  ```bash
  echo $OPENAI_API_KEY  # Should show your key
  ```

### Frontend Issues

**Issue**: `CORS error when calling API`
- **Solution**: Verify CORS config in backend
  - Check `FRONTEND_URL` matches frontend URL
  - Verify backend has CORSMiddleware enabled

**Issue**: `Chat widget not appearing`
- **Solution**: Check browser console for errors
  - Verify VITE_API_URL points to running backend
  - Check Network tab for API calls

### Database Issues

**Issue**: `Migration conflicts`
- **Solution**: Reset database (development only!)
  ```bash
  psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  alembic upgrade head
  ```

---

## Performance Tuning

### Database Optimization

```sql
-- Verify indexes exist
SELECT indexname FROM pg_indexes WHERE tablename = 'conversation';
SELECT indexname FROM pg_indexes WHERE tablename = 'message';

-- If missing, create manually
CREATE INDEX idx_conversation_user_id ON conversation(user_id);
CREATE INDEX idx_message_user_id ON message(user_id);
CREATE INDEX idx_message_conversation_id ON message(conversation_id);
```

### Backend Optimization

- **Connection pooling**: Configured via SQLModel
- **Caching**: Not used (stateless design)
- **Pagination**: Prepare for future phases

### Frontend Optimization

- **Code splitting**: Vite handles automatically
- **Lazy loading**: ChatWidget loads on demand
- **Image optimization**: Use next-gen formats

---

## Security Checklist

Before deploying to production:

- [ ] `DEBUG=false` in production
- [ ] OPENAI_API_KEY secured (use secrets manager)
- [ ] AUTH_SECRET strong (32+ characters)
- [ ] DATABASE_URL uses SSL connection
- [ ] CORS only allows production frontend URL
- [ ] HTTPS enabled on all endpoints
- [ ] Rate limiting configured
- [ ] Error monitoring (Sentry/similar) enabled
- [ ] Logs don't contain sensitive data
- [ ] JWT expiration configured appropriately

---

## Deployment

### Development
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Staging/Production

See deployment guides:
- **Backend**: `docs/deployment-backend.md` (to be created)
- **Frontend**: `docs/deployment-frontend.md` (to be created)
- **Database**: `docs/deployment-database.md` (to be created)

---

## Next Steps

### After Setup
1. Run all tests to verify installation
2. Try example API calls (see "API Verification")
3. Review `ARCHITECTURE.md` for system design
4. Review `CHATBOT_SAFETY.md` for constraints

### For User Story Development
1. Read `PHASE2_COMPLETION.md` for Phase 2 summary
2. Review User Story tasks in `tasks.md`
3. Follow development workflow above
4. Ensure tests pass before submitting PR

---

## Support

- **Issues**: Check `docs/troubleshooting.md` or GitHub Issues
- **Questions**: See `ARCHITECTURE.md` for design questions
- **Bugs**: Report with steps to reproduce

---

**Setup Guide Version**: 1.0
**Last Updated**: 2026-01-15
**Status**: ✅ Phase 2 Ready

Next: User Stories (Phase 3-5) Implementation

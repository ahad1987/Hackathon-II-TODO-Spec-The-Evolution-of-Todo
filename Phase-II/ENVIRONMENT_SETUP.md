# 🔧 Environment Setup Guide

Complete guide for setting up environment variables for development, testing, and production.

---

## 🏠 Development Environment

### Backend Setup (`.env` file)

```bash
# Create backend/.env file
cd backend

cat > .env << 'EOF'
# Database - Use local PostgreSQL or Neon dev instance
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/todo_db

# JWT Configuration
BETTER_AUTH_SECRET=your-very-long-secret-key-at-least-32-characters-for-development
JWT_EXPIRY=86400
JWT_ALGORITHM=HS256

# Server Configuration
DEBUG=true
ENVIRONMENT=development
API_TITLE=Todo API
API_VERSION=0.1.0

# CORS Configuration (allow localhost)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:3001

# Password Hashing
PASSWORD_HASH_ALGORITHM=bcrypt
PASSWORD_HASH_ROUNDS=12

# Pagination
DEFAULT_PAGE_SIZE=50
MAX_PAGE_SIZE=100

# Task Constraints
TASK_TITLE_MIN_LENGTH=1
TASK_TITLE_MAX_LENGTH=255
TASK_DESCRIPTION_MAX_LENGTH=5000

# User Constraints
PASSWORD_MIN_LENGTH=8
EMAIL_MAX_LENGTH=255
EOF
```

### Frontend Setup (`frontend/.env.local` file)

```bash
# Create frontend/.env.local file
cd ../frontend

cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_BETTER_AUTH_SECRET=your-very-long-secret-key-at-least-32-characters-for-development
NODE_ENV=development
EOF
```

### Verify Setup

```bash
# Backend should start without errors
cd backend
python -m uvicorn src.main:app --reload

# Frontend should start without errors (in another terminal)
cd frontend
npm run dev

# Visit http://localhost:3000
```

---

## 🧪 Testing Environment

### Backend Test Setup (`.env.test`)

```bash
# Create backend/.env.test file
cat > backend/.env.test << 'EOF'
# Use test database (separate from development)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/todo_test

# JWT Configuration
BETTER_AUTH_SECRET=test-secret-key-at-least-32-characters-for-testing-purposes
JWT_EXPIRY=3600
JWT_ALGORITHM=HS256

# Server Configuration
DEBUG=true
ENVIRONMENT=testing
API_TITLE=Todo API Test
API_VERSION=0.1.0

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Other settings same as development...
PASSWORD_HASH_ALGORITHM=bcrypt
PASSWORD_HASH_ROUNDS=12
DEFAULT_PAGE_SIZE=50
MAX_PAGE_SIZE=100
TASK_TITLE_MIN_LENGTH=1
TASK_TITLE_MAX_LENGTH=255
TASK_DESCRIPTION_MAX_LENGTH=5000
PASSWORD_MIN_LENGTH=8
EMAIL_MAX_LENGTH=255
EOF
```

### Run Tests

```bash
# Set test environment and run
cd backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/todo_test \
BETTER_AUTH_SECRET=test-secret-key-at-least-32-characters-for-testing-purposes \
python -m pytest tests/
```

---

## 🚀 Production Environment

### Prerequisites

1. **Neon PostgreSQL Database**
   - Go to https://neon.tech
   - Create project
   - Get connection string (PostgreSQL format)

2. **Generate Secrets**
   ```bash
   # Generate strong secret (32+ characters)
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Example output:
   # Drmhze6EPcv0fN_81Bj-nA_fake_example_secret_key_123
   ```

3. **Get Frontend URL**
   - Will be: `https://your-site.netlify.app`
   - Will be: `https://your-space-url` (for HF Spaces)

### Backend Production Setup (HF Spaces)

**In Hugging Face Space Settings → Secrets**, add these environment variables:

```
KEY: DATABASE_URL
VALUE: postgresql+psycopg://user:password@host/database

KEY: BETTER_AUTH_SECRET
VALUE: [your-32-character-secret-generated-above]

KEY: JWT_EXPIRY
VALUE: 86400

KEY: JWT_ALGORITHM
VALUE: HS256

KEY: ENVIRONMENT
VALUE: production

KEY: DEBUG
VALUE: false

KEY: API_TITLE
VALUE: TaskFlow API

KEY: API_VERSION
VALUE: 2.0.0

KEY: CORS_ORIGINS
VALUE: https://your-site.netlify.app

KEY: PASSWORD_HASH_ALGORITHM
VALUE: bcrypt

KEY: PASSWORD_HASH_ROUNDS
VALUE: 12

KEY: DEFAULT_PAGE_SIZE
VALUE: 50

KEY: MAX_PAGE_SIZE
VALUE: 100

KEY: TASK_TITLE_MIN_LENGTH
VALUE: 1

KEY: TASK_TITLE_MAX_LENGTH
VALUE: 255

KEY: TASK_DESCRIPTION_MAX_LENGTH
VALUE: 5000

KEY: PASSWORD_MIN_LENGTH
VALUE: 8

KEY: EMAIL_MAX_LENGTH
VALUE: 255
```

### Frontend Production Setup (Netlify)

**In Netlify Site Settings → Build & Deploy → Environment**, add these variables:

```
NEXT_PUBLIC_API_URL=https://your-hf-space-url
NEXT_PUBLIC_BACKEND_URL=https://your-hf-space-url
NEXT_PUBLIC_BETTER_AUTH_SECRET=[your-32-character-secret]
NODE_ENV=production
```

---

## 📋 Database Setup Guide

### Option 1: Neon PostgreSQL (Recommended for Production)

```bash
# 1. Go to https://neon.tech
# 2. Sign up / Sign in
# 3. Create new project
# 4. Select PostgreSQL version
# 5. Get connection string

# Connection string format:
# postgresql+psycopg://user:password@host/database

# Test connection:
psql postgresql://user:password@host/database

# For async (FastAPI):
# postgresql+psycopg://user:password@host/database
```

### Option 2: Local PostgreSQL (Development)

```bash
# macOS
brew install postgresql
brew services start postgresql

# Linux
sudo apt-get install postgresql
sudo systemctl start postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/

# Create database
createdb todo_db

# Connection string:
# postgresql://postgres:postgres@localhost:5432/todo_db
```

### Initialize Database

```bash
cd backend

# If you want to manually init:
python << 'EOF'
import asyncio
from src.database import init_db
asyncio.run(init_db())
EOF

# Or it happens automatically on app startup
```

---

## 🔐 Secrets Management

### Generating Strong Secrets

```bash
# Method 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 2: OpenSSL
openssl rand -base64 32

# Method 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Best Practices

✅ **DO:**
- Generate secrets outside of code
- Store in platform secrets manager
- Use 32+ character secrets for JWT
- Rotate secrets periodically
- Use different secrets for each environment

❌ **DON'T:**
- Commit `.env` files to git
- Share secrets via chat/email
- Use same secret for prod and dev
- Commit secrets in commit messages
- Log secrets in error messages

---

## 🧪 Testing Variables

### Unit Test Environment

```bash
# For running unit tests
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/todo_test
export BETTER_AUTH_SECRET=test-secret-at-least-32-characters-for-tests
export ENVIRONMENT=testing
export DEBUG=true

# Run tests
python -m pytest tests/
```

### Integration Test Environment

```bash
# For integration tests with full stack
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/todo_integration
export BETTER_AUTH_SECRET=integration-test-secret-at-least-32-characters
export ENVIRONMENT=testing
export DEBUG=false

# Run integration tests
python -m pytest tests/integration/ -v
```

---

## 🔄 Environment Variable Reference

### Backend Variables

| Variable | Required | Development | Production | Notes |
|----------|----------|-------------|------------|-------|
| `DATABASE_URL` | ✅ | Local DB | Neon PostgreSQL | Use async driver (psycopg) |
| `BETTER_AUTH_SECRET` | ✅ | 32+ chars | 32+ chars | Generate securely |
| `JWT_EXPIRY` | ❌ | 86400 | 86400 | Seconds (24 hours) |
| `JWT_ALGORITHM` | ❌ | HS256 | HS256 | Don't change |
| `ENVIRONMENT` | ❌ | development | production | Affects logging |
| `DEBUG` | ❌ | true | false | Critical for security |
| `CORS_ORIGINS` | ✅ | localhost | Your domain | Comma-separated URLs |
| `API_TITLE` | ❌ | Todo API | TaskFlow API | Display name |
| `API_VERSION` | ❌ | 0.1.0 | 2.0.0 | Semantic versioning |

### Frontend Variables

| Variable | Required | Development | Production | Notes |
|----------|----------|-------------|------------|-------|
| `NEXT_PUBLIC_API_URL` | ✅ | localhost:8000 | HF Space URL | Backend URL |
| `NEXT_PUBLIC_BACKEND_URL` | ✅ | localhost:8000 | HF Space URL | Same as above |
| `NEXT_PUBLIC_BETTER_AUTH_SECRET` | ✅ | 32+ chars | 32+ chars | For client validation |
| `NODE_ENV` | ❌ | development | production | Next.js environment |

---

## ✅ Verification Checklist

### Backend Verification

```bash
# Check backend starts
cd backend
python -c "from src.config import get_settings; s = get_settings(); print('Config loaded successfully')"

# Check database connection
python << 'EOF'
import asyncio
from src.database import engine
async def test():
    async with engine.begin() as conn:
        result = await conn.execute("SELECT 1")
        print("Database connection works!")
asyncio.run(test())
EOF

# Check imports
python -c "from src.main import app; print('App loaded successfully')"
```

### Frontend Verification

```bash
# Check environment variables
cd frontend
npm run build

# Check environment is set
echo $NEXT_PUBLIC_API_URL
echo $NEXT_PUBLIC_BACKEND_URL
```

### Production Verification

After deployment, test these:

```bash
# Backend health
curl https://your-space-url/health

# Frontend loads
curl https://your-netlify-site.netlify.app

# Can signup
curl -X POST https://your-space-url/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234","first_name":"Test","last_name":"User"}'

# Can chat
curl -X POST https://your-space-url/api/your-user-id/chat \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{"message":"show my tasks"}'
```

---

## 📚 Resources

- [Neon PostgreSQL Docs](https://neon.tech/docs)
- [Hugging Face Spaces Docs](https://huggingface.co/docs/hub/spaces)
- [Netlify Docs](https://docs.netlify.com)
- [FastAPI Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)

---

**Last Updated:** 2026-01-16
**Version:** 1.0.0
**Status:** Production Ready ✅

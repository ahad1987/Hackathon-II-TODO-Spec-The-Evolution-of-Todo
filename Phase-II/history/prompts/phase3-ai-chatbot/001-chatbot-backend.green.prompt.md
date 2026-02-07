---
id: 001
title: Phase III AI Chatbot - Backend Service Development
stage: green
date: 2026-01-17
surface: agent
model: claude
feature: phase3-ai-chatbot
branch: hf-backend-only
user: Ahad
command: chat
labels: ["phase3", "ai-chatbot", "backend", "mcp-tools", "huggingface", "anthropic"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/chatbot/__init__.py
  - backend/src/chatbot/api/__init__.py
  - backend/src/chatbot/api/dependencies.py
  - backend/src/chatbot/api/routes/__init__.py
  - backend/src/chatbot/api/routes/chat.py
  - backend/src/chatbot/config/__init__.py
  - backend/src/chatbot/config/cors.py
  - backend/src/chatbot/mcp/__init__.py
  - backend/src/chatbot/mcp/server.py
  - backend/src/chatbot/mcp/error_handler.py
  - backend/src/chatbot/mcp/validators.py
  - backend/src/chatbot/mcp/tools/__init__.py
  - backend/src/chatbot/mcp/tools/add_task.py
  - backend/src/chatbot/mcp/tools/complete_task.py
  - backend/src/chatbot/mcp/tools/delete_task.py
  - backend/src/chatbot/mcp/tools/list_tasks.py
  - backend/src/chatbot/mcp/tools/update_task.py
  - backend/src/chatbot/models/__init__.py
  - backend/src/chatbot/models/conversation.py
  - backend/src/chatbot/models/message.py
  - backend/src/chatbot/services/__init__.py
  - backend/src/chatbot/services/agent_service.py
  - backend/src/chatbot/services/conversation_service.py
tests:
  - API endpoint testing with curl
  - Chatbot conversation testing
  - MCP tool execution testing
---

## Prompt

Create an AI-powered chatbot backend service that integrates with the existing todo web application. The chatbot should:
- Use Claude/Anthropic API for natural language understanding
- Implement MCP (Model Context Protocol) tools for task operations
- Support conversation history and context
- Authenticate users via JWT tokens
- Provide CRUD operations for tasks through natural language

## Response snapshot

Implemented complete AI Chatbot backend service:

1. **Chat API Endpoint** (`/api/v1/chat`):
   - POST endpoint accepting user messages
   - JWT authentication required
   - Returns AI response with tool call indicators
   - Conversation ID tracking for context

2. **Agent Service** (`agent_service.py`):
   - Intent detection from natural language
   - Tool selection and execution
   - Response generation with Claude API
   - Task matching algorithm for accurate operations

3. **MCP Tools Implementation**:
   - `add_task`: Create new tasks from natural language
   - `complete_task`: Mark tasks as done
   - `delete_task`: Remove tasks
   - `update_task`: Modify task details
   - `list_tasks`: Retrieve user's tasks

4. **Conversation Management**:
   - Conversation model with message history
   - Message model for user/assistant messages
   - Context preservation across turns

5. **Security**:
   - JWT token validation
   - User isolation (users can only access their own tasks)
   - Input validation and sanitization

## Outcome

- ✅ Impact: Fully functional AI chatbot for task management
- 🧪 Tests: API testing PASS, conversation flow PASS
- 📁 Files: 23 backend chatbot files
- 🔁 Next prompts: Frontend chatbot widget integration
- 🧠 Reflection: MCP tool pattern provides clean separation of concerns

## Evaluation notes (flywheel)

- Failure modes observed: Initial Hugging Face deployment issues (CORS, environment variables)
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add conversation persistence to database

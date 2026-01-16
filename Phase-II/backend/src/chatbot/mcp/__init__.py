"""
Phase-III MCP (Model Context Protocol) module.

Implements the Model Context Protocol server for AI chatbot tools.
Provides stateless tools for task CRUD operations that are invoked by the OpenAI Agent.

MCP specification: https://modelcontextprotocol.io

Tools provided:
1. add_task - Create a new task (title, description required)
2. list_tasks - List all user's tasks (with optional filters)
3. update_task - Update task (title, description, completion status)
4. complete_task - Mark task as complete
5. delete_task - Delete a task

Design principles:
- All tools are stateless (no in-memory caching, all DB queries fresh)
- All tools enforce user isolation (WHERE user_id = :user_id)
- All tools return structured responses (JSON-compatible)
- All tools include error handling (never crash, always return meaningful errors)
- All tools validate inputs (prevent injection, invalid states)

Integration with Agent:
- Agent uses MCP to discover available tools
- Agent calls tools with user's intent + context
- Agent receives tool results and formats response to user
- No direct database writes - all mutations go through MCP tools
"""

from src.chatbot.mcp.server import MCPServer
from src.chatbot.mcp.validators import MCPInputValidator
from src.chatbot.mcp.error_handler import MCPErrorHandler

__all__ = ["MCPServer", "MCPInputValidator", "MCPErrorHandler"]

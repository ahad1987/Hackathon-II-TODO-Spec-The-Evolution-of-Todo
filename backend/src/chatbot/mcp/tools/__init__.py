"""
MCP Tools for Phase-III AI Chatbot.

Provides stateless tools for task management.
All tools enforce user isolation and input validation.

Tools:
1. add_task - Create a new task
2. list_tasks - List all user's tasks
3. update_task - Update task details
4. complete_task - Mark task as done
5. delete_task - Delete a task

Tool execution model:
- Each tool is a pure function (no side effects except DB)
- All tools receive user_id from JWT token (enforced by caller)
- All tools return structured responses (never raise exceptions)
- All tools are idempotent where possible
"""

from src.chatbot.mcp.tools.add_task import add_task_tool
from src.chatbot.mcp.tools.list_tasks import list_tasks_tool
from src.chatbot.mcp.tools.update_task import update_task_tool
from src.chatbot.mcp.tools.complete_task import complete_task_tool
from src.chatbot.mcp.tools.delete_task import delete_task_tool

__all__ = [
    "add_task_tool",
    "list_tasks_tool",
    "update_task_tool",
    "complete_task_tool",
    "delete_task_tool",
]

# Tool definitions for MCP server registration
AVAILABLE_TOOLS = [
    {
        "name": "add_task",
        "description": "Create a new task. Returns the newly created task with ID, timestamps, and status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title (required, 1-255 characters)"
                },
                "description": {
                    "type": "string",
                    "description": "Task description (optional, max 5000 characters)"
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "list_tasks",
        "description": "List all tasks for the current user. Returns array of tasks with IDs, titles, and completion status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "completed_only": {
                    "type": "boolean",
                    "description": "Filter to completed tasks only (optional, default false)"
                }
            },
            "required": []
        }
    },
    {
        "name": "update_task",
        "description": "Update a task's title and/or description. Returns the updated task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of task to update (required)"
                },
                "title": {
                    "type": "string",
                    "description": "New title (optional, 1-255 characters)"
                },
                "description": {
                    "type": "string",
                    "description": "New description (optional, max 5000 characters)"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a task as complete. Returns the updated task with completion status and timestamp.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of task to complete (required)"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "delete_task",
        "description": "Delete a task permanently. Returns success confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of task to delete (required)"
                }
            },
            "required": ["task_id"]
        }
    }
]

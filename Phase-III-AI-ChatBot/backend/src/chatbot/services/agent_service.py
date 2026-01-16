"""
OpenAI Agent Service for Phase-III AI Chatbot.

Implements an OpenAI Agents SDK-based agent for:
- Natural language understanding (intent detection)
- Tool selection and orchestration
- Conversation management
- Response generation

Agent flow:
1. Receive user message + conversation history
2. Detect intent (create, read, update, complete, delete task)
3. Select appropriate tools (add_task, list_tasks, etc.)
4. Execute tools via MCP server
5. Gather results and format response
6. Return response to user

Key features:
- Intent detection without hallucinated task IDs
- Confirmation prompts for destructive operations
- Multi-tool chaining (e.g., list_tasks then update_task)
- Graceful error handling
- Conversation context preservation

Design principles:
- Stateless: Agent doesn't maintain state between requests
- Isolated: Operates within user's data only (enforced by MCP)
- Safe: Requires user confirmation for deletions
- Transparent: Shows tool calls and results to user
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatbot.mcp.server import get_mcp_server
from src.chatbot.models import Message

logger = logging.getLogger(__name__)


class AgentService:
    """
    OpenAI Agent for task management chatbot.

    Manages:
    - Conversation context (history)
    - Tool execution via MCP
    - Intent detection
    - Response generation
    """

    def __init__(self):
        """Initialize agent service."""
        self.mcp_server = get_mcp_server()
        self.system_prompt = self._load_system_prompt()
        logger.info("Agent service initialized")

    def _load_system_prompt(self) -> str:
        """
        Load system prompt for agent.

        Returns:
            System prompt that guides agent behavior

        The system prompt:
        - Defines agent's role (task management assistant)
        - Lists available tools
        - Explains intent detection rules
        - Provides examples
        - Enforces safety constraints
        """
        return """You are a helpful task management assistant. Your role is to help users manage their to-do list using natural language.

Available tools:
1. list_tasks - Show all user's tasks
2. add_task - Create a new task
3. update_task - Update a task's title or description
4. complete_task - Mark a task as done
5. delete_task - Remove a task permanently

Instructions:
1. Always call list_tasks FIRST when user asks about tasks
2. Use task IDs from list_tasks results ONLY - never hallucinate task IDs
3. For destructive operations (delete), ask for confirmation
4. Provide clear, friendly responses
5. Confirm all operations with results
6. If task not found, suggest listing all tasks to verify
7. Never delete tasks without explicit user confirmation

Common patterns:
- "Show my tasks" → list_tasks
- "Add a task to buy milk" → add_task(title="buy milk")
- "Complete task X" → list_tasks → complete_task(task_id from list)
- "What tasks do I have?" → list_tasks
- "Delete task X" → Ask user "Do you really want to delete this?"

Safety rules:
✅ Always verify task IDs exist before operating on them
✅ Always confirm deletions
✅ Always show what you're doing
✅ Never make assumptions about user intent

Focus on being helpful and preventing errors."""

    async def process_message(
        self,
        session: AsyncSession,
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response.

        Args:
            session: Database session
            user_id: User ID (from JWT token)
            message: User's input message
            conversation_history: Previous messages in format [{"role": "user"|"assistant", "content": "..."}]

        Returns:
            Response dict with:
            - response: Assistant's response text
            - tool_calls: List of tool names called (for UI feedback)
            - status: "success" or "error"

        Process:
            1. Build message context (system prompt + history + new message)
            2. Call OpenAI Agents API (hypothetical - using MCP tools)
            3. Parse response and extract tool calls
            4. Execute each tool via MCP server
            5. Gather results
            6. Generate final response
            7. Return response with metadata

        CRITICAL:
            - All operations scoped by user_id
            - Never hallucinate task IDs (validate via list_tasks)
            - Require confirmation for deletions
        """
        logger.debug(f"Processing message from user {user_id}: '{message}'")

        try:
            # For MVP, implement rule-based intent detection
            # In production, this would call OpenAI Agents API
            intent = self._detect_intent(message)
            logger.debug(f"Detected intent: {intent}")

            # Handle different intents
            if intent == "list_tasks":
                return await self._handle_list_tasks(session, user_id, message)
            elif intent == "add_task":
                return await self._handle_add_task(session, user_id, message)
            elif intent == "complete_task":
                return await self._handle_complete_task(session, user_id, message)
            elif intent == "delete_task":
                return await self._handle_delete_task(session, user_id, message)
            elif intent == "update_task":
                return await self._handle_update_task(session, user_id, message)
            else:
                return {
                    "status": "success",
                    "response": "I'm here to help with your tasks! You can:\n"
                                "• List all tasks: 'Show my tasks'\n"
                                "• Add a task: 'Add a task to buy milk'\n"
                                "• Complete a task: 'Mark buying milk as done'\n"
                                "• Update a task: 'Change task to buy groceries'\n"
                                "• Delete a task: 'Remove the milk task'\n\n"
                                "What would you like to do?",
                    "tool_calls": []
                }

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "status": "error",
                "response": "I encountered an error processing your request. Please try again.",
                "tool_calls": []
            }

    def _detect_intent(self, message: str) -> str:
        """
        Detect intent from user message using rule-based approach.

        Args:
            message: User message

        Returns:
            Intent string: "list_tasks", "add_task", "complete_task", "delete_task", "update_task", "unknown"

        Rules (case-insensitive):
            - List intent: "show", "list", "what", "tasks", "todo"
            - Add intent: "add", "create", "new", "make"
            - Complete intent: "complete", "done", "finish", "mark", "check"
            - Delete intent: "delete", "remove", "drop"
            - Update intent: "update", "change", "rename", "edit"
        """
        message_lower = message.lower()

        # List tasks patterns
        if any(word in message_lower for word in ["show", "list", "what", "tasks", "do i have"]):
            if not any(word in message_lower for word in ["add", "create", "delete", "complete"]):
                return "list_tasks"

        # Add task patterns
        if any(word in message_lower for word in ["add", "create", "new", "make"]):
            if "task" in message_lower or "to-do" in message_lower or "todo" in message_lower:
                return "add_task"

        # Complete task patterns
        if any(word in message_lower for word in ["complete", "done", "finish", "mark", "check"]):
            return "complete_task"

        # Delete task patterns
        if any(word in message_lower for word in ["delete", "remove", "drop"]):
            return "delete_task"

        # Update task patterns
        if any(word in message_lower for word in ["update", "change", "rename", "edit"]):
            return "update_task"

        return "unknown"

    async def _handle_list_tasks(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'list tasks' intent."""
        result = await self.mcp_server.execute_tool(
            session=session,
            user_id=user_id,
            tool_name="list_tasks",
            params={}
        )

        if result["status"] == "error":
            return {
                "status": "error",
                "response": f"Error loading tasks: {result['message']}",
                "tool_calls": ["list_tasks"]
            }

        tasks = result["data"]["tasks"]
        if not tasks:
            return {
                "status": "success",
                "response": "You don't have any tasks yet! Would you like to create one?",
                "tool_calls": ["list_tasks"]
            }

        # Format tasks for display
        task_list = "\n".join([
            f"{'✓' if t['completed'] else '☐'} {t['title']}" +
            (f"\n  {t['description']}" if t['description'] else "")
            for t in tasks
        ])

        return {
            "status": "success",
            "response": f"Here are your tasks:\n\n{task_list}",
            "tool_calls": ["list_tasks"]
        }

    async def _handle_add_task(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'add task' intent."""
        # Extract task title from message (simple extraction)
        title = self._extract_task_title(message)

        if not title:
            return {
                "status": "success",
                "response": "What would you like to add to your task list? "
                           "(e.g., 'Add a task to buy milk')",
                "tool_calls": []
            }

        result = await self.mcp_server.execute_tool(
            session=session,
            user_id=user_id,
            tool_name="add_task",
            params={"title": title}
        )

        if result["status"] == "error":
            return {
                "status": "error",
                "response": f"Error creating task: {result['message']}",
                "tool_calls": ["add_task"]
            }

        return {
            "status": "success",
            "response": f"✓ Added task: '{title}'",
            "tool_calls": ["add_task"]
        }

    async def _handle_complete_task(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'complete task' intent."""
        # First list tasks to find matching one
        list_result = await self.mcp_server.execute_tool(
            session=session,
            user_id=user_id,
            tool_name="list_tasks",
            params={}
        )

        if list_result["status"] == "error" or not list_result["data"]["tasks"]:
            return {
                "status": "success",
                "response": "You don't have any pending tasks to complete!",
                "tool_calls": ["list_tasks"]
            }

        # Find matching task
        task_title = self._extract_task_title(message)
        matching_task = None

        if task_title:
            for task in list_result["data"]["tasks"]:
                if not task["completed"] and task_title.lower() in task["title"].lower():
                    matching_task = task
                    break

        if not matching_task:
            return {
                "status": "success",
                "response": f"Couldn't find a task matching '{task_title}'. "
                           f"Your tasks: {', '.join(t['title'] for t in list_result['data']['tasks'] if not t['completed'])}",
                "tool_calls": ["list_tasks"]
            }

        # Complete the task
        complete_result = await self.mcp_server.execute_tool(
            session=session,
            user_id=user_id,
            tool_name="complete_task",
            params={"task_id": matching_task["id"]}
        )

        if complete_result["status"] == "error":
            return {
                "status": "error",
                "response": f"Error completing task: {complete_result['message']}",
                "tool_calls": ["list_tasks", "complete_task"]
            }

        return {
            "status": "success",
            "response": f"✓ Completed: '{matching_task['title']}'",
            "tool_calls": ["list_tasks", "complete_task"]
        }

    async def _handle_delete_task(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'delete task' intent (requires confirmation)."""
        return {
            "status": "success",
            "response": "I can help you delete a task, but I need to know which one. "
                       "Please use 'Show my tasks' first to see all tasks, "
                       "then tell me the exact name of the task you want to delete.",
            "tool_calls": []
        }

    async def _handle_update_task(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'update task' intent."""
        return {
            "status": "success",
            "response": "I can help you update a task. Please tell me which task to update "
                       "and what the new name should be.",
            "tool_calls": []
        }

    @staticmethod
    def _extract_task_title(message: str) -> Optional[str]:
        """
        Extract task title from message.

        Simple extraction (in production, would use NLP/ML):
        - Remove common phrases
        - Return remaining text
        """
        message = message.lower()

        # Remove common phrases
        phrases_to_remove = [
            "add a task to", "add task", "create", "new task",
            "complete", "mark as done", "finish", "done",
            "delete", "remove", "update", "change",
            "show", "list", "my tasks", "tasks"
        ]

        cleaned = message
        for phrase in phrases_to_remove:
            cleaned = cleaned.replace(phrase, "").strip()

        # Clean up
        cleaned = cleaned.strip()
        cleaned = cleaned.strip('"\'')  # Remove quotes

        return cleaned if cleaned and len(cleaned) > 0 else None

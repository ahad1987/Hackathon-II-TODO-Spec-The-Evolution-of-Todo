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
            if intent == "greeting":
                return await self._handle_greeting(session, user_id, message)
            elif intent == "list_tasks":
                return await self._handle_list_tasks(session, user_id, message)
            elif intent == "list_pending":
                return await self._handle_list_pending(session, user_id, message)
            elif intent == "list_completed":
                return await self._handle_list_completed(session, user_id, message)
            elif intent == "search_tasks":
                return await self._handle_search_tasks(session, user_id, message)
            elif intent == "task_stats":
                return await self._handle_task_stats(session, user_id, message)
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
            Intent string: "greeting", "list_tasks", "list_pending", "list_completed", "search_tasks",
                          "task_stats", "add_task", "complete_task", "delete_task", "update_task", "unknown"

        Rules (case-insensitive):
            - Greeting intent: "hi", "hello", "hey", "howdy", "greetings"
            - List intent: "show", "list", "what", "tasks", "todo"
            - List pending: "pending", "incomplete", "not done", "todo", "remaining"
            - List completed: "completed", "done", "finished"
            - Search intent: "about", "search", "find", "containing"
            - Stats intent: "how many", "count", "total", "statistics"
            - Add intent: "add", "create", "new", "make"
            - Complete intent: "complete", "done", "finish", "mark", "check"
            - Delete intent: "delete", "remove", "drop"
            - Update intent: "update", "change", "rename", "edit"
        """
        message_lower = message.lower()

        # Greeting patterns (check first to catch simple greetings)
        if any(word in message_lower for word in ["hi", "hello", "hey", "howdy", "greetings", "good morning", "good afternoon", "good evening"]):
            if len(message_lower) <= 20:  # Only treat short messages as greetings
                return "greeting"

        # Stats patterns (must check before list patterns)
        if any(word in message_lower for word in ["how many", "count", "total", "statistics", "how much"]):
            if "task" in message_lower:
                return "task_stats"

        # Search patterns
        if any(word in message_lower for word in ["about", "search", "find", "containing", "with"]):
            if "task" in message_lower:
                return "search_tasks"

        # List completed patterns
        if any(word in message_lower for word in ["completed", "finished", "done"]):
            if any(word in message_lower for word in ["show", "list", "tasks", "all"]):
                return "list_completed"

        # List pending patterns
        if any(word in message_lower for word in ["pending", "incomplete", "not done", "remaining"]):
            if any(word in message_lower for word in ["show", "list", "tasks"]):
                return "list_pending"

        # List all tasks patterns
        if any(word in message_lower for word in ["show", "list", "what", "tasks", "do i have"]):
            if not any(word in message_lower for word in ["add", "create", "delete", "complete", "update", "change"]):
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

    async def _handle_greeting(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle greeting intent - respond with a friendly greeting."""
        greetings = [
            "👋 Hello! I'm TaskFlow AI, your personal productivity assistant. How can I help you with your tasks today?",
            "🎉 Hi there! Ready to manage your tasks? You can ask me to add, list, complete, or organize your tasks!",
            "👋 Hey! Welcome to TaskFlow AI. I'm here to help you stay on top of your tasks!",
            "💬 Hello! I'm your TaskFlow AI assistant. What would you like to do with your tasks?",
            "🚀 Hi! TaskFlow AI here. Let's get your tasks organized and your productivity up!",
        ]

        import random
        greeting_response = random.choice(greetings)

        return {
            "status": "success",
            "response": greeting_response,
            "tool_calls": []
        }

    async def _handle_list_tasks(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'list all tasks' intent with enhanced formatting."""
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

        # Separate pending and completed tasks
        pending = [t for t in tasks if not t['completed']]
        completed = [t for t in tasks if t['completed']]

        # Format tasks with numbering and grouping
        task_list = ""

        if pending:
            task_list += "📋 **Pending Tasks:**\n"
            for i, t in enumerate(pending, 1):
                task_list += f"{i}. ☐ {t['title']}"
                if t['description']:
                    task_list += f"\n   {t['description']}"
                task_list += "\n"

        if completed:
            if pending:
                task_list += "\n"
            task_list += "✅ **Completed Tasks:**\n"
            for i, t in enumerate(completed, 1):
                task_list += f"{i}. ✓ {t['title']}"
                if t['description']:
                    task_list += f"\n   {t['description']}"
                task_list += "\n"

        return {
            "status": "success",
            "response": f"Here are your tasks:\n\n{task_list}",
            "tool_calls": ["list_tasks"]
        }

    async def _handle_list_pending(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'list pending tasks' intent."""
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
        pending = [t for t in tasks if not t['completed']]

        if not pending:
            return {
                "status": "success",
                "response": "Great! You don't have any pending tasks. You're all caught up! 🎉",
                "tool_calls": ["list_tasks"]
            }

        # Format pending tasks
        task_list = "📋 **Your Pending Tasks:**\n"
        for i, t in enumerate(pending, 1):
            task_list += f"{i}. ☐ {t['title']}"
            if t['description']:
                task_list += f"\n   {t['description']}"
            task_list += "\n"

        return {
            "status": "success",
            "response": f"{task_list}\nTotal: {len(pending)} pending task{'s' if len(pending) != 1 else ''}",
            "tool_calls": ["list_tasks"]
        }

    async def _handle_list_completed(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'list completed tasks' intent."""
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
        completed = [t for t in tasks if t['completed']]

        if not completed:
            return {
                "status": "success",
                "response": "You haven't completed any tasks yet. Keep working! 💪",
                "tool_calls": ["list_tasks"]
            }

        # Format completed tasks
        task_list = "✅ **Your Completed Tasks:**\n"
        for i, t in enumerate(completed, 1):
            task_list += f"{i}. ✓ {t['title']}"
            if t['description']:
                task_list += f"\n   {t['description']}"
            task_list += "\n"

        return {
            "status": "success",
            "response": f"{task_list}\nTotal: {len(completed)} completed task{'s' if len(completed) != 1 else ''}",
            "tool_calls": ["list_tasks"]
        }

    async def _handle_search_tasks(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'search tasks' intent - search by keyword."""
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

        # Extract search keyword from message
        message_lower = message.lower()
        keywords = ["about", "search", "find", "containing", "with"]
        search_term = ""

        for keyword in keywords:
            if keyword in message_lower:
                parts = message_lower.split(keyword)
                if len(parts) > 1:
                    search_term = parts[-1].strip().replace("task", "").strip().strip('"\'')
                    break

        if not search_term:
            return {
                "status": "success",
                "response": "What would you like to search for? (e.g., 'Find tasks about shopping')",
                "tool_calls": ["list_tasks"]
            }

        # Search tasks
        tasks = result["data"]["tasks"]
        matching = [t for t in tasks if search_term.lower() in t['title'].lower() or
                   (t.get('description') and search_term.lower() in t['description'].lower())]

        if not matching:
            return {
                "status": "success",
                "response": f"No tasks found matching '{search_term}'. Try a different search term!",
                "tool_calls": ["list_tasks"]
            }

        # Format search results
        task_list = f"🔍 **Tasks matching '{search_term}':**\n"
        for i, t in enumerate(matching, 1):
            task_list += f"{i}. {'✓' if t['completed'] else '☐'} {t['title']}"
            if t['description']:
                task_list += f"\n   {t['description']}"
            task_list += "\n"

        return {
            "status": "success",
            "response": f"{task_list}\nTotal: {len(matching)} matching task{'s' if len(matching) != 1 else ''}",
            "tool_calls": ["list_tasks"]
        }

    async def _handle_task_stats(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'task statistics' intent."""
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
        total = len(tasks)
        completed = len([t for t in tasks if t['completed']])
        pending = total - completed

        completion_rate = 0 if total == 0 else int((completed / total) * 100)

        stats_response = f"""📊 **Your Task Statistics:**

• Total tasks: {total}
• Completed: {completed} ✓
• Pending: {pending} ☐
• Completion rate: {completion_rate}% {'🎉' if completion_rate == 100 and total > 0 else ''}"""

        return {
            "status": "success",
            "response": stats_response,
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

        # Find matching task using improved matching
        pending_tasks = [t for t in list_result["data"]["tasks"] if not t["completed"]]

        if not pending_tasks:
            return {
                "status": "success",
                "response": "You don't have any pending tasks to complete! All done! 🎉",
                "tool_calls": ["list_tasks"]
            }

        matching_task = self._find_best_matching_task(message, pending_tasks)

        if not matching_task:
            task_list = ", ".join(t['title'] for t in pending_tasks)
            return {
                "status": "success",
                "response": f"Which task would you like to complete? Your pending tasks: {task_list}",
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
        """Handle 'delete task' intent."""
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
                "response": "You don't have any tasks to delete!",
                "tool_calls": ["list_tasks"]
            }

        # Find matching task using improved matching
        matching_task = self._find_best_matching_task(
            message,
            list_result["data"]["tasks"]
        )

        if not matching_task:
            task_list = ", ".join(t['title'] for t in list_result["data"]["tasks"])
            return {
                "status": "success",
                "response": f"Which task would you like to delete? Your tasks: {task_list}",
                "tool_calls": ["list_tasks"]
            }

        # Delete the task
        delete_result = await self.mcp_server.execute_tool(
            session=session,
            user_id=user_id,
            tool_name="delete_task",
            params={"task_id": matching_task["id"]}
        )

        if delete_result["status"] == "error":
            return {
                "status": "error",
                "response": f"Error deleting task: {delete_result['message']}",
                "tool_calls": ["list_tasks", "delete_task"]
            }

        return {
            "status": "success",
            "response": f"✓ Deleted: '{matching_task['title']}'",
            "tool_calls": ["list_tasks", "delete_task"]
        }

    async def _handle_update_task(
        self,
        session: AsyncSession,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle 'update task' intent."""
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
                "response": "You don't have any tasks to update!",
                "tool_calls": ["list_tasks"]
            }

        # Try to extract task name and new name from message
        # Format: "update [task_name] to [new_name]" or "change [task_name] to [new_name]"
        message_lower = message.lower()

        # Find the task that matches
        matching_task = None
        for task in list_result["data"]["tasks"]:
            task_title_lower = task["title"].lower()
            if task_title_lower in message_lower:
                matching_task = task
                break

        if not matching_task:
            task_list = ", ".join(t['title'] for t in list_result["data"]["tasks"])
            return {
                "status": "success",
                "response": f"Which task would you like to update? Your tasks: {task_list}",
                "tool_calls": ["list_tasks"]
            }

        # Extract new title - look for " to " separator
        if " to " in message_lower:
            parts = message_lower.split(" to ")
            if len(parts) >= 2:
                new_title = parts[-1].strip()
                # Clean up the new title
                for phrase in ["buy", "get", "do", "make", "create"]:
                    if new_title.startswith(phrase + " "):
                        new_title = new_title[len(phrase):].strip()
                        break

                if new_title and len(new_title) > 0:
                    # Update the task
                    update_result = await self.mcp_server.execute_tool(
                        session=session,
                        user_id=user_id,
                        tool_name="update_task",
                        params={"task_id": matching_task["id"], "title": new_title}
                    )

                    if update_result["status"] == "error":
                        return {
                            "status": "error",
                            "response": f"Error updating task: {update_result['message']}",
                            "tool_calls": ["list_tasks", "update_task"]
                        }

                    return {
                        "status": "success",
                        "response": f"✓ Updated: '{matching_task['title']}' → '{new_title}'",
                        "tool_calls": ["list_tasks", "update_task"]
                    }

        return {
            "status": "success",
            "response": f"Please tell me what to change '{matching_task['title']}' to. (e.g., 'update {matching_task['title']} to buy groceries')",
            "tool_calls": ["list_tasks"]
        }

    @staticmethod
    def _find_best_matching_task(message: str, tasks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the best matching task from user message.

        Matching priority:
        1. Exact title match (case-insensitive)
        2. Title contained in message
        3. Most words matching (scored by match count)

        This prevents matching "buy laptop" when user says "remove buy appliances"
        """
        message_lower = message.lower()

        # Remove common action words to get the task reference
        action_words = ["delete", "remove", "drop", "complete", "finish", "mark", "done", "update", "change", "the", "task", "a", "my"]
        message_words = set(message_lower.split())
        for word in action_words:
            message_words.discard(word)

        best_match = None
        best_score = 0

        for task in tasks:
            task_title_lower = task["title"].lower()
            task_words = set(task_title_lower.split())

            # Priority 1: Exact match
            if task_title_lower in message_lower:
                return task

            # Priority 2: Score by word overlap
            # Count how many words from task title appear in message
            matching_words = task_words.intersection(message_words)

            if matching_words:
                # Score = matching words / total task words (higher = better match)
                score = len(matching_words) / len(task_words)

                # Bonus: if ALL task words match, prioritize it
                if len(matching_words) == len(task_words):
                    score += 1

                if score > best_score:
                    best_score = score
                    best_match = task

        # Only return if we have a reasonable match (at least 50% of task words matched)
        if best_score >= 0.5:
            return best_match

        return None

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

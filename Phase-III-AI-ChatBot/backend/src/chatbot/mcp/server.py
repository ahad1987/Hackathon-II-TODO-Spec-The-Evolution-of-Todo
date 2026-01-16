"""
MCP Server for Phase-III AI Chatbot.

Implements the Model Context Protocol server.
Provides tool registration, discovery, and execution.

Tools exposed:
1. add_task - Create task
2. list_tasks - List user's tasks
3. update_task - Update task
4. complete_task - Mark task as complete
5. delete_task - Delete task

MCP flow:
1. Agent calls mcp_server.execute_tool(tool_name, params)
2. Server validates inputs (MCPInputValidator)
3. Server executes tool function
4. Server handles errors (MCPErrorHandler)
5. Server returns structured response
6. Agent receives response and processes for user

Tool contract:
- Input: async function(session, user_id, **params)
- Output: Dict[str, Any] with status, data, and optional message
- All tools enforce user_id isolation
- All errors are returned as structured dicts (never exceptions)
"""

import logging
from typing import Dict, Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatbot.mcp.tools import (
    add_task_tool,
    list_tasks_tool,
    update_task_tool,
    complete_task_tool,
    delete_task_tool,
)
from src.chatbot.mcp.tools import AVAILABLE_TOOLS
from src.chatbot.mcp.error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP (Model Context Protocol) Server for AI chatbot tools.

    Manages tool registration, discovery, and execution.

    Usage:
        # Initialize server
        mcp_server = MCPServer()

        # Get available tools (for agent)
        tools = mcp_server.get_tools()

        # Execute a tool
        result = await mcp_server.execute_tool(
            session=db_session,
            user_id="user-uuid",
            tool_name="add_task",
            params={"title": "Buy milk"}
        )
    """

    def __init__(self):
        """Initialize MCP server and register tools."""
        self.tools: Dict[str, Callable] = {
            "add_task": add_task_tool,
            "list_tasks": list_tasks_tool,
            "update_task": update_task_tool,
            "complete_task": complete_task_tool,
            "delete_task": delete_task_tool,
        }

        logger.info(f"MCP Server initialized with {len(self.tools)} tools")

    def get_tools(self) -> list:
        """
        Get tool definitions for agent discovery.

        Returns:
            List of tool definitions (includes name, description, input_schema)

        Used by:
            - Agent: To discover available tools
            - API: To document available tools
        """
        return AVAILABLE_TOOLS

    async def execute_tool(
        self,
        session: AsyncSession,
        user_id: str,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool with given parameters.

        Args:
            session: Database session (async)
            user_id: User ID from JWT token (enforced by caller)
            tool_name: Name of tool to execute
            params: Tool parameters (tool-specific)

        Returns:
            Response dict with status, data, and optional message
            Format: {"status": "success"|"error", "data": {...}, "message": "..."}

        Error handling:
            - Unknown tool: returns error response (no exception)
            - Invalid params: returns validation error response
            - Database errors: returns internal error response
            - Never raises exceptions (always returns structured response)

        User isolation:
            - All tools receive user_id from JWT token
            - User cannot pass different user_id in params
            - All tools enforce WHERE user_id = :user_id in queries
        """
        try:
            # Validate tool exists
            if tool_name not in self.tools:
                logger.warning(f"Unknown tool requested: {tool_name}")
                return MCPErrorHandler.handle_validation_error(
                    f"Unknown tool: {tool_name}. Available tools: {list(self.tools.keys())}"
                )

            logger.debug(f"Executing tool: {tool_name} for user {user_id}")

            # Get tool function
            tool_func = self.tools[tool_name]

            # Execute tool (includes its own error handling)
            result = await tool_func(
                session=session,
                user_id=user_id,
                **params
            )

            logger.debug(f"Tool {tool_name} completed with status: {result.get('status')}")
            return result

        except Exception as e:
            # Unexpected error (shouldn't happen if tools are well-written)
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return MCPErrorHandler.handle_unexpected_error(e)

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get input schema for a specific tool.

        Args:
            tool_name: Name of tool

        Returns:
            Tool definition with schema, or None if not found

        Used by:
            - Agent: To validate parameters before calling tool
            - API: To document tool requirements
        """
        for tool in AVAILABLE_TOOLS:
            if tool["name"] == tool_name:
                return tool
        return None


# Global MCP server instance
# Initialized once at startup
mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """
    Get or create the global MCP server instance.

    Returns:
        MCPServer instance

    Usage:
        server = get_mcp_server()
        result = await server.execute_tool(...)

    Note:
        This is called once at app startup to initialize the server.
        Subsequent calls return the same instance.
    """
    global mcp_server
    if mcp_server is None:
        mcp_server = MCPServer()
    return mcp_server

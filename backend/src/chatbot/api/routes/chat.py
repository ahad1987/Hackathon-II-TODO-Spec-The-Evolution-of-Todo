"""
Chat endpoint for Phase-III AI Chatbot.

Endpoint: POST /api/{user_id}/chat

Request:
{
  "conversation_id": "optional-uuid",  // Omit for new conversation
  "message": "user input text"          // Required
}

Response:
{
  "conversation_id": "uuid",
  "response": "assistant response text",
  "tool_calls": ["add_task", "list_tasks"],
  "status": "success" | "error"
}

Error responses:
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: user_id mismatch
- 422 Unprocessable Entity: Validation error
- 500 Internal Server Error: Database or unexpected error

Guarantees:
- Stateless: No session state retained after request
- User-scoped: All operations for authenticated user only
- Persistent: Conversation history saved to database
- Safe: All inputs validated, errors handled gracefully

Critical flow (STATELESS):
1. Receive request with JWT token + user_id + message + optional conversation_id
2. Authenticate: validate JWT token, extract user_id
3. Authorize: verify URL user_id matches token user_id
4. Load: fetch existing conversation (or create new)
5. Load history: fetch all messages for conversation from DB
6. Execute: call agent with history + new message
7. Persist: save user message and assistant response to DB
8. Release: clear all in-memory state (function returns)
9. Return: send response to client
10. ← Server memory cleared, ready for next request
"""

import logging
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.chatbot.api.dependencies import get_current_user, verify_user_ownership
from src.chatbot.services import ConversationService, AgentService
from src.chatbot.models import MessageCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""
    conversation_id: Optional[str] = Field(
        default=None,
        description="Existing conversation ID (omit to create new conversation)"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message"
    )


class ChatResponse(BaseModel):
    """Chat response model."""
    conversation_id: str = Field(description="Conversation ID")
    response: str = Field(description="Assistant response text")
    tool_calls: List[str] = Field(
        default_factory=list,
        description="List of tool names called"
    )
    status: str = Field(
        description="Response status: 'success' or 'error'"
    )


@router.post("/{user_id}/chat", response_model=ChatResponse)
async def chat(
    user_id: str,
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    authenticated_user_id: str = Depends(get_current_user)
) -> ChatResponse:
    """
    Process a chat message.

    STATELESS GUARANTEE:
    This endpoint is completely stateless:
    - No session state stored on server
    - No connection affinity required
    - Can be deployed on multiple servers
    - Server restart = zero data loss
    - Horizontal scaling enabled

    Flow:
    1. Authenticate user via JWT token
    2. Load conversation (or create new)
    3. Load conversation history from database
    4. Execute agent with context
    5. Save response to database
    6. Return response to user
    7. Clear all in-memory state

    Args:
        user_id: User ID from URL path
        request: Chat request (conversation_id, message)
        session: Database session (auto-injected)
        authenticated_user_id: User ID from JWT token (auto-injected)

    Returns:
        ChatResponse with conversation_id, assistant response, tool calls, status

    Raises:
        HTTPException: 401 (auth error), 403 (forbidden), 422 (validation), 500 (server error)

    User isolation:
        - Verified at two levels:
          1. JWT token validation (authenticated_user_id)
          2. URL path verification (user_id == authenticated_user_id)
        - All database queries filtered by user_id
        - User cannot access other users' conversations
    """
    try:
        # STEP 1: AUTHENTICATE & AUTHORIZE
        logger.info(f"Chat request from user {authenticated_user_id}")

        # Verify URL user_id matches authenticated user
        verify_user_ownership(authenticated_user_id, user_id)

        # STEP 2: LOAD OR CREATE CONVERSATION
        conversation_service = ConversationService()

        if request.conversation_id:
            # Load existing conversation
            conversation = await conversation_service.get_conversation(
                session=session,
                conversation_id=request.conversation_id,
                user_id=user_id
            )

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )

            logger.debug(f"Loaded existing conversation {conversation.id}")
        else:
            # Create new conversation
            conversation = await conversation_service.create_conversation(
                session=session,
                user_id=user_id
            )
            logger.debug(f"Created new conversation {conversation.id}")

        # STEP 3: LOAD CONVERSATION HISTORY
        history: List = await conversation_service.get_conversation_history(
            session=session,
            conversation_id=conversation.id,
            user_id=user_id
        )

        # Convert messages to format expected by agent
        conversation_context = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in history
        ]

        logger.debug(f"Loaded {len(history)} messages from conversation history")

        # STEP 4: SAVE USER MESSAGE
        user_msg = await conversation_service.append_message(
            session=session,
            conversation_id=conversation.id,
            user_id=user_id,
            role="user",
            content=request.message
        )

        logger.debug(f"Saved user message {user_msg.id}")

        # STEP 5: EXECUTE AGENT
        agent_service = AgentService()

        agent_response = await agent_service.process_message(
            session=session,
            user_id=user_id,
            message=request.message,
            conversation_history=conversation_context
        )

        if agent_response["status"] == "error":
            logger.error(f"Agent error: {agent_response['response']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing request"
            )

        # STEP 6: SAVE ASSISTANT RESPONSE
        assistant_msg = await conversation_service.append_message(
            session=session,
            conversation_id=conversation.id,
            user_id=user_id,
            role="assistant",
            content=agent_response["response"],
            tool_calls=None  # TODO: Serialize tool_calls to JSON string
        )

        logger.debug(f"Saved assistant message {assistant_msg.id}")

        # STEP 7: BUILD RESPONSE
        response = ChatResponse(
            conversation_id=conversation.id,
            response=agent_response["response"],
            tool_calls=agent_response.get("tool_calls", []),
            status="success"
        )

        logger.info(f"Chat completed for user {user_id} (conversation {conversation.id})")

        # STEP 8: RELEASE STATE (implicit - function returns)
        # All local variables go out of scope
        # All in-memory state is cleared
        # Database session is closed by dependency injection
        # Server is ready for next request

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

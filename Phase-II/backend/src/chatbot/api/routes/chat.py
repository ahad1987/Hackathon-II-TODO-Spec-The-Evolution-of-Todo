"""
Chat endpoint for AI Chatbot.

Endpoint: POST /api/v1/chat

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

User ID is extracted from JWT token (via middleware) - NOT from URL.
"""

import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.chatbot.api.dependencies import get_current_user
from src.chatbot.services import ConversationService, AgentService

logger = logging.getLogger(__name__)

# No prefix here - prefix added in main.py as /api/v1
router = APIRouter(tags=["Chat"])


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


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
) -> ChatResponse:
    """
    Process a chat message. User ID extracted from JWT token.

    Endpoint: POST /api/v1/chat
    """
    try:
        logger.info(f"Chat request from user {user_id}")

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

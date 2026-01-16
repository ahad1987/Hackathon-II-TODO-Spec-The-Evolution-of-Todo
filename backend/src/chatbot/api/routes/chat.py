"""
Chat endpoint for Phase-III AI Chatbot.
"""

import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.chatbot.api.dependencies import get_current_user, verify_user_ownership
from src.chatbot.services import ConversationService, AgentService
from src.chatbot.models import MessageCreate

logger = logging.getLogger(__name__)

# Router WITHOUT prefix - prefix will be added in main.py
router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (omit for new)")
    message: str = Field(..., min_length=1, max_length=5000, description="User message")


class ChatResponse(BaseModel):
    """Chat response model."""
    conversation_id: str = Field(..., description="Conversation ID")
    response: str = Field(..., description="Assistant response")
    tool_calls: List[str] = Field(default_factory=list, description="Tools called")
    status: str = Field(..., description="Response status: success or error")


@router.post("/{user_id}/chat", response_model=ChatResponse)
async def chat(
    user_id: str,
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    authenticated_user_id: str = Depends(get_current_user)
) -> ChatResponse:
    """
    Send a message to the AI chatbot.
    """
    logger.info(f"Chat request from user {user_id}, authenticated as {authenticated_user_id}")
    
    # Verify user ownership
    verify_user_ownership(authenticated_user_id, user_id)
    
    conversation_service = ConversationService()
    agent_service = AgentService()
    
    try:
        # Get or create conversation
        if request.conversation_id:
            conversation = await conversation_service.get_conversation(
                session, request.conversation_id, user_id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            conversation = await conversation_service.create_conversation(session, user_id)
        
        # Get conversation history
        history = await conversation_service.get_conversation_history(
            session, conversation.id, user_id
        )
        history_dicts = [{"role": m.role, "content": m.content} for m in history]
        
        # Save user message
        await conversation_service.append_message(
            session, conversation.id, user_id, "user", request.message
        )
        
        # Process with agent
        result = await agent_service.process_message(
            session, user_id, request.message, history_dicts
        )
        
        # Save assistant response
        tool_calls_str = ",".join(result.get("tool_calls", []))
        await conversation_service.append_message(
            session, conversation.id, user_id, "assistant", 
            result["response"], tool_calls_str if tool_calls_str else None
        )
        
        return ChatResponse(
            conversation_id=conversation.id,
            response=result["response"],
            tool_calls=result.get("tool_calls", []),
            status=result.get("status", "success")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return ChatResponse(
            conversation_id=request.conversation_id or "error",
            response=f"Error: {str(e)}",
            tool_calls=[],
            status="error"
        )

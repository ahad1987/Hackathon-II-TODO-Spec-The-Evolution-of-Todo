"""
Chat endpoint for Phase-III AI Chatbot.
Supports both:
- POST /api/chat (preferred, user_id from JWT)
- POST /api/{user_id}/chat (legacy, for frontend compatibility)
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

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    message: str = Field(..., min_length=1, max_length=5000, description="User message")


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    tool_calls: List[str] = Field(default_factory=list)
    status: str


async def process_chat(user_id: str, request: ChatRequest, session: AsyncSession) -> ChatResponse:
    """Common chat processing logic."""
    logger.info(f"Processing chat for user: {user_id}")
    
    conversation_service = ConversationService()
    agent_service = AgentService()
    
    try:
        if request.conversation_id:
            conversation = await conversation_service.get_conversation(session, request.conversation_id, user_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            conversation = await conversation_service.create_conversation(session, user_id)
        
        history = await conversation_service.get_conversation_history(session, conversation.id, user_id)
        history_dicts = [{"role": m.role, "content": m.content} for m in history]
        
        await conversation_service.append_message(session, conversation.id, user_id, "user", request.message)
        
        result = await agent_service.process_message(session, user_id, request.message, history_dicts)
        
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


@router.post("/chat", response_model=ChatResponse)
async def chat_simple(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
) -> ChatResponse:
    """Chat endpoint - user_id from JWT token."""
    return await process_chat(user_id, request, session)


@router.post("/{user_id}/chat", response_model=ChatResponse)
async def chat_with_user_id(
    user_id: str,
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    authenticated_user_id: str = Depends(get_current_user)
) -> ChatResponse:
    """Chat endpoint with user_id in URL (legacy compatibility)."""
    # Verify the URL user_id matches the authenticated user
    if user_id != authenticated_user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch")
    return await process_chat(user_id, request, session)

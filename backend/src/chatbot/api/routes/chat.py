"""
Chat endpoint for AI Chatbot.
Endpoint: POST /api/v1/chat
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.chatbot.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

# Router - NO prefix here, prefix added in main.py
router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")


class ChatResponse(BaseModel):
    """Chat response model."""
    reply: str = Field(..., description="AI response")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
) -> ChatResponse:
    """
    AI Chat endpoint. User ID extracted from JWT token.
    
    Stub implementation:
    - "add task" or "add a task" -> creates task
    - Otherwise -> conversational response
    """
    logger.info(f"Chat request from user {user_id}: {request.message[:50]}...")
    
    message_lower = request.message.lower()
    
    try:
        # Simple intent detection
        if "add task" in message_lower or "add a task" in message_lower:
            # Extract task title from message
            title = extract_task_title(request.message)
            if title:
                # Create task using existing Task model
                from src.models.task import Task
                task = Task(user_id=user_id, title=title, completed=False)
                session.add(task)
                await session.commit()
                await session.refresh(task)
                return ChatResponse(
                    reply=f"Task '{title}' added successfully.",
                    conversation_id=request.conversation_id
                )
            else:
                return ChatResponse(
                    reply="What task would you like to add? Please tell me the task name.",
                    conversation_id=request.conversation_id
                )
        
        elif "list task" in message_lower or "show task" in message_lower or "my task" in message_lower:
            from src.models.task import Task
            from sqlalchemy import select
            result = await session.execute(
                select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
            )
            tasks = result.scalars().all()
            if tasks:
                task_list = "\n".join([f"- {'✓' if t.completed else '☐'} {t.title}" for t in tasks])
                return ChatResponse(
                    reply=f"Here are your tasks:\n{task_list}",
                    conversation_id=request.conversation_id
                )
            else:
                return ChatResponse(
                    reply="You don't have any tasks yet. Would you like to add one?",
                    conversation_id=request.conversation_id
                )
        
        elif "hello" in message_lower or "hi" in message_lower or "hey" in message_lower:
            return ChatResponse(
                reply="Hello! I'm your TaskFlow AI assistant. I can help you manage tasks. Try saying 'add a task to buy milk' or 'show my tasks'.",
                conversation_id=request.conversation_id
            )
        
        else:
            return ChatResponse(
                reply=f"I understand you said: '{request.message}'. I can help you add tasks, list tasks, or complete tasks. What would you like to do?",
                conversation_id=request.conversation_id
            )
            
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return ChatResponse(
            reply=f"Sorry, I encountered an error. Please try again.",
            conversation_id=request.conversation_id
        )


def extract_task_title(message: str) -> Optional[str]:
    """Extract task title from message."""
    message_lower = message.lower()
    
    # Common patterns
    patterns = [
        "add a task to ", "add task to ", "add a task ", "add task ",
        "create a task to ", "create task to ", "create a task ", "create task ",
        "new task to ", "new task "
    ]
    
    for pattern in patterns:
        if pattern in message_lower:
            idx = message_lower.find(pattern) + len(pattern)
            title = message[idx:].strip()
            # Clean up
            title = title.rstrip('.!?')
            if title:
                return title
    
    return None

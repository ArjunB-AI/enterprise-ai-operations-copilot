
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user
from backend.app.db.dependencies import get_db
from backend.app.models.ai_chat_message import AIChatMessage
from backend.app.models.ai_conversation import AIConversation
from backend.app.models.user import User
from backend.app.schemas.ai_chat import (
    AIChatMessageCreate,
    AIChatMessageResponse,
    AIConversationCreate,
    AIConversationResponse,
)


router = APIRouter(
    prefix="/ai-chat",
    tags=["AI Chat"],
)


@router.post(
    "/conversations",
    response_model=AIConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conversation_data: AIConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = AIConversation(
        user_id=current_user.id,
        title=conversation_data.title,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get(
    "/conversations",
    response_model=list[AIConversationResponse],
)
def get_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(AIConversation)
        .filter(AIConversation.user_id == current_user.id)
        .order_by(AIConversation.updated_at.desc())
        .all()
    )

    return conversations

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AIChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_message(
    conversation_id: int,
    message_data: AIChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id,
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    message = AIChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=message_data.content,
    )

    conversation.updated_at = datetime.utcnow()

    db.add(message)
    db.commit()
    db.refresh(message)

    return message

@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[AIChatMessageResponse],
)
def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id,
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = (
        db.query(AIChatMessage)
        .filter(AIChatMessage.conversation_id == conversation_id)
        .order_by(AIChatMessage.created_at.asc())
        .all()
    )

    return messages

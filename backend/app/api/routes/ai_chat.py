
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user
from backend.app.db.dependencies import get_db, get_vector_db
from backend.app.models.ai_chat_message import AIChatMessage
from backend.app.models.ai_conversation import AIConversation
from backend.app.models.user import User
from backend.app.schemas.ai_chat import (
    AIChatMessageCreate,
    AIChatMessageResponse,
    AIConversationCreate,
    AIConversationResponse,
    AIChatTurnResponse,
)

from backend.app.services.rag_service import generate_rag_response


logger = logging.getLogger(__name__)


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
    logger.info(
        "Creating AI conversation | user_id=%s",
        current_user.id,
    )

    conversation = AIConversation(
        user_id=current_user.id,
        title=conversation_data.title,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    logger.info(
        "AI conversation created | conversation_id=%s | user_id=%s",
        conversation.id,
        current_user.id,
    )

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

    logger.info(
        "AI conversations retrieved | user_id=%s | count=%s",
        current_user.id,
        len(conversations),
    )

    return conversations


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AIChatTurnResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_message(
    conversation_id: int,
    message_data: AIChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    vector_db: Session = Depends(get_vector_db),
):
    logger.info(
        "AI chat request started | conversation_id=%s | user_id=%s",
        conversation_id,
        current_user.id,
    )

    # Step 1: Verify conversation ownership.
    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id,
        )
        .first()
    )

    if conversation is None:
        logger.warning(
            "AI chat conversation not found or access denied | conversation_id=%s | user_id=%s",
            conversation_id,
            current_user.id,
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    logger.info(
        "Conversation ownership verified | conversation_id=%s | user_id=%s",
        conversation_id,
        current_user.id,
    )

    # Step 2: Save the employee's message.
    user_message = AIChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=message_data.content,
    )

    conversation.updated_at = datetime.utcnow()
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    logger.info(
        "Employee message saved | message_id=%s | conversation_id=%s",
        user_message.id,
        conversation_id,
    )

    # Step 3: Generate an answer using RAG.
    try:
        logger.info(
            "Calling RAG service | conversation_id=%s",
            conversation_id,
        )

        rag_result = generate_rag_response(
            query=message_data.content,
            db=db,
            vector_db=vector_db,
        )

        logger.info(
            "RAG service completed | conversation_id=%s | source_count=%s",
            conversation_id,
            len(rag_result["sources"]),
        )

    except Exception:
        logger.exception(
            "AI response generation failed | conversation_id=%s | user_id=%s",
            conversation_id,
            current_user.id,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate an AI response. Please try again.",
        )

    # Step 4: Save the assistant's response.
    assistant_message = AIChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=rag_result["answer"],
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    logger.info(
        "Assistant message saved | message_id=%s | conversation_id=%s",
        assistant_message.id,
        conversation_id,
    )

    # Step 5: Return both messages and document sources.
    logger.info(
        "AI chat request completed | conversation_id=%s",
        conversation_id,
    )

    return {
        "user_message": user_message,
        "assistant_message": assistant_message,
        "sources": rag_result["sources"],
    }


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
        logger.warning(
            "Message history access denied | conversation_id=%s | user_id=%s",
            conversation_id,
            current_user.id,
        )

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

    logger.info(
        "Conversation messages retrieved | conversation_id=%s | count=%s",
        conversation_id,
        len(messages),
    )

    return messages

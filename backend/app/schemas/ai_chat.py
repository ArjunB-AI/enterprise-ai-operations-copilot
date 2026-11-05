
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


MessageRole = Literal["user", "assistant"]


class AIConversationCreate(BaseModel):
    title: str = "New conversation"


class AIConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class AIChatMessageCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message content cannot be empty")

        return value.strip()


class AIChatMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

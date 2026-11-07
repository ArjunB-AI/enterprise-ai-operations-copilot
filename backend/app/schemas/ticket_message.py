from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TicketMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Message content cannot be empty.")

        return value


class TicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender_id: int
    sender_name: str
    sender_role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
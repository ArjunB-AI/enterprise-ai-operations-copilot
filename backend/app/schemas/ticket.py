from datetime import datetime
from typing import Literal

from pydantic import BaseModel


TicketType = Literal["incident", "request", "asset", "onboarding"]
TicketStatus = Literal["open", "in_progress", "resolved", "closed"]
TicketPriority = Literal["low", "medium", "high", "critical"]


class TicketCreate(BaseModel):
    ticket_type: TicketType
    title: str
    description: str
    priority: TicketPriority = "medium"


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_to: int | None = None


class TicketResponse(BaseModel):
    id: int
    ticket_type: TicketType
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_by: int
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.schemas.ticket import TicketCreate
from backend.app.services.ticket_service import (
    create_ticket,
    get_my_tickets,
)

def create_employee_ticket(
    db: Session,
    current_user: User,
    ticket_type: str,
    title: str,
    description: str,
    priority: str = "medium",
):
    ticket_data = TicketCreate(
        ticket_type=ticket_type,
        title=title,
        description=description,
        priority=priority,
    )

    return create_ticket(
        db=db,
        ticket_data=ticket_data,
        current_user=current_user,
    )


def get_employee_tickets(
    db: Session,
    current_user: User,
):
    return get_my_tickets(
        db=db,
        current_user=current_user,
    )

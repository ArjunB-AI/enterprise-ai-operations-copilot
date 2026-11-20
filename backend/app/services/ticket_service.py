
from sqlalchemy.orm import Session

from backend.app.models.ticket import Ticket
from backend.app.models.user import User
from backend.app.schemas.ticket import TicketCreate


def create_ticket(
    db: Session,
    ticket_data: TicketCreate,
    current_user: User,
) -> Ticket:
    """
    Create a ticket for the authenticated user.
    """

    ticket = Ticket(
        ticket_type=ticket_data.ticket_type,
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        created_by=current_user.id,
        status="open",
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return ticket

    except Exception:
        db.rollback()
        raise


def get_my_tickets(
    db: Session,
    current_user: User,
) -> list[Ticket]:
    """
    Retrieve tickets created by the authenticated user.
    """

    tickets = (
        db.query(Ticket)
        .filter(Ticket.created_by == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return tickets

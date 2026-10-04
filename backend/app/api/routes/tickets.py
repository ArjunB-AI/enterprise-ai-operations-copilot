from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user, require_role
from backend.app.db.dependencies import get_db
from backend.app.models.ticket import Ticket
from backend.app.models.user import User
from backend.app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = Ticket(
        ticket_type=ticket_data.ticket_type,
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        created_by=current_user.id,
        status="open",
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket

@router.get(
    "/my",
    response_model=list[TicketResponse],
)
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.created_by == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return tickets

# it support side endponts
@router.get(
    "",
    response_model=list[TicketResponse],
)
def get_all_tickets(
    current_user: User = Depends(require_role("it_support")),
    db: Session = Depends(get_db),
):
    tickets = (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return tickets

@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    current_user: User = Depends(require_role("it_support")),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    if ticket_data.status is not None:
        ticket.status = ticket_data.status

    if ticket_data.priority is not None:
        ticket.priority = ticket_data.priority

    if ticket_data.assigned_to is not None:
        ticket.assigned_to = ticket_data.assigned_to

    db.commit()
    db.refresh(ticket)

    return ticket
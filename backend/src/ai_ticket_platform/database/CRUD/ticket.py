# database/CRUD/ticket.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from ai_ticket_platform.database.generated_models import Ticket


async def create_tickets(db: AsyncSession, tickets_data: List[dict]) -> List[Ticket]:
	"""
	Bulk insert tickets from CSV data.
	"""
	tickets = []

	for ticket_data in tickets_data:
		# Build ticket params, excluding created_at if None to allow database default
		ticket_params = {
			"subject": ticket_data.get("subject"),
			"body": ticket_data.get("body"),
		}
		if ticket_data.get("created_at") is not None:
			ticket_params["created_at"] = ticket_data.get("created_at")

		ticket = Ticket(**ticket_params)
		tickets.append(ticket)

	try:
		db.add_all(tickets)
		await db.commit()
	except SQLAlchemyError as e:
		await db.rollback()
		raise RuntimeError(f"Failed to create tickets: {e}") from e

	return tickets


async def get_ticket(db: AsyncSession, ticket_id: int) -> Ticket | None:
    """
    Fetch a single ticket by ID.
    """
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    return result.scalar_one_or_none()


async def list_tickets(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Ticket]:
    """
    Fetch all tickets with pagination.
    """
    result = await db.execute(select(Ticket)
        .offset(skip)
        .limit(limit)
        .order_by(Ticket.created_at.desc())
    )
    return result.scalars().all()


async def count_tickets(db: AsyncSession) -> int:
	"""
	Count the total number of tickets in the database.

	Args:
	    db: Database session

	Returns:
	    Total count of tickets
	"""
	result = await db.execute(select(func.count(Ticket.id)))
	return result.scalar_one()


async def list_tickets_by_intent(db: AsyncSession, intent_id: int) -> List[Ticket]:
    """
    Fetch all tickets linked to a specific intent.
    """
    result = await db.execute(select(Ticket)
        .where(Ticket.intent_id == intent_id)
        .order_by(Ticket.created_at.desc())
    )
    return result.scalars().all()


async def update_ticket_intent(db: AsyncSession, ticket_id: int, intent_id: int) -> Ticket | None:
    """
    Update a ticket's intent_id (used when orchestrator links clusters to tickets).
    """
    ticket = await get_ticket(db, ticket_id)
    
    if not ticket:
        return None
    
    ticket.intent_id = intent_id
    await db.commit()
    await db.refresh(ticket)

    return ticket


async def get_unassigned_tickets(db: AsyncSession) -> List[Ticket]:
    """
    Fetch all tickets that haven't been assigned to an intent yet.
    """
    result = await db.execute(
        select(Ticket)
        .where(Ticket.intent_id.is_(None))
        .order_by(Ticket.created_at.desc())
    )
    return list(result.scalars().all())

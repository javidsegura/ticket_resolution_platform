# database/CRUD/ticket.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ai_ticket_platform.database.generated_models import Ticket


async def create_tickets(db: AsyncSession, tickets_data: List[dict]) -> List[Ticket]:
    """
    Bulk insert tickets from CSV data.
    
    Args:
        db: Database session
        tickets_data: List of dicts with keys: subject, body, created_at
        
    Returns:
        List of created Ticket objects
    """
    tickets = []
    
    for ticket_data in tickets_data:
        ticket = Ticket(
            subject=ticket_data.get("Ticket Subject"),
            body=ticket_data.get("body"),
            created_at=ticket_data.get("created_at")
        )
        tickets.append(ticket)
    
    db.add_all(tickets)
    await db.commit()
    
    # Refresh all to get generated IDs
    for ticket in tickets:
        await db.refresh(ticket)
    
    return tickets


async def get_ticket(db: AsyncSession, ticket_id: int) -> Ticket | None:
    """
    Fetch a single ticket by ID.
    
    Args:
        db: Database session
        ticket_id: Ticket ID
        
    Returns:
        Ticket object or None if not found
    """
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    return result.scalar_one_or_none()


async def list_tickets(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Ticket]:
    """
    Fetch all tickets with pagination.
    
    Args:
        db: Database session
        skip: Number of tickets to skip
        limit: Maximum number of tickets to return
        
    Returns:
        List of Ticket objects
    """
    result = await db.execute(select(Ticket)
        .offset(skip)
        .limit(limit)
        .order_by(Ticket.created_at.desc())
    )
    return result.scalars().all()


async def list_tickets_by_intent(db: AsyncSession, intent_id: int) -> List[Ticket]:
    """
    Fetch all tickets linked to a specific intent.
    
    Args:
        db: Database session
        intent_id: Intent ID
        
    Returns:
        List of Ticket objects for that intent
    """
    result = await db.execute(select(Ticket)
        .where(Ticket.intent_id == intent_id)
        .order_by(Ticket.created_at.desc())
    )
    return result.scalars().all()


async def update_ticket_intent(db: AsyncSession, ticket_id: int, intent_id: int) -> Ticket | None:
    """
    Update a ticket's intent_id (used when orchestrator links clusters to tickets).
    
    Args:
        db: Database session
        ticket_id: Ticket ID
        intent_id: Intent ID to link
        
    Returns:
        Updated Ticket object or None if not found
    """
    ticket = await get_ticket(db, ticket_id)
    
    if not ticket:
        return None
    
    ticket.intent_id = intent_id
    await db.commit()
    await db.refresh(ticket)
    
    return ticket

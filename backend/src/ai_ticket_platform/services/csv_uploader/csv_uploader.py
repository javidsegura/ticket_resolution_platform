import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.database.generated_models import Ticket
from ai_ticket_platform.database.CRUD.ticket import create_tickets

logger = logging.getLogger(__name__)


async def save_tickets_to_db(db: AsyncSession,tickets_data: List[dict]) -> List[Ticket]:
    """
    Save parsed tickets to database.
    
    Args:
        db: Database session
        tickets_data: List of parsed ticket dicts from CSV parser
                     Keys: subject, id, created_at, body
    
    Returns:
        List of created Ticket objects with generated IDs
        
    Raises:
        ValueError: If tickets_data is empty or invalid
        Exception: Database errors during insertion
    """
    
    if not tickets_data:
        raise ValueError("No tickets data to save")
    
    logger.info(f"Saving {len(tickets_data)} tickets to database")
    
    try:
        # CRUD function to insert
        created_tickets = await create_tickets(db, tickets_data)
        logger.info(f"Successfully saved {len(created_tickets)} tickets to database")
        return created_tickets
    
    except Exception as e:
        logger.error(f"Error saving tickets to database: {str(e)}")
        raise RuntimeError(f"Failed to save tickets: {str(e)}") from e
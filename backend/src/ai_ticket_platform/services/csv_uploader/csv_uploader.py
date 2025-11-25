import logging
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.database.generated_models import Ticket
from ai_ticket_platform.database.CRUD.ticket import create_tickets
from ai_ticket_platform.core.clients import llm_client
from ai_ticket_platform.services.clustering.cluster_service import cluster_and_categorize_tickets

logger = logging.getLogger(__name__)


async def cluster_tickets_with_cache(tickets_data: List[dict]) -> Dict:
    """
    Cluster a list of ticket dictionaries and return clustering metadata, using an LLM-backed service with internal caching.
    
    Parameters:
        tickets_data (List[dict]): Parsed ticket dictionaries (e.g., containing `subject`, `id`, `created_at`, `body`).
    
    Returns:
        Dict: A dictionary with clustering results and metadata:
            - `total_tickets` (int): Number of tickets considered.
            - `clusters_created` (int): Number of clusters created in this operation.
            - `clusters` (List[dict]): List of cluster objects (structure depends on the clustering service).
            - `cached` (bool): `true` if the returned result was served from cache, `false` otherwise.
    
    Raises:
        RuntimeError: If clustering fails.
    """
    if not tickets_data:
        logger.warning("No tickets to cluster")
        return {
            "total_tickets": 0,
            "clusters_created": 0,
            "clusters": [],
            "cached": False
        }

    logger.info(f"Starting clustering for {len(tickets_data)} tickets (with cache)")

    try:
        # Call clustering service which handles caching internally
        clustering_result = await cluster_and_categorize_tickets(tickets_data, llm_client)
        logger.info(f"Clustering completed: {clustering_result.get('clusters_created', 0)} clusters created")
        return clustering_result
    except Exception as e:
        logger.error(f"Error during clustering: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to cluster tickets: {str(e)}") from e


async def save_tickets_to_db(db: AsyncSession,tickets_data: List[dict]) -> List[Ticket]:
    """
    Save a list of parsed ticket dictionaries to the database and return the created Ticket objects.
    
    Parameters:
        db (AsyncSession): Active asynchronous database session used for insertion.
        tickets_data (List[dict]): Parsed ticket dictionaries from the CSV parser. Expected keys include
            `subject`, `id`, `created_at`, and `body`.
    
    Returns:
        List[Ticket]: The list of Ticket objects created in the database, each containing generated IDs.
    
    Raises:
        ValueError: If `tickets_data` is empty.
        RuntimeError: If a database error occurs while creating tickets; the original exception is chained.
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
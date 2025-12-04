import logging
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.database.generated_models import Ticket
from ai_ticket_platform.database.CRUD.ticket import create_tickets
from ai_ticket_platform.core.clients import llm_client
from ai_ticket_platform.services.clustering.cluster_service import cluster_tickets

logger = logging.getLogger(__name__)


async def cluster_tickets_with_cache(db: AsyncSession, tickets_data: List[dict]) -> Dict:
    """
    Cluster tickets using the LLM with caching for deduplication.

    Args:
        db: Database session
        tickets_data: List of ticket dicts from CSV parser

    Returns:
        Dict with clustering results including cache hit info
    """
    if not tickets_data:
        logger.warning("No tickets to cluster")
        return {
            "total_tickets": 0,
            "clusters_created": 0,
            "clusters": [],
            "cached": False,
        }

    logger.info(f"Starting clustering for {len(tickets_data)} tickets (with cache)")

    try:
        # Call clustering service which handles caching internally
        # Note: cluster_tickets expects (db, llm_client, tickets) arguments
        clustering_result = await cluster_tickets(db, llm_client, tickets_data)
        logger.info(f"Clustering completed: {clustering_result.get('clusters_created', 0)} clusters created")
        return clustering_result
    except Exception as e:
        logger.error(f"Error during clustering: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to cluster tickets: {str(e)}") from e
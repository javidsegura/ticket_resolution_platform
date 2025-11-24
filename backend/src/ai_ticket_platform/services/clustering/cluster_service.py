from typing import List, Dict
import logging
import hashlib
import json

import ai_ticket_platform.core.clients as clients
from ai_ticket_platform.core.clients import LLMClient
from ai_ticket_platform.services.clustering import llm_clusterer
from ai_ticket_platform.services.caching.ttl_config import CacheTTL

logger = logging.getLogger(__name__)

def _compute_clustering_hash(ticket_texts: List[str]) -> str:
    """
    Compute SHA256 hash of sorted ticket titles for deduplication.

    Args:
        ticket_texts: List of ticket subject strings

    Returns:
        SHA256 hash hex string
    """
    sorted_texts = sorted(ticket_texts)
    combined = json.dumps(sorted_texts, sort_keys=True)
    return hashlib.sha256(combined.encode()).hexdigest()


async def cluster_and_categorize_tickets(tickets: List[Dict],llm_client: LLMClient) -> Dict:
    """
    Main entry point for ticket clustering.

    Orchestrates the complete workflow:
    1. Extract ticket texts from 'Ticket Subject' column
    2. Call LLM clusterer
    3. Transform results for storage
    TODO: 4. Save to database

    Args:
        tickets: List of ticket dicts with 'Ticket Subject' field
        llm_client: Initialized LLM client instance for making API calls

    Returns:
        Dict with clustering results:
        {
            "total_tickets": 150,
            "clusters_created": 7,
            "clusters": [
                {
                    "topic_name": "Password Reset Issues",
                    "product_category": "Account Management",
                    "product_subcategory": "Authentication",
                    "ticket_count": 35,
                    "example_tickets": ["How to reset...", ...],
                    "summary": "Users unable to reset passwords"
                },
                ...
            ]
        }
    """

    # preprocess ticket data
    logger.debug(f"Starting ticket clustering for {len(tickets)} tickets")
    ticket_texts = _extract_ticket_texts(tickets)

    if not ticket_texts:
        logger.warning("No valid ticket texts extracted from tickets")
        return {
            "total_tickets": 0,
            "clusters_created": 0,
            "clusters": []
        }

    logger.info(f"Extracted {len(ticket_texts)} ticket texts for clustering")

    # Compute hash for deduplication
    clustering_hash = _compute_clustering_hash(ticket_texts)
    cache_key = f"clustering:batch:{clustering_hash}"

    # Try cache first (if initialized)
    if clients.cache_manager:
        cached_result = await clients.cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Cache HIT for clustering hash {clustering_hash[:8]}... - returning cached result")
            return cached_result
        logger.info(f"Cache MISS for clustering hash {clustering_hash[:8]}... - calling LLM")
    else:
        logger.warning("Cache manager not initialized, skipping cache check")

    # cluster tickets using injected LLM client
    try:
        # Handle case where LLM client is not initialized
        if not llm_client:
            logger.warning("LLM client not initialized, returning empty clustering result")
            clustering_result = {
                "total_tickets": len(ticket_texts),
                "clusters_created": 0,
                "clusters": []
            }
        else:
            clustering_result = llm_clusterer.cluster_tickets(llm_client=llm_client, ticket_texts=ticket_texts)
            logger.info(f"Successfully clustered tickets into {clustering_result.get('clusters_created', 0)} clusters")

        # Store in cache for 30 days (if initialized)
        if clients.cache_manager:
            await clients.cache_manager.set(cache_key, clustering_result, CacheTTL.CLUSTERING_TTL)
            logger.info(f"Cached clustering result with TTL {CacheTTL.CLUSTERING_TTL}s")
        else:
            logger.warning("Cache manager not initialized, skipping cache storage")

        return clustering_result
    except Exception as e:
        logger.exception(f"Failed to cluster tickets: {str(e)}")
        raise RuntimeError(f"Failed to cluster tickets: {str(e)}") from e


def _extract_ticket_texts(tickets: List[Dict]) -> List[str]:
    """
    Extract ticket subject/title field from ticket dictionaries.
    Supports multiple field names: 'subject', 'title', 'Ticket Subject'

    Args:
        tickets: List of ticket dicts with subject/title field

    Returns: List of ticket subject strings
    """
    ticket_texts = []

    for ticket in tickets:
        # Try multiple field name variations
        subject = (
            ticket.get("subject", "") or
            ticket.get("title", "") or
            ticket.get("Ticket Subject", "")
        ).strip()

        if subject:
            ticket_texts.append(subject)

    logger.debug(f"Extracted {len(ticket_texts)} valid ticket subjects from {len(tickets)} tickets")
    return ticket_texts

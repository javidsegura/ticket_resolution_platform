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
    Compute a deterministic SHA256 hex digest for a list of ticket texts to detect duplicate batches.
    
    Parameters:
        ticket_texts (List[str]): Ticket subject strings to include in the hash; order-insensitive.
    
    Returns:
        str: Hexadecimal SHA256 digest of the JSON-encoded, sorted ticket texts.
    """
    sorted_texts = sorted(ticket_texts)
    combined = json.dumps(sorted_texts, sort_keys=True)
    return hashlib.sha256(combined.encode()).hexdigest()


async def cluster_and_categorize_tickets(tickets: List[Dict],llm_client: LLMClient) -> Dict:
    """
    Cluster and categorize a batch of tickets into topic-based clusters.
    
    Parameters:
        tickets (List[Dict]): List of ticket dictionaries. The function will extract a subject/title from the first available of 'subject', 'title', or 'Ticket Subject' for each ticket.
        llm_client (LLMClient): Initialized LLM client used to perform clustering; if not provided or falsy, the function returns a result counting tickets with zero clusters.
    
    Returns:
        Dict: Clustering result with the following structure:
            {
                "total_tickets": int,
                "clusters_created": int,
                "clusters": [
                    {
                        "topic_name": str,
                        "product_category": str,
                        "product_subcategory": str,
                        "ticket_count": int,
                        "example_tickets": List[str],
                        "summary": str
                    },
                    ...
                ]
            }
    
    Raises:
        RuntimeError: If clustering fails due to an unexpected error.
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
    Extracts subject/title strings from a list of ticket dictionaries.
    
    Attempts to read subject text from each ticket using the following keys (in order): 'subject', 'title', 'Ticket Subject'. Skips tickets with no present or non-empty subject after trimming whitespace.
    
    Parameters:
        tickets (List[Dict]): List of ticket dictionaries to extract subjects from.
    
    Returns:
        List[str]: Extracted subject strings in the same order as their source tickets (omitting tickets with no valid subject).
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
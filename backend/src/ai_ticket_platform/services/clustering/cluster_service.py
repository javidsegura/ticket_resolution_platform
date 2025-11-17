from typing import List, Dict

from ai_ticket_platform.core.clients import LLMClient
from ai_ticket_platform.services.clustering import llm_clusterer

def cluster_and_categorize_tickets(tickets: List[Dict],llm_client: LLMClient) -> Dict:
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
    ticket_texts = _extract_ticket_texts(tickets)

    if not ticket_texts:
        return {
            "total_tickets": 0,
            "clusters_created": 0,
            "clusters": []
        }

     # cluster tickets using injected LLM client
    try:
        clustering_result = llm_clusterer.cluster_tickets(llm_client=llm_client, ticket_texts=ticket_texts)
        return clustering_result
    except Exception as e:
          raise RuntimeError(f"Failed to cluster tickets: {str(e)}") from e


def _extract_ticket_texts(tickets: List[Dict]) -> List[str]:
    """
    Extract 'Ticket Subject' field from ticket dictionaries.

    Args:
        tickets: List of ticket dicts with 'Ticket Subject' field

    Returns: List of ticket subject strings
    """
    ticket_texts = []

    for ticket in tickets:
        # try to get 'Ticket Subject'
        subject = ticket.get("Ticket Subject", "").strip()
        if subject:
            ticket_texts.append(subject)

    return ticket_texts

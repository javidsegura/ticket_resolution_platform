"""
LLM-based ticket clustering.

Handles the core clustering logic using LLM with structured output.
"""

from typing import List, Dict

from ai_ticket_platform.core.clients import LLMClient
from ai_ticket_platform.services.clustering import prompt_builder


def cluster_tickets(llm_client: LLMClient, ticket_texts: List[str]) -> Dict:
    """
    Use LLM with structured output to cluster all tickets in one call.

    Args:
        llm_client: Initialized LLM client instance
        ticket_texts: List of ticket text strings

    Returns:
        Dict with clustering results:
        {
            "clusters": [
                {
                    "topic_name": "Password Reset Issues",
                    "category": "Account Management",
                    "subcategory": "Authentication",
                    "ticket_indices": [0, 5, 12, 23, ...],
                    "summary": "Users unable to reset passwords..."
                },
                ...
            ]
        }
    """

    # build prompt and get schema
    prompt = prompt_builder.build_clustering_prompt(ticket_texts=ticket_texts)
    output_schema = prompt_builder.get_output_schema()

    # configure LLM for clustering task
    task_config = {
        "system_prompt": (
            "You are a support ticket clustering expert. "
            "Analyze tickets and group them into meaningful clusters."
        ),
        "schema_name": "ticket_clustering"
    }

    # call LLM
    result = llm_client.call_llm_structured(prompt=prompt, output_schema=output_schema, task_config=task_config, temperature=0.3)

    clusters = result.get("clusters", [])

    # validate that all tickets were assigned
    assigned_tickets = set()
    for cluster in clusters:
        assigned_tickets.update(cluster["ticket_indices"])

    return result

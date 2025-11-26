import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)



def filter_ticket(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
    ticket_id = ticket_data.get("id")
    logger.info(f"[FILTER] Filtering ticket {ticket_id}")
    
    required_fields = ["id", "description", "category"]
    for field in required_fields:
        if field not in ticket_data or not ticket_data[field]:
            raise ValueError(f"Missing: {field}")
    
    result = {
        "id": ticket_data["id"],
        "description": str(ticket_data["description"]).strip(),
        "category": str(ticket_data["category"]).lower(),
        "priority": ticket_data.get("priority", "medium")
    }
    logger.info(f"[FILTER] Ticket {ticket_id} filtered successfully")
    return result


def cluster_ticket(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
    ticket_id = ticket_data.get("id")
    logger.info(f"[CLUSTER] Clustering ticket {ticket_id}")
    
    description = ticket_data["description"].lower()
    
    if "bug" in description or "error" in description:
        cluster = "technical_issue"
    elif "feature" in description or "add" in description:
        cluster = "feature_request"
    else:
        cluster = "general_inquiry"
    
    ticket_data["cluster"] = cluster
    logger.info(f"[CLUSTER] Ticket {ticket_id} assigned to cluster: {cluster}")
    return ticket_data


def generate_content(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
    ticket_id = ticket_data.get("id")
    cluster = ticket_data["cluster"]
    logger.info(f"[GENERATE] Generating content for ticket {ticket_id} in cluster {cluster}")
    
    templates = {
        "technical_issue": "We've identified this as a technical issue...",
        "feature_request": "Thank you for your feature suggestion...",
        "general_inquiry": "Thanks for reaching out..."
    }
    
    result = {
        "ticket_id": ticket_id,
        "cluster": cluster,
        "response": templates.get(cluster, "We'll look into this..."),
        "timestamp": time.time()
    }
    logger.info(f"[GENERATE] Content generated for ticket {ticket_id}")
    return result
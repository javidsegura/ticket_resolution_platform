import logging
from typing import Dict, Any, List

from ai_ticket_platform.database.main import initialize_db_engine
from ai_ticket_platform.database.CRUD.ticket import create_tickets
from ai_ticket_platform.services.clustering.cluster_interface import cluster_tickets
from ai_ticket_platform.core.clients.llm import get_llm_client
from ai_ticket_platform.services.content_generation.content_generation_interface import generate_article_task
from ai_ticket_platform.services.queue_manager.async_helper import _run_async

logger = logging.getLogger(__name__)


def save_tickets(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
	"""Validate ticket data, then create in database.

	Uses async CRUD operations via _run_async helper.
	"""
	csv_id = ticket_data.get("id", "unknown")
	logger.info(f"[FILTER] Filtering ticket with CSV id {csv_id}")

	# Validate required fields
	required_fields = ["subject", "body"]
	for field in required_fields:
		if field not in ticket_data or not ticket_data[field]:
			raise ValueError(f"Missing required field: {field}")

	# Create ticket in database using async CRUD
	async def create_in_db():
		AsyncSessionLocal = initialize_db_engine()
		async with AsyncSessionLocal() as db:
			tickets = await create_tickets(db, [ticket_data])
			if not tickets:
				raise RuntimeError(f"Failed to create ticket with CSV id {csv_id}")
			return tickets[0]

	db_ticket = _run_async(create_in_db())

	# Return enriched ticket data with DB id
	result = {
		"id": db_ticket.id,  # DB ticket ID
		"csv_id": csv_id,  # Original CSV id
		"subject": str(ticket_data["subject"]).strip(),
		"body": str(ticket_data["body"]).strip(),
		"source_row": ticket_data.get("source_row"),
	}

	logger.info(f"[FILTER] Ticket {csv_id} created in DB with id {db_ticket.id}")
	return result


def cluster_ticket(tickets_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	"""Cluster a BATCH of tickets using the clustering service.

	Args:
		tickets_data: List of ticket data dictionaries (already filtered and created in DB)

	Returns:
		List of ticket data dictionaries with clustering results added
	"""
	if not tickets_data:
		logger.warning("[CLUSTER] Empty ticket batch provided")
		return []

	ticket_ids = [t.get("id") for t in tickets_data]
	logger.info(f"[CLUSTER] Clustering batch of {len(tickets_data)} tickets: {ticket_ids}")

	# Initialize LLM client for this worker
	llm = get_llm_client()

	async def run_clustering():
		AsyncSessionLocal = initialize_db_engine()

		async with AsyncSessionLocal() as db:
			logger.info(f"[CLUSTER] Calling cluster_tickets with {len(tickets_data)} tickets")

			# Run clustering on the entire batch
			clustering_result = await cluster_tickets(
				db=db,
				llm_client=llm,
				tickets=tickets_data
			)

			# Extract assignments
			if not clustering_result.get("assignments"):
				raise RuntimeError("Clustering returned no assignments")

			return clustering_result["assignments"]

	assignments = _run_async(run_clustering())

	# Map assignments back to ticket_data
	# Create a mapping of ticket_id -> assignment
	assignment_map = {}
	for assignment in assignments:
		ticket_id = assignment.get("ticket_id")
		if ticket_id:
			assignment_map[ticket_id] = assignment

	# Add to each ticket_data with clustering results
	enriched_tickets = []
	for ticket_data in tickets_data:
		ticket_id = ticket_data.get("id")
		assignment = assignment_map.get(ticket_id)

		if assignment:
			# Validate required fields from clustering service
			intent_name = assignment.get("intent_name")
			intent_id = assignment.get("intent_id")

			if not intent_name or not intent_id:
				logger.error(
					f"[CLUSTER] Invalid assignment for ticket {ticket_id}: "
					f"missing intent_name or intent_id. Assignment: {assignment}"
				)
				continue

			# Create enriched copy to avoid mutating input
			enriched = ticket_data.copy()
			enriched["cluster"] = intent_name
			enriched["intent_id"] = intent_id
			enriched["category_l1_id"] = assignment.get("category_l1_id")
			enriched["category_l1_name"] = assignment.get("category_l1_name")
			enriched["category_l2_id"] = assignment.get("category_l2_id")
			enriched["category_l2_name"] = assignment.get("category_l2_name")
			enriched["category_l3_id"] = assignment.get("category_l3_id")
			enriched["category_l3_name"] = assignment.get("category_l3_name")

			logger.info(f"[CLUSTER] Ticket {ticket_id} assigned to intent: {intent_name} (ID: {intent_id})")
			enriched_tickets.append(enriched)
		else:
			logger.warning(f"[CLUSTER] No assignment found for ticket {ticket_id}")

	logger.info(f"[CLUSTER] Batch clustering complete: {len(enriched_tickets)}/{len(tickets_data)} tickets successfully clustered")
	return enriched_tickets


def generate_content(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
	"""Generate article content for an intent/cluster using RAG.

	Note: This is called ONCE per unique cluster (intent) by the batch_finalizer,
	not once per ticket. Multiple tickets in the same cluster share one article.
	"""
	ticket_id = ticket_data.get("id")
	intent_id = ticket_data.get("intent_id")
	cluster = ticket_data.get("cluster")

	if not intent_id:
		raise ValueError(f"Missing intent_id for ticket {ticket_id} - cannot generate content")

	logger.info(f"[GENERATE] Generating article for intent '{cluster}' (ID: {intent_id}) - representative ticket: {ticket_id}")

	# Call the RAG article generation task
	# This function is already sync-compatible (uses _run_async internally)
	result = generate_article_task(intent_id=intent_id)
	logger.info(f"[GENERATE] Article generation for intent {intent_id}: {result.get('status')}")

	return {
		"ticket_id": ticket_id,
		"intent_id": intent_id,
		"cluster": cluster,
		"article_id": result.get("article_id"),
		"status": result.get("status"),
		"result": result
	}

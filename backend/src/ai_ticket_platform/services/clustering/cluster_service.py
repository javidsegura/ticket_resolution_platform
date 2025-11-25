# services/clustering/cluster_service.py
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ai_ticket_platform.core.clients import LLMClient
from ai_ticket_platform.database.generated_models import Ticket
from ai_ticket_platform.database.CRUD import intent as intent_crud
from ai_ticket_platform.services.clustering import batch_processor

logger = logging.getLogger(__name__)

# Default batch size - can be adjusted based on LLM context limits
DEFAULT_BATCH_SIZE = 10

async def cluster_tickets(
	db: AsyncSession,
	llm_client: LLMClient,
	tickets: List[Ticket],
	batch_size: int = DEFAULT_BATCH_SIZE
) -> Dict:
	"""
	Entry point for ticket clustering.

	This approach processes tickets in batches. For each batch:
	1. Fetch all existing intents with their 3-tier category hierarchy
	2. Send batch of tickets + all intents to LLM
	3. LLM decides for each ticket: MATCH existing intent OR CREATE new specific intent
	4. Create category hierarchy and intents as needed
	5. Assign tickets to intents

	Args:
		db: Database session
		llm_client: Initialized LLM client instance
		tickets: List of Ticket objects to cluster
		batch_size: Number of tickets to process per LLM call (default: 10)

	Returns:
		Dict with clustering results:
		{
			"total_tickets": 150,
			"intents_created": 12,
			"intents_matched": 138,
			"categories_created": {"l1": 2, "l2": 5, "l3": 12},
			"assignments": [...]
		}
	"""
	if not tickets:
		logger.warning("No tickets provided for clustering")
		return {
			"total_tickets": 0,
			"intents_created": 0,
			"intents_matched": 0,
			"categories_created": {"l1": 0, "l2": 0, "l3": 0},
			"assignments": []
		}

	logger.info(f"Starting batch clustering for {len(tickets)} tickets (batch_size={batch_size})")

	# Get all existing intents with their category hierarchy
	existing_intents = await intent_crud.get_all_intents_with_categories(db)

	logger.info(f"Found {len(existing_intents)} existing intents in the system")

	# Initialize statistics
	stats = {
		"intents_created": 0,
		"intents_matched": 0,
		"categories_created": {"l1": 0, "l2": 0, "l3": 0}
	}

	# Process tickets in batches
	all_assignments = []
	num_batches = (len(tickets) + batch_size - 1) // batch_size

	for batch_idx in range(num_batches):
		start_idx = batch_idx * batch_size
		end_idx = min(start_idx + batch_size, len(tickets))
		batch_tickets = tickets[start_idx:end_idx]

		logger.info(f"Processing batch {batch_idx + 1}/{num_batches} ({len(batch_tickets)} tickets)")

		try:
			# Process batch
			batch_assignments = await batch_processor.process_batch(
				db=db,
				llm_client=llm_client,
				tickets=batch_tickets,
				existing_intents=existing_intents,
				stats=stats
			)

			all_assignments.extend(batch_assignments)

			# Update existing_intents with newly created intents from this batch
			for assignment in batch_assignments:
				if assignment.get("is_new_intent"):
					existing_intents.append({
						"intent_id": assignment["intent_id"],
						"intent_name": assignment["intent_name"],
						"category_l1_id": assignment["category_l1_id"],
						"category_l1_name": assignment["category_l1_name"],
						"category_l2_id": assignment["category_l2_id"],
						"category_l2_name": assignment["category_l2_name"],
						"category_l3_id": assignment["category_l3_id"],
						"category_l3_name": assignment["category_l3_name"]
					})

		except Exception as e:
			logger.error(f"Error processing batch {batch_idx + 1}: {str(e)}")
			raise RuntimeError(f"Failed to process batch {batch_idx + 1}: {str(e)}") from e

	# Build final result
	result = {
		"total_tickets": len(all_assignments),
		"intents_created": stats["intents_created"],
		"intents_matched": stats["intents_matched"],
		"total_intents": stats["intents_created"] + stats["intents_matched"],
		"categories_created": stats["categories_created"],
		"assignments": all_assignments
	}

	logger.info(
		f"Batch clustering completed successfully:\n"
		f"  - Tickets processed: {result['total_tickets']}\n"
		f"  - Batches processed: {num_batches}\n"
		f"  - Intents created: {result['intents_created']}\n"
		f"  - Intents matched: {result['intents_matched']}\n"
		f"  - New categories: L1={stats['categories_created']['l1']}, "
		f"L2={stats['categories_created']['l2']}, L3={stats['categories_created']['l3']}"
	)

	return result




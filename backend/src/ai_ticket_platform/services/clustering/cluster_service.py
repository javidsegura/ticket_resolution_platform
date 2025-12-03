# services/clustering/cluster_service.py
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import hashlib
import json
import asyncio

import ai_ticket_platform.core.clients as clients
from ai_ticket_platform.core.clients import LLMClient
from ai_ticket_platform.database.CRUD import intent as intent_crud
from ai_ticket_platform.services.clustering import prompt_builder, intent_matcher
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


async def cluster_tickets(
	db: AsyncSession,
	llm_client: LLMClient,
	tickets: List[Dict]
) -> Dict:
	"""
	Cluster a batch of tickets by assigning them to existing or new intents.

	Tickets are already batched by the caller, so we process them all at once:
	1. Fetch all existing intents with their 3-tier category hierarchy
	2. Send all tickets + all intents to LLM in one call
	3. LLM decides for each ticket: MATCH existing intent OR CREATE new specific intent
	4. Create category hierarchy and intents as needed
	5. Assign tickets to intents

	Args:
		db: Database session
		llm_client: LLM client for clustering
		tickets: List of ticket dicts with keys: id, subject, body

	Returns:
		Dict with clustering results and statistics
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

	logger.info(f"Starting clustering for {len(tickets)} tickets")

	# Extract ticket texts for cache key computation
	ticket_texts = [ticket.get("subject", "") for ticket in tickets]
	clustering_hash = _compute_clustering_hash(ticket_texts)
	cache_key = f"clustering:batch:{clustering_hash}"

	# Try cache first (if initialized)
	if clients.cache_manager:
		cached_result = await clients.cache_manager.get(cache_key)
		if cached_result:
			logger.info(f"Cache HIT for clustering hash {clustering_hash[:8]}... - returning cached result")
			return cached_result
		logger.info(f"Cache MISS for clustering hash {clustering_hash[:8]}... - processing tickets")
	else:
		logger.warning("Cache manager not initialized, skipping cache check")

	# Get all existing intents with their category hierarchy
	existing_intents = await intent_crud.get_all_intents_with_categories(db)
	logger.info(f"Found {len(existing_intents)} existing intents in the system")

	# Initialize statistics
	stats = {
		"intents_created": 0,
		"intents_matched": 0,
		"categories_created": {"l1": 0, "l2": 0, "l3": 0}
	}

	# Build prompt for batch
	prompt = prompt_builder.build_batch_clustering_prompt(tickets, existing_intents)
	schema = prompt_builder.get_batch_clustering_schema()
	task_config = prompt_builder.get_task_config()

	# Call LLM once for entire batch (wrapped in thread pool to avoid blocking)
	logger.debug(f"Calling LLM for batch of {len(tickets)} tickets")
	llm_result = await asyncio.to_thread(
		llm_client.call_llm_structured,
		prompt=prompt,
		output_schema=schema,
		task_config=task_config,
		temperature=0.2
	)

	# Validate we got assignments for all tickets
	llm_assignments = llm_result["assignments"]
	if len(llm_assignments) != len(tickets):
		raise ValueError(
			f"LLM returned {len(llm_assignments)} assignments, expected {len(tickets)}"
		)

	# Process each assignment
	all_assignments = []
	processed_indices = set()

	for llm_assignment in llm_assignments:
		ticket_index = llm_assignment["ticket_index"]

		if ticket_index < 0 or ticket_index >= len(tickets):
			raise ValueError(f"Invalid ticket_index {ticket_index} from LLM")

		if ticket_index in processed_indices:
			raise ValueError(f"Duplicate ticket_index {ticket_index} from LLM")
		processed_indices.add(ticket_index)

		ticket = tickets[ticket_index]
		decision = llm_assignment["decision"]

		if decision == "match_existing":
			assignment = await intent_matcher.process_match_decision(
				db, ticket, llm_assignment, existing_intents, stats
			)

		elif decision == "create_new":
			assignment = await intent_matcher.process_create_decision(
				db, ticket, llm_assignment, stats
			)

		else:
			raise ValueError(f"Unknown decision type from LLM: {decision}")

		all_assignments.append(assignment)

		# Update existing_intents with newly created intents
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

	# Build final result
	result = {
		"total_tickets": len(all_assignments),
		"intents_created": stats["intents_created"],
		"intents_matched": stats["intents_matched"],
		"total_intents": stats["intents_created"] + stats["intents_matched"],
		"categories_created": stats["categories_created"],
		"assignments": all_assignments
	}

	# Store in cache for configured TTL (if initialized)
	if clients.cache_manager:
		await clients.cache_manager.set(cache_key, result, CacheTTL.CLUSTERING_TTL)
		logger.info(f"Cached clustering result with TTL {CacheTTL.CLUSTERING_TTL}s")
	else:
		logger.warning("Cache manager not initialized, skipping cache storage")

	logger.info(
		f"Clustering completed successfully:\n"
		f"  - Tickets processed: {result['total_tickets']}\n"
		f"  - Intents created: {result['intents_created']}\n"
		f"  - Intents matched: {result['intents_matched']}\n"
		f"  - New categories: L1={stats['categories_created']['l1']}, "
		f"L2={stats['categories_created']['l2']}, L3={stats['categories_created']['l3']}"
	)

	return result




# services/clustering/batch_processor.py
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ai_ticket_platform.core.clients import LLMClient
from ai_ticket_platform.database.generated_models import Ticket
from ai_ticket_platform.services.clustering import prompt_builder
from ai_ticket_platform.services.clustering import intent_matcher

logger = logging.getLogger(__name__)


async def process_batch(
	db: AsyncSession,
	llm_client: LLMClient,
	tickets: List[Ticket],
	existing_intents: List[Dict],
	stats: Dict
) -> List[Dict]:
	"""
	Process a batch of tickets through the clustering pipeline.

	Args:
		db: Database session
		llm_client: LLM client
		tickets: Batch of tickets to process
		existing_intents: List of existing intents
		stats: Statistics dict to update

	Returns:
		List of assignment dicts for the batch
	"""
	# Build prompt for batch
	prompt = prompt_builder.build_batch_clustering_prompt(tickets, existing_intents)
	schema = prompt_builder.get_batch_clustering_schema()
	task_config = prompt_builder.get_task_config()

	# Call LLM once for entire batch
	logger.debug(f"Calling LLM for batch of {len(tickets)} tickets")
	llm_result = llm_client.call_llm_structured(
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
	batch_assignments = []
	for llm_assignment in llm_assignments:
		ticket_index = llm_assignment["ticket_index"]

		if ticket_index < 0 or ticket_index >= len(tickets):
			raise ValueError(f"Invalid ticket_index {ticket_index} from LLM")

		ticket = tickets[ticket_index]
		decision = llm_assignment["decision"]

		if decision == "match_existing":
			assignment = await intent_matcher.process_match_decision(
				db, ticket, llm_assignment, existing_intents
			)
			stats["intents_matched"] += 1

		elif decision == "create_new":
			assignment = await intent_matcher.process_create_decision(
				db, ticket, llm_assignment, stats
			)

		else:
			raise ValueError(f"Unknown decision type from LLM: {decision}")

		batch_assignments.append(assignment)

	return batch_assignments

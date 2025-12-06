# services/clustering/intent_matcher.py
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ai_ticket_platform.database.CRUD import intent as intent_crud
from ai_ticket_platform.database.CRUD import category as category_crud
from ai_ticket_platform.database.CRUD import ticket as ticket_crud

logger = logging.getLogger(__name__)


async def process_match_decision(
	db: AsyncSession,
	ticket: Dict,
	llm_result: Dict,
	existing_intents: List[Dict],
	stats: Dict,
) -> Dict:
	"""
	Process LLM decision to match ticket to existing intent.

	Args:
		db: Database session
		ticket: Ticket dict with keys: id, subject, body
		llm_result: Structured output from LLM
		existing_intents: List of existing intents
		stats: Statistics dict to update

	Returns:
		Assignment dict with ticket and intent information
	"""
	intent_id = llm_result["intent_id"]
	ticket_id = ticket.get("id")

	if ticket_id is None:
		raise ValueError("Ticket dict missing required 'id' field")
	if intent_id is None:
		raise ValueError(
			f"LLM chose 'match_existing' but didn't provide intent_id for ticket {ticket_id}"
		)

	# Find the intent in existing_intents
	matched_intent = next(
		(intent for intent in existing_intents if intent["intent_id"] == intent_id),
		None,
	)

	if not matched_intent:
		raise ValueError(f"LLM referenced non-existent intent ID: {intent_id}")

	# Update ticket with intent
	await ticket_crud.update_ticket_intent(db, ticket_id, intent_id)

	# Update statistics
	stats["intents_matched"] = stats.get("intents_matched", 0) + 1

	logger.info(
		f"Ticket {ticket_id} matched to existing intent: "
		f"{matched_intent['category_l1_name']} > {matched_intent['category_l2_name']} > {matched_intent['category_l3_name']}"
	)

	return {
		"ticket_id": ticket_id,
		"subject": ticket.get("subject"),
		"body": ticket.get("body"),
		"decision": "match_existing",
		"intent_id": intent_id,
		"intent_name": matched_intent["intent_name"],
		"category_l1_id": matched_intent["category_l1_id"],
		"category_l1_name": matched_intent["category_l1_name"],
		"category_l2_id": matched_intent["category_l2_id"],
		"category_l2_name": matched_intent["category_l2_name"],
		"category_l3_id": matched_intent["category_l3_id"],
		"category_l3_name": matched_intent["category_l3_name"],
		"is_new_intent": False,
		"confidence": llm_result.get("confidence"),
		"reasoning": llm_result.get("reasoning"),
	}


async def process_create_decision(
	db: AsyncSession, ticket: Dict, llm_result: Dict, stats: Dict
) -> Dict:
	"""
	Process LLM decision to create new intent with full category hierarchy.

	Args:
		db: Database session
		ticket: Ticket dict with keys: id, subject, body
		llm_result: Structured output from LLM
		stats: Statistics dict to update

	Returns:
		Assignment dict with ticket and intent information
	"""
	cat_l1_name = llm_result.get("category_l1_name")
	cat_l2_name = llm_result.get("category_l2_name")
	cat_l3_name = llm_result.get("category_l3_name")
	intent_name_from_llm = llm_result.get("intent_name")
	ticket_id = ticket.get("id")

	if ticket_id is None:
		raise ValueError("Ticket dict missing required 'id' field")

	if not cat_l1_name or not cat_l2_name or not cat_l3_name:
		raise ValueError(
			f"LLM chose 'create_new' but didn't provide all 3 category names for ticket {ticket_id}"
		)

	if not intent_name_from_llm:
		raise ValueError(
			f"LLM chose 'create_new' but didn't provide intent name for ticket {ticket_id}"
		)

	category_l1, is_l1_new = await category_crud.get_or_create_category(
		db, name=cat_l1_name, level=1, parent_id=None
	)
	if is_l1_new:
		stats.setdefault("categories_created", {}).setdefault("l1", 0)
		stats["categories_created"]["l1"] += 1
		logger.info(f"Created new L1 category: {cat_l1_name}")

	# Create or get Level 2 category
	category_l2, is_l2_new = await category_crud.get_or_create_category(
		db, name=cat_l2_name, level=2, parent_id=category_l1.id
	)
	if is_l2_new:
		stats.setdefault("categories_created", {}).setdefault("l2", 0)
		stats["categories_created"]["l2"] += 1
		logger.info(f"Created new L2 category: {cat_l2_name} under {cat_l1_name}")

	# Create or get Level 3 category
	category_l3, is_l3_new = await category_crud.get_or_create_category(
		db, name=cat_l3_name, level=3, parent_id=category_l2.id
	)
	if is_l3_new:
		stats.setdefault("categories_created", {}).setdefault("l3", 0)
		stats["categories_created"]["l3"] += 1
		logger.info(
			f"Created new L3 category: {cat_l3_name} under {cat_l1_name} > {cat_l2_name}"
		)
	if is_l3_new:
		stats["categories_created"]["l3"] += 1
		logger.info(
			f"Created new L3 category: {cat_l3_name} under {cat_l1_name} > {cat_l2_name}"
		)

	# Create intent using the semantic name from LLM
	intent, is_new_intent = await intent_crud.get_or_create_intent(
		db,
		name=intent_name_from_llm,
		category_level_1_id=category_l1.id,
		category_level_2_id=category_l2.id,
		category_level_3_id=category_l3.id,
		area=None,
	)

	# Update statistics based on whether intent was newly created
	if is_new_intent:
		stats["intents_created"] = stats.get("intents_created", 0) + 1
		logger.info(f"Created new intent: {intent_name_from_llm}")
	else:
		stats["intents_matched"] = stats.get("intents_matched", 0) + 1
		logger.info(f"Matched to existing intent: {intent_name_from_llm}")
	# Update ticket with intent
	await ticket_crud.update_ticket_intent(db, ticket_id, intent.id)

	return {
		"ticket_id": ticket_id,
		"subject": ticket.get("subject"),
		"body": ticket.get("body"),
		"decision": "create_new",
		"intent_id": intent.id,
		"intent_name": intent_name_from_llm,
		"category_l1_id": category_l1.id,
		"category_l1_name": cat_l1_name,
		"category_l2_id": category_l2.id,
		"category_l2_name": cat_l2_name,
		"category_l3_id": category_l3.id,
		"category_l3_name": cat_l3_name,
		"is_new_intent": is_new_intent,
		"is_l1_new": is_l1_new,
		"is_l2_new": is_l2_new,
		"is_l3_new": is_l3_new,
		"confidence": llm_result.get("confidence"),
		"reasoning": llm_result.get("reasoning"),
	}

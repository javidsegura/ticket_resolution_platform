# database/CRUD/intent.py
from typing import List, Optional, Tuple, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ai_ticket_platform.database.generated_models import Intent, Ticket, Category
import logging

logger = logging.getLogger(__name__)


async def get_intent_by_category_path(
	db: AsyncSession,
	category_level_1_id: int,
	category_level_2_id: int,
	category_level_3_id: int
) -> Optional[Intent]:
	"""
	Find an intent by its category path.
	"""
	query = select(Intent).where(
		Intent.category_level_1_id == category_level_1_id,
		Intent.category_level_2_id == category_level_2_id,
		Intent.category_level_3_id == category_level_3_id
	)

	result = await db.execute(query)
	return result.scalar_one_or_none()


async def create_intent(
	db: AsyncSession,
	name: str,
	category_level_1_id: int,
	category_level_2_id: int,
	category_level_3_id: int,
	area: Optional[str] = None
) -> Intent:
	"""
	Create a new intent.
	"""
	try:
		intent = Intent(
			name=name,
			category_level_1_id=category_level_1_id,
			category_level_2_id=category_level_2_id,
			category_level_3_id=category_level_3_id,
			area=area,
			is_processed=False
		)
		db.add(intent)
		await db.commit()
		await db.refresh(intent)

		logger.info(f"Created intent: {name} (id={intent.id}, l1={category_level_1_id}, l2={category_level_2_id}, l3={category_level_3_id})")
		return intent
	except Exception as e:
		await db.rollback()
		logger.error(f"Error creating intent '{name}': {str(e)}")
		raise


async def get_or_create_intent(
	db: AsyncSession,
	name: str,
	category_level_1_id: int,
	category_level_2_id: int,
	category_level_3_id: int,
	area: Optional[str] = None
) -> tuple[Intent, bool]:
	"""
	Get existing intent or create if it doesn't exist.

	Matches based on category path, not name. If an intent exists with the same
	category path but different name, returns the existing intent.

	Returns:
		Tuple of (Intent, created) where created is True if newly created
	"""
	try:
		# Try to find existing intent by category path
		intent = await get_intent_by_category_path(
			db,
			category_level_1_id,
			category_level_2_id,
			category_level_3_id
		)

		if intent:
			logger.debug(f"Found existing intent: {intent.name} (id={intent.id})")
			return intent, False

		# Create new intent if it doesn't exist
		logger.debug(f"Creating new intent: {name}")
		new_intent = await create_intent(
			db,
			name,
			category_level_1_id,
			category_level_2_id,
			category_level_3_id,
			area
		)
		return new_intent, True
	except Exception as e:
		await db.rollback()
		logger.error(f"Error in get_or_create_intent for '{name}': {str(e)}")
		raise

async def update_ticket_intent(
	db: AsyncSession,
	ticket_id: int,
	intent_id: int
) -> Ticket:
	"""
	Update a single ticket's intent_id.
	"""
	try:
		result = await db.execute(
			select(Ticket).where(Ticket.id == ticket_id)
		)
		ticket = result.scalar_one_or_none()

		if not ticket:
			raise ValueError(f"Ticket with id {ticket_id} not found")

		ticket.intent_id = intent_id
		await db.commit()
		await db.refresh(ticket)

		logger.info(f"Updated ticket {ticket_id} with intent {intent_id}")
		return ticket
	except Exception as e:
		await db.rollback()
		logger.error(f"Error updating ticket {ticket_id} intent: {str(e)}")
		raise

async def get_all_intents_with_categories(db: AsyncSession) -> List[Dict]:
	"""
	Fetch all intents with their full 3-tier category hierarchy.

	This is used by the clustering algorithm to provide
	the LLM with all existing intents for matching.
	"""
	# Query intents with eager loading of category relationships
	query = (
		select(Intent)
		.options(
			selectinload(Intent.category_level_1),
			selectinload(Intent.category_level_2),
			selectinload(Intent.category_level_3)
		)
		.order_by(Intent.created_at.desc())
	)

	result = await db.execute(query)
	intents = result.scalars().all()

	# Transform into dict format
	intent_dicts = []
	for intent in intents:
		# Only include intents with all 3 category levels
		if not intent.category_level_1 or not intent.category_level_2 or not intent.category_level_3:
			logger.warning(
				f"Skipping intent {intent.id} - missing category levels "
				f"(L1: {intent.category_level_1_id}, L2: {intent.category_level_2_id}, L3: {intent.category_level_3_id})"
			)
			continue

		intent_dicts.append({
			"intent_id": intent.id,
			"intent_name": intent.name,
			"category_l1_id": intent.category_level_1.id,
			"category_l1_name": intent.category_level_1.name,
			"category_l2_id": intent.category_level_2.id,
			"category_l2_name": intent.category_level_2.name,
			"category_l3_id": intent.category_level_3.id,
			"category_l3_name": intent.category_level_3.name
		})

	logger.debug(f"Fetched {len(intent_dicts)} intents with complete category hierarchy")
	return intent_dicts

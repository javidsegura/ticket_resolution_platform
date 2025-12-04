from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from ai_ticket_platform.database.generated_models import Intent
from ai_ticket_platform.schemas.endpoints.intent import IntentCreate, IntentUpdate


async def create_intent(db: AsyncSession, intent_data: IntentCreate) -> Intent:
	"""
	Create a new intent.

	Args:
		db: Database session
		intent_data: IntentCreate schema with intent data

	Returns:
		Created Intent object
	"""
	db_intent = Intent(
		name=intent_data.name,
		category_level_1_id=intent_data.category_level_1_id,
		category_level_2_id=intent_data.category_level_2_id,
		category_level_3_id=intent_data.category_level_3_id,
		area=intent_data.area,
		is_processed=intent_data.is_processed,
		variant_a_impressions=intent_data.variant_a_impressions,
		variant_b_impressions=intent_data.variant_b_impressions,
		variant_a_resolutions=intent_data.variant_a_resolutions,
		variant_b_resolutions=intent_data.variant_b_resolutions,
	)

	db.add(db_intent)
	await db.commit()
	await db.refresh(db_intent)

	return db_intent


async def get_intent(db: AsyncSession, intent_id: int) -> Intent | None:
	"""
	Fetch a single intent by ID.

	Args:
		db: Database session
		intent_id: Intent ID

	Returns:
		Intent object or None if not found
	"""
	result = await db.execute(select(Intent).where(Intent.id == intent_id))
	return result.scalar_one_or_none()


async def list_intents(
	db: AsyncSession,
	skip: int = 0,
	limit: int = 100,
	is_processed: bool | None = None,
) -> List[Intent]:
	"""
	Fetch all intents with pagination and optional filtering.

	Args:
		db: Database session
		skip: Number of intents to skip
		limit: Maximum number of intents to return
		is_processed: Optional filter by is_processed status

	Returns:
		List of Intent objects
	"""
	query = select(Intent)

	if is_processed is not None:
		query = query.where(Intent.is_processed == is_processed)

	result = await db.execute(
		query.offset(skip).limit(limit).order_by(Intent.created_at.desc())
	)
	return result.scalars().all()


async def update_intent(
	db: AsyncSession, intent_id: int, intent_data: IntentUpdate
) -> Intent | None:
	"""
	Update an intent.

	Args:
		db: Database session
		intent_id: Intent ID
		intent_data: IntentUpdate schema with fields to update

	Returns:
		Updated Intent object or None if not found
	"""
	intent = await get_intent(db, intent_id)

	if not intent:
		return None

	# Build update dict with only provided fields
	update_dict = {}
	if intent_data.name is not None:
		update_dict["name"] = intent_data.name
	if intent_data.category_level_1_id is not None:
		update_dict["category_level_1_id"] = intent_data.category_level_1_id
	if intent_data.category_level_2_id is not None:
		update_dict["category_level_2_id"] = intent_data.category_level_2_id
	if intent_data.category_level_3_id is not None:
		update_dict["category_level_3_id"] = intent_data.category_level_3_id
	if intent_data.area is not None:
		update_dict["area"] = intent_data.area
	if intent_data.is_processed is not None:
		update_dict["is_processed"] = intent_data.is_processed
	if intent_data.variant_a_impressions is not None:
		update_dict["variant_a_impressions"] = intent_data.variant_a_impressions
	if intent_data.variant_b_impressions is not None:
		update_dict["variant_b_impressions"] = intent_data.variant_b_impressions
	if intent_data.variant_a_resolutions is not None:
		update_dict["variant_a_resolutions"] = intent_data.variant_a_resolutions
	if intent_data.variant_b_resolutions is not None:
		update_dict["variant_b_resolutions"] = intent_data.variant_b_resolutions

	if not update_dict:
		return intent

	stmt = update(Intent).where(Intent.id == intent_id).values(**update_dict)
	await db.execute(stmt)
	await db.commit()

	# Fetch updated intent
	await db.refresh(intent)
	return intent


async def delete_intent(db: AsyncSession, intent_id: int) -> bool:
	"""
	Delete an intent by ID.

	Args:
		db: Database session
		intent_id: Intent ID

	Returns:
		True if deleted, False if not found
	"""
	intent = await get_intent(db, intent_id)

	if not intent:
		return False

	await db.delete(intent)
	await db.commit()

	return True


async def increment_variant_impressions(
	db: AsyncSession, intent_id: int, variant: str
) -> bool:
	"""
	Increment the impressions count for a variant.

	Args:
		db: Database session
		intent_id: Intent ID
		variant: Variant ("A" or "B")

	Returns:
		True if incremented, False if not found
	"""
	intent = await get_intent(db, intent_id)
	if not intent:
		return False

	if variant == "A":
		intent.variant_a_impressions += 1
	elif variant == "B":
		intent.variant_b_impressions += 1
	else:
		return False

	await db.commit()
	return True


async def increment_variant_resolutions(
	db: AsyncSession, intent_id: int, variant: str
) -> bool:
	"""
	Increment the resolutions count for a variant.

	Args:
		db: Database session
		intent_id: Intent ID
		variant: Variant ("A" or "B")

	Returns:
		True if incremented, False if not found
	"""
	intent = await get_intent(db, intent_id)
	if not intent:
		return False

	if variant == "A":
		intent.variant_a_resolutions += 1
	elif variant == "B":
		intent.variant_b_resolutions += 1
	else:
		return False

	await db.commit()
	return True


async def get_ab_testing_totals(db: AsyncSession) -> dict[str, int]:
	"""
	Return summed impressions and resolutions across all intents.
	"""
	query = select(
		func.coalesce(func.sum(Intent.variant_a_impressions), 0).label(
			"variant_a_impressions"
		),
		func.coalesce(func.sum(Intent.variant_b_impressions), 0).label(
			"variant_b_impressions"
		),
		func.coalesce(func.sum(Intent.variant_a_resolutions), 0).label(
			"variant_a_resolutions"
		),
		func.coalesce(func.sum(Intent.variant_b_resolutions), 0).label(
			"variant_b_resolutions"
		),
	)
	result = await db.execute(query)
	row = result.one()

	return {
		"variant_a_impressions": row.variant_a_impressions,
		"variant_b_impressions": row.variant_b_impressions,
		"variant_a_resolutions": row.variant_a_resolutions,
		"variant_b_resolutions": row.variant_b_resolutions,
	}

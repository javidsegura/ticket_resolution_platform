from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from ai_ticket_platform.database.generated_models import Category
import logging

logger = logging.getLogger(__name__)

async def get_level_1_categories(db: AsyncSession) -> List[Category]:
	"""
	Fetch all level 1 categories (root categories with no parent).
	"""
	result = await db.execute(
		select(Category)
		.where(Category.level == 1)
		.order_by(Category.name)
	)
	return list(result.scalars().all())


async def get_level_2_categories_by_parent(db: AsyncSession, parent_id: int) -> List[Category]:
	"""
	Fetch all level 2 categories that are children of a specific level 1 category.
	"""
	result = await db.execute(
		select(Category)
		.where(Category.level == 2, Category.parent_id == parent_id)
		.order_by(Category.name)
	)
	return list(result.scalars().all())


async def get_level_3_categories_by_parent(db: AsyncSession, parent_id: int) -> List[Category]:
	"""
	Fetch all level 3 categories that are children of a specific level 2 category.
	"""
	result = await db.execute(
		select(Category)
		.where(Category.level == 3, Category.parent_id == parent_id)
		.order_by(Category.name)
	)
	return list(result.scalars().all())


async def create_category(
	db: AsyncSession,
	name: str,
	level: int,
	parent_id: Optional[int] = None
) -> Category:
	"""
	Create a new category.
	"""

	if level not in (1, 2, 3):
		raise ValueError("Category level must be between 1 and 3.")
	if level == 1 and parent_id is not None:
		raise ValueError("Level 1 categories cannot have a parent.")
	if level in (2, 3) and parent_id is None:
		raise ValueError("Level 2-3 categories require a parent_id.")

	try:
		category = Category(name=name, level=level, parent_id=parent_id)
		db.add(category)
		await db.commit()
		await db.refresh(category)
		logger.info(f"Created category: {name} (level {level}, parent_id {parent_id})")
		return category
	except Exception as e:
		await db.rollback()
		logger.error(f"Error creating category '{name}': {str(e)}")
		raise


async def get_or_create_category(
	db: AsyncSession,
	name: str,
	level: int,
	parent_id: Optional[int] = None
) -> tuple[Category, bool]:
	"""
	Get existing category or create if it doesn't exist.

	This function handles potential race conditions by using database constraints.

	Returns:
		Tuple of (Category, created) where created is True if newly created
	"""
	# Simplified query construction - SQLAlchemy handles None correctly
	query = select(Category).where(
		Category.name == name,
		Category.level == level,
		Category.parent_id == parent_id
	)

	result = await db.execute(query)
	try:
		category = result.scalar_one_or_none()
	except Exception as e:
		# Handle case where multiple rows exist (shouldn't happen, but just in case)
		logger.warning(f"Multiple categories found for name='{name}', level={level}, parent_id={parent_id}. Using first one.")
		result = await db.execute(query)
		category = result.scalars().first()

	if category:
		logger.debug(f"Found existing category: {name} (id={category.id})")
		return category, False

	# Try to create new category, handling race condition with IntegrityError
	try:
		logger.debug(f"Creating new category: {name} (level {level})")
		category = Category(name=name, level=level, parent_id=parent_id)
		db.add(category)
		await db.commit()
		await db.refresh(category)
		logger.info(f"Created category: {name} (level {level}, parent_id {parent_id})")
		return category, True
	except IntegrityError:
		await db.rollback()
		logger.warning(f"Race condition handled for category '{name}'. Fetching existing.")
		result = await db.execute(query)
		category = result.scalar_one_or_none()
		if category is None:
			raise RuntimeError(f"Category '{name}' not found after IntegrityError - concurrent deletion?")
		return category, False
	except Exception as e:
		await db.rollback()
		logger.error(f"Error in get_or_create_category for '{name}': {str(e)}")
		raise


async def get_category_by_id(db: AsyncSession, category_id: int) -> Optional[Category]:
	"""
	Fetch a single category by ID.
	"""
	result = await db.execute(select(Category).where(Category.id == category_id))
	return result.scalar_one_or_none()


async def get_all_categories(
	db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Category]:
	"""
	Retrieve all categories.
	"""
	result = await db.execute(
		select(Category).offset(skip).limit(limit).order_by(Category.created_at.desc())
	)
	return result.scalars().all()


async def update_category(
	db: AsyncSession, category_id: int, name: Optional[str] = None
) -> Optional[Category]:
	"""
	Update a category. Only name can be updated.

	Note: level and parent_id are immutable to prevent hierarchy manipulation.
	"""
	category = await get_category_by_id(db, category_id)

	if not category:
		return None

	if name is not None:
		category.name = name

	try:
		await db.commit()
		await db.refresh(category)
	except SQLAlchemyError as e:
		await db.rollback()
		raise RuntimeError(f"Failed to update category: {e}") from e

	return category


async def delete_category(db: AsyncSession, category_id: int) -> bool:
	"""
	Delete a category by ID.
	"""
	category = await get_category_by_id(db, category_id)
	if category:
		try:
			await db.delete(category)
			await db.commit()
		except SQLAlchemyError as e:
			await db.rollback()
			raise RuntimeError(f"Failed to delete category: {e}") from e
		return True
	return False

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
	try:
		# Try to find existing category
		query = select(Category).where(
			Category.name == name,
			Category.level == level
		)

		if parent_id is not None:
			query = query.where(Category.parent_id == parent_id)
		else:
			query = query.where(Category.parent_id.is_(None))

		result = await db.execute(query)
		category = result.scalar_one_or_none()

		if category:
			logger.debug(f"Found existing category: {name} (id={category.id})")
			return category, False

		# Create new category if it doesn't exist
		logger.debug(f"Creating new category: {name} (level {level})")
		new_category = await create_category(db, name, level, parent_id)
		return new_category, True
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



from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.database.generated_models import Category


async def create_category(
	db: AsyncSession, name: str, level: int, parent_id: Optional[int] = None
) -> Category:
	"""
	Create a new category.

	Args:
	    db: Database session
	    name: Category name
	    level: Category level (1-3)
	    parent_id: Parent category ID (required for levels 2-3, must be None for level 1)
	"""
	if level not in (1, 2, 3):
		raise ValueError("Category level must be between 1 and 3.")
	if level == 1 and parent_id is not None:
		raise ValueError("Level 1 categories cannot have a parent.")
	if level in (2, 3) and parent_id is None:
		raise ValueError("Level 2-3 categories require a parent_id.")

	db_category = Category(
		name=name,
		level=level,
		parent_id=parent_id,
	)
	try:
		db.add(db_category)
		await db.commit()
		await db.refresh(db_category)
	except SQLAlchemyError as e:
		await db.rollback()
		raise RuntimeError(f"Failed to create category: {e}") from e
	return db_category


async def get_category_by_id(db: AsyncSession, category_id: int) -> Optional[Category]:
	"""
	Retrieve a category by ID.
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

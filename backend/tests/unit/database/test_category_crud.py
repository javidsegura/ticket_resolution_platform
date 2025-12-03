"""Unit tests for category CRUD operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from ai_ticket_platform.database.CRUD.category import (
	create_category,
	get_category_by_id,
	get_all_categories,
	update_category,
	delete_category,
)


@pytest.mark.asyncio
class TestCreateCategory:
	"""Test create_category function."""

	async def test_create_category_level_1_success(self):
		"""Test successful creation of level 1 category."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.category.Category") as mock_cat:
			mock_category = MagicMock()
			mock_category.id = 1
			mock_category.name = "Hardware"
			mock_category.level = 1
			mock_category.parent_id = None
			mock_cat.return_value = mock_category

			result = await create_category(db=mock_db, name="Hardware", level=1)

			assert result.name == "Hardware"
			assert result.level == 1
			assert result.parent_id is None
			mock_db.add.assert_called_once_with(mock_category)
			mock_db.commit.assert_called_once()

	async def test_create_category_level_2_success(self):
		"""Test successful creation of level 2 category with parent."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.category.Category") as mock_cat:
			mock_category = MagicMock()
			mock_category.id = 2
			mock_category.name = "Laptops"
			mock_category.level = 2
			mock_category.parent_id = 1
			mock_cat.return_value = mock_category

			result = await create_category(
				db=mock_db, name="Laptops", level=2, parent_id=1
			)

			assert result.name == "Laptops"
			assert result.level == 2
			assert result.parent_id == 1
			mock_db.commit.assert_called_once()

	async def test_create_category_level_3_success(self):
		"""Test successful creation of level 3 category with parent."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.category.Category") as mock_cat:
			mock_category = MagicMock()
			mock_category.id = 3
			mock_category.name = "Dell Laptops"
			mock_category.level = 3
			mock_category.parent_id = 2
			mock_cat.return_value = mock_category

			result = await create_category(
				db=mock_db, name="Dell Laptops", level=3, parent_id=2
			)

			assert result.name == "Dell Laptops"
			assert result.level == 3
			mock_db.commit.assert_called_once()

	async def test_create_category_invalid_level(self):
		"""Test category creation with invalid level."""
		mock_db = MagicMock(spec=AsyncSession)

		with pytest.raises(ValueError, match="Category level must be between 1 and 3"):
			await create_category(db=mock_db, name="Test", level=4)

		with pytest.raises(ValueError, match="Category level must be between 1 and 3"):
			await create_category(db=mock_db, name="Test", level=0)

	async def test_create_category_level_1_with_parent(self):
		"""Test that level 1 category cannot have parent."""
		mock_db = MagicMock(spec=AsyncSession)

		with pytest.raises(
			ValueError, match="Level 1 categories cannot have a parent"
		):
			await create_category(db=mock_db, name="Test", level=1, parent_id=1)

	async def test_create_category_level_2_without_parent(self):
		"""Test that level 2 category requires parent."""
		mock_db = MagicMock(spec=AsyncSession)

		with pytest.raises(
			ValueError, match="Level 2-3 categories require a parent_id"
		):
			await create_category(db=mock_db, name="Test", level=2)

	async def test_create_category_level_3_without_parent(self):
		"""Test that level 3 category requires parent."""
		mock_db = MagicMock(spec=AsyncSession)

		with pytest.raises(
			ValueError, match="Level 2-3 categories require a parent_id"
		):
			await create_category(db=mock_db, name="Test", level=3)

	async def test_create_category_db_error(self):
		"""Test category creation with database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
		mock_db.rollback = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.category.Category"):
			with pytest.raises(RuntimeError, match="Failed to create category"):
				await create_category(db=mock_db, name="Test", level=1)

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestGetCategoryById:
	"""Test get_category_by_id function."""

	async def test_get_category_by_id_success(self):
		"""Test successful retrieval of category by ID."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_category = MagicMock()
		mock_category.id = 1
		mock_category.name = "Hardware"
		mock_result.scalar_one_or_none.return_value = mock_category

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_category_by_id(db=mock_db, category_id=1)

		assert result.id == 1
		assert result.name == "Hardware"
		mock_db.execute.assert_called_once()

	async def test_get_category_by_id_not_found(self):
		"""Test retrieval of non-existent category."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_category_by_id(db=mock_db, category_id=999)

		assert result is None


@pytest.mark.asyncio
class TestGetAllCategories:
	"""Test get_all_categories function."""

	async def test_get_all_categories_success(self):
		"""Test successful retrieval of all categories."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_category_1 = MagicMock()
		mock_category_1.id = 1
		mock_category_2 = MagicMock()
		mock_category_2.id = 2

		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [
			mock_category_1,
			mock_category_2,
		]

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_categories(db=mock_db, skip=0, limit=100)

		assert len(result) == 2
		assert result[0].id == 1
		assert result[1].id == 2
		mock_db.execute.assert_called_once()

	async def test_get_all_categories_empty(self):
		"""Test retrieval when no categories exist."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = []

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_categories(db=mock_db, skip=0, limit=100)

		assert len(result) == 0

	async def test_get_all_categories_with_pagination(self):
		"""Test retrieval with custom pagination."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_category = MagicMock()
		mock_category.id = 1

		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [mock_category]

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_categories(db=mock_db, skip=10, limit=5)

		assert len(result) == 1
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestUpdateCategory:
	"""Test update_category function."""

	async def test_update_category_name(self):
		"""Test updating category name."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		mock_category = MagicMock()
		mock_category.id = 1
		mock_category.name = "Old Name"

		with patch(
			"ai_ticket_platform.database.CRUD.category.get_category_by_id",
			new=AsyncMock(return_value=mock_category),
		):
			result = await update_category(db=mock_db, category_id=1, name="New Name")

			assert result.name == "New Name"
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once_with(mock_category)

	async def test_update_category_not_found(self):
		"""Test updating non-existent category."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch(
			"ai_ticket_platform.database.CRUD.category.get_category_by_id",
			new=AsyncMock(return_value=None),
		):
			result = await update_category(db=mock_db, category_id=999, name="New Name")

			assert result is None

	async def test_update_category_db_error(self):
		"""Test updating category with database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
		mock_db.rollback = AsyncMock()

		mock_category = MagicMock()
		mock_category.id = 1

		with patch(
			"ai_ticket_platform.database.CRUD.category.get_category_by_id",
			new=AsyncMock(return_value=mock_category),
		):
			with pytest.raises(RuntimeError, match="Failed to update category"):
				await update_category(db=mock_db, category_id=1, name="New Name")

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestDeleteCategory:
	"""Test delete_category function."""

	async def test_delete_category_success(self):
		"""Test successful deletion of category."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.delete = AsyncMock()
		mock_db.commit = AsyncMock()

		mock_category = MagicMock()
		mock_category.id = 1

		with patch(
			"ai_ticket_platform.database.CRUD.category.get_category_by_id",
			new=AsyncMock(return_value=mock_category),
		):
			result = await delete_category(db=mock_db, category_id=1)

			assert result is True
			mock_db.delete.assert_called_once_with(mock_category)
			mock_db.commit.assert_called_once()

	async def test_delete_category_not_found(self):
		"""Test deletion of non-existent category."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch(
			"ai_ticket_platform.database.CRUD.category.get_category_by_id",
			new=AsyncMock(return_value=None),
		):
			result = await delete_category(db=mock_db, category_id=999)

			assert result is False

	async def test_delete_category_db_error(self):
		"""Test deletion with database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.delete = AsyncMock()
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
		mock_db.rollback = AsyncMock()

		mock_category = MagicMock()
		mock_category.id = 1

		with patch(
			"ai_ticket_platform.database.CRUD.category.get_category_by_id",
			new=AsyncMock(return_value=mock_category),
		):
			with pytest.raises(RuntimeError, match="Failed to delete category"):
				await delete_category(db=mock_db, category_id=1)

			mock_db.rollback.assert_called_once()

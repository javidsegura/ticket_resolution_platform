"""Unit tests for intent CRUD operations (intent.py - singular)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ai_ticket_platform.database.CRUD.intent import (
	get_intent_by_category_path,
	create_intent,
	get_or_create_intent,
	get_intents_processing_status,
	get_all_intents_with_categories,
)


@pytest.mark.asyncio
class TestGetIntentByCategoryPath:
	"""Test get_intent_by_category_path operation."""

	async def test_get_intent_by_category_path_found(self):
		"""Test finding intent by category path."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.id = 1
		mock_intent.name = "Login Issues"

		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=mock_intent)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_intent_by_category_path(
			db=mock_db,
			category_level_1_id=1,
			category_level_2_id=2,
			category_level_3_id=3
		)

		assert result == mock_intent
		assert result.id == 1
		mock_db.execute.assert_called_once()

	async def test_get_intent_by_category_path_not_found(self):
		"""Test category path not found returns None."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=None)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_intent_by_category_path(
			db=mock_db,
			category_level_1_id=99,
			category_level_2_id=99,
			category_level_3_id=99
		)

		assert result is None
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestCreateIntent:
	"""Test create_intent operation."""

	async def test_create_intent_success(self):
		"""Test successful intent creation."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()
		mock_db.rollback = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.intent.Intent") as mock_intent_class:
			mock_intent = MagicMock()
			mock_intent.id = 1
			mock_intent.name = "Login Issues"
			mock_intent_class.return_value = mock_intent

			result = await create_intent(
				db=mock_db,
				name="Login Issues",
				category_level_1_id=1,
				category_level_2_id=2,
				category_level_3_id=3,
				area="Tech"
			)

			assert result == mock_intent
			mock_db.add.assert_called_once_with(mock_intent)
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once()
			mock_db.rollback.assert_not_called()

	async def test_create_intent_without_area(self):
		"""Test creating intent without area field."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.intent.Intent") as mock_intent_class:
			mock_intent = MagicMock()
			mock_intent_class.return_value = mock_intent

			result = await create_intent(
				db=mock_db,
				name="Test Intent",
				category_level_1_id=1,
				category_level_2_id=2,
				category_level_3_id=3
			)

			assert result == mock_intent
			call_kwargs = mock_intent_class.call_args[1]
			assert call_kwargs["area"] is None
			assert call_kwargs["is_processed"] is False

	async def test_create_intent_database_error(self):
		"""Test handling database error during creation."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock(side_effect=Exception("DB Error"))
		mock_db.rollback = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.intent.Intent"):
			with pytest.raises(Exception, match="DB Error"):
				await create_intent(
					db=mock_db,
					name="Test",
					category_level_1_id=1,
					category_level_2_id=2,
					category_level_3_id=3
				)

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestGetOrCreateIntent:
	"""Test get_or_create_intent operation."""

	async def test_get_or_create_intent_existing(self):
		"""Test returning existing intent."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.id = 1
		mock_intent.name = "Existing Intent"

		with patch("ai_ticket_platform.database.CRUD.intent.get_intent_by_category_path", new=AsyncMock(return_value=mock_intent)):
			result, created = await get_or_create_intent(
				db=mock_db,
				name="New Name",
				category_level_1_id=1,
				category_level_2_id=2,
				category_level_3_id=3
			)

			assert result == mock_intent
			assert created is False

	async def test_get_or_create_intent_create_new(self):
		"""Test creating new intent when none exists."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		mock_new_intent = MagicMock()
		mock_new_intent.id = 1
		mock_new_intent.name = "New Intent"

		with patch("ai_ticket_platform.database.CRUD.intent.get_intent_by_category_path", new=AsyncMock(return_value=None)):
			with patch("ai_ticket_platform.database.CRUD.intent.Intent") as mock_intent_class:
				mock_intent_class.return_value = mock_new_intent

				result, created = await get_or_create_intent(
					db=mock_db,
					name="New Intent",
					category_level_1_id=1,
					category_level_2_id=2,
					category_level_3_id=3,
					area="Finance"
				)

				assert result == mock_new_intent
				assert created is True
				mock_db.add.assert_called_once()
				mock_db.commit.assert_called_once()

	async def test_get_or_create_intent_race_condition(self):
		"""Test handling race condition with IntegrityError."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock(side_effect=IntegrityError(None, None, None))
		mock_db.rollback = AsyncMock()

		mock_existing_intent = MagicMock()
		mock_existing_intent.id = 1
		mock_existing_intent.name = "Existing"

		with patch("ai_ticket_platform.database.CRUD.intent.get_intent_by_category_path") as mock_get:
			# First call returns None (doesn't exist), second call returns existing (after race condition)
			mock_get.side_effect = [None, mock_existing_intent]

			with patch("ai_ticket_platform.database.CRUD.intent.Intent"):
				result, created = await get_or_create_intent(
					db=mock_db,
					name="Test",
					category_level_1_id=1,
					category_level_2_id=2,
					category_level_3_id=3
				)

				assert result == mock_existing_intent
				assert created is False
				mock_db.rollback.assert_called_once()
				assert mock_get.call_count == 2

	async def test_get_or_create_intent_race_condition_still_not_found(self):
		"""Test race condition where intent still not found after rollback."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock(side_effect=IntegrityError(None, None, None))
		mock_db.rollback = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.intent.get_intent_by_category_path") as mock_get:
			# Both calls return None
			mock_get.side_effect = [None, None]

			with patch("ai_ticket_platform.database.CRUD.intent.Intent"):
				with pytest.raises(RuntimeError, match="Intent not found for category path"):
					await get_or_create_intent(
						db=mock_db,
						name="Test",
						category_level_1_id=1,
						category_level_2_id=2,
						category_level_3_id=3
					)

	async def test_get_or_create_intent_general_error(self):
		"""Test handling general database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock(side_effect=Exception("Unexpected error"))
		mock_db.rollback = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.intent.get_intent_by_category_path", new=AsyncMock(return_value=None)):
			with patch("ai_ticket_platform.database.CRUD.intent.Intent"):
				with pytest.raises(Exception, match="Unexpected error"):
					await get_or_create_intent(
						db=mock_db,
						name="Test",
						category_level_1_id=1,
						category_level_2_id=2,
						category_level_3_id=3
					)

				mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestGetIntentsProcessingStatus:
	"""Test get_intents_processing_status operation."""

	async def test_get_intents_processing_status_success(self):
		"""Test retrieving processing status for multiple intents."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.all = MagicMock(return_value=[
			(1, True),
			(2, False),
			(3, True)
		])
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_intents_processing_status(db=mock_db, intent_ids=[1, 2, 3])

		assert result == {1: True, 2: False, 3: True}
		mock_db.execute.assert_called_once()

	async def test_get_intents_processing_status_empty_list(self):
		"""Test with empty intent ID list."""
		mock_db = MagicMock(spec=AsyncSession)

		result = await get_intents_processing_status(db=mock_db, intent_ids=[])

		assert result == {}
		# execute should not be called for empty list
		assert not mock_db.execute.called

	async def test_get_intents_processing_status_single_intent(self):
		"""Test with single intent ID."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.all = MagicMock(return_value=[(5, False)])
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_intents_processing_status(db=mock_db, intent_ids=[5])

		assert result == {5: False}
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestGetAllIntentsWithCategories:
	"""Test get_all_intents_with_categories operation."""

	async def test_get_all_intents_with_categories_success(self):
		"""Test retrieving all intents with complete category hierarchy."""
		mock_db = MagicMock(spec=AsyncSession)

		# Mock category objects
		mock_cat_l1 = MagicMock()
		mock_cat_l1.id = 1
		mock_cat_l1.name = "Tech"

		mock_cat_l2 = MagicMock()
		mock_cat_l2.id = 2
		mock_cat_l2.name = "Authentication"

		mock_cat_l3 = MagicMock()
		mock_cat_l3.id = 3
		mock_cat_l3.name = "Login"

		# Mock intent
		mock_intent = MagicMock()
		mock_intent.id = 10
		mock_intent.name = "Login Issues"
		mock_intent.category_level_1_id = 1
		mock_intent.category_level_2_id = 2
		mock_intent.category_level_3_id = 3
		mock_intent.category_level_1 = mock_cat_l1
		mock_intent.category_level_2 = mock_cat_l2
		mock_intent.category_level_3 = mock_cat_l3

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_intent])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_intents_with_categories(db=mock_db)

		assert len(result) == 1
		assert result[0]["intent_id"] == 10
		assert result[0]["intent_name"] == "Login Issues"
		assert result[0]["category_l1_id"] == 1
		assert result[0]["category_l1_name"] == "Tech"
		assert result[0]["category_l2_id"] == 2
		assert result[0]["category_l2_name"] == "Authentication"
		assert result[0]["category_l3_id"] == 3
		assert result[0]["category_l3_name"] == "Login"
		mock_db.execute.assert_called_once()

	async def test_get_all_intents_skips_incomplete_categories(self):
		"""Test that intents with missing category levels are skipped."""
		mock_db = MagicMock(spec=AsyncSession)

		# Mock complete intent
		mock_cat_l1 = MagicMock()
		mock_cat_l1.id = 1
		mock_cat_l1.name = "Tech"
		mock_cat_l2 = MagicMock()
		mock_cat_l2.id = 2
		mock_cat_l2.name = "Auth"
		mock_cat_l3 = MagicMock()
		mock_cat_l3.id = 3
		mock_cat_l3.name = "Login"

		mock_intent_complete = MagicMock()
		mock_intent_complete.id = 1
		mock_intent_complete.name = "Complete"
		mock_intent_complete.category_level_1_id = 1
		mock_intent_complete.category_level_2_id = 2
		mock_intent_complete.category_level_3_id = 3
		mock_intent_complete.category_level_1 = mock_cat_l1
		mock_intent_complete.category_level_2 = mock_cat_l2
		mock_intent_complete.category_level_3 = mock_cat_l3

		# Mock incomplete intent (missing L3)
		mock_intent_incomplete = MagicMock()
		mock_intent_incomplete.id = 2
		mock_intent_incomplete.name = "Incomplete"
		mock_intent_incomplete.category_level_1_id = 1
		mock_intent_incomplete.category_level_2_id = 2
		mock_intent_incomplete.category_level_3_id = None
		mock_intent_incomplete.category_level_1 = mock_cat_l1
		mock_intent_incomplete.category_level_2 = mock_cat_l2
		mock_intent_incomplete.category_level_3 = None

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_intent_complete, mock_intent_incomplete])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_intents_with_categories(db=mock_db)

		# Only complete intent should be included
		assert len(result) == 1
		assert result[0]["intent_id"] == 1
		assert result[0]["intent_name"] == "Complete"

	async def test_get_all_intents_empty_database(self):
		"""Test with no intents in database."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_intents_with_categories(db=mock_db)

		assert result == []
		mock_db.execute.assert_called_once()

	async def test_get_all_intents_multiple_intents(self):
		"""Test with multiple complete intents."""
		mock_db = MagicMock(spec=AsyncSession)

		# Create mock intents with categories
		intents = []
		for i in range(3):
			mock_cat_l1 = MagicMock(id=i+1, name=f"Cat1_{i}")
			mock_cat_l2 = MagicMock(id=i+10, name=f"Cat2_{i}")
			mock_cat_l3 = MagicMock(id=i+20, name=f"Cat3_{i}")

			mock_intent = MagicMock()
			mock_intent.id = i
			mock_intent.name = f"Intent_{i}"
			mock_intent.category_level_1_id = i+1
			mock_intent.category_level_2_id = i+10
			mock_intent.category_level_3_id = i+20
			mock_intent.category_level_1 = mock_cat_l1
			mock_intent.category_level_2 = mock_cat_l2
			mock_intent.category_level_3 = mock_cat_l3
			intents.append(mock_intent)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=intents)
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_intents_with_categories(db=mock_db)

		assert len(result) == 3
		for i in range(3):
			assert result[i]["intent_id"] == i
			assert result[i]["intent_name"] == f"Intent_{i}"

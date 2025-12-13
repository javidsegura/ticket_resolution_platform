"""Unit tests for intents CRUD operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.database.CRUD.intents import (
	create_intent,
	get_intent,
	list_intents,
	update_intent,
	delete_intent,
	increment_variant_impressions,
	increment_variant_resolutions,
	get_ab_testing_totals
)
from ai_ticket_platform.schemas.endpoints.intent import IntentCreate, IntentUpdate


@pytest.mark.asyncio
class TestCreateIntent:
	"""Test create_intent operation."""

	async def test_create_intent_success(self):
		"""Test successful creation of intent."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		intent_data = IntentCreate(
			name="Login Issues",
			category_level_1_id=1,
			category_level_2_id=2,
			category_level_3_id=3,
			area="Support",
			is_processed=False,
			variant_a_impressions=0,
			variant_b_impressions=0,
			variant_a_resolutions=0,
			variant_b_resolutions=0
		)

		with patch("ai_ticket_platform.database.CRUD.intents.Intent") as mock_intent_class:
			mock_intent = MagicMock()
			mock_intent.id = 1
			mock_intent_class.return_value = mock_intent

			result = await create_intent(db=mock_db, intent_data=intent_data)

			assert result == mock_intent
			mock_db.add.assert_called_once_with(mock_intent)
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once_with(mock_intent)

	async def test_create_intent_with_minimal_fields(self):
		"""Test creating intent with minimal required fields."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		intent_data = IntentCreate(
			name="Test Intent",
			category_level_1_id=1,
			is_processed=False,
			variant_a_impressions=0,
			variant_b_impressions=0,
			variant_a_resolutions=0,
			variant_b_resolutions=0
		)

		with patch("ai_ticket_platform.database.CRUD.intents.Intent") as mock_intent_class:
			mock_intent = MagicMock()
			mock_intent_class.return_value = mock_intent

			await create_intent(db=mock_db, intent_data=intent_data)

			call_kwargs = mock_intent_class.call_args[1]
			assert call_kwargs["name"] == "Test Intent"
			assert call_kwargs["category_level_1_id"] == 1
			assert call_kwargs["is_processed"] is False


@pytest.mark.asyncio
class TestGetIntent:
	"""Test get_intent by ID operation."""

	async def test_get_intent_found(self):
		"""Test successful retrieval of intent by ID."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.id = 1
		mock_intent.name = "Test Intent"

		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=mock_intent)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_intent(db=mock_db, intent_id=1)

		assert result == mock_intent
		assert result.id == 1
		mock_db.execute.assert_called_once()

	async def test_get_intent_not_found(self):
		"""Test intent not found returns None."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=None)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_intent(db=mock_db, intent_id=999)

		assert result is None
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestListIntents:
	"""Test list_intents with pagination and filtering."""

	async def test_list_intents_default_pagination(self):
		"""Test listing intents with default pagination."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent_1 = MagicMock(id=1, name="Intent 1")
		mock_intent_2 = MagicMock(id=2, name="Intent 2")

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_intent_1, mock_intent_2])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await list_intents(db=mock_db)

		assert len(result) == 2
		assert result[0].id == 1
		assert result[1].id == 2
		mock_db.execute.assert_called_once()

	async def test_list_intents_with_is_processed_filter(self):
		"""Test listing intents filtered by is_processed status."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock(id=1, is_processed=True)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_intent])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await list_intents(db=mock_db, is_processed=True)

		assert len(result) == 1
		assert result[0].is_processed is True
		mock_db.execute.assert_called_once()

	async def test_list_intents_custom_pagination(self):
		"""Test listing intents with custom skip and limit."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await list_intents(db=mock_db, skip=10, limit=5)

		assert result == []
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestUpdateIntent:
	"""Test update_intent operation."""

	async def test_update_intent_success(self):
		"""Test successfully updating intent."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.id = 1
		mock_intent.name = "Old Name"

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			mock_db.execute = AsyncMock()
			mock_db.commit = AsyncMock()
			mock_db.refresh = AsyncMock()

			intent_update = IntentUpdate(name="New Name")

			result = await update_intent(db=mock_db, intent_id=1, intent_data=intent_update)

			assert result == mock_intent
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once()

	async def test_update_intent_not_found(self):
		"""Test updating intent when intent doesn't exist."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=None)):
			intent_update = IntentUpdate(name="New Name")

			result = await update_intent(db=mock_db, intent_id=999, intent_data=intent_update)

			assert result is None

	async def test_update_intent_no_changes(self):
		"""Test updating intent with no fields provided."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.id = 1

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			intent_update = IntentUpdate()

			result = await update_intent(db=mock_db, intent_id=1, intent_data=intent_update)

			assert result == mock_intent

	async def test_update_intent_multiple_fields(self):
		"""Test updating multiple intent fields."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.id = 1

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			mock_db.execute = AsyncMock()
			mock_db.commit = AsyncMock()
			mock_db.refresh = AsyncMock()

			intent_update = IntentUpdate(
				name="Updated Name",
				area="New Area",
				is_processed=True
			)

			result = await update_intent(db=mock_db, intent_id=1, intent_data=intent_update)

			assert result == mock_intent
			mock_db.execute.assert_called_once()

	async def test_update_intent_category_levels(self):
		"""Test updating intent with category level IDs."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.id = 1

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			mock_db.execute = AsyncMock()
			mock_db.commit = AsyncMock()
			mock_db.refresh = AsyncMock()

			intent_update = IntentUpdate(
				category_level_1_id=5,
				category_level_2_id=10,
				category_level_3_id=15
			)

			result = await update_intent(db=mock_db, intent_id=1, intent_data=intent_update)

			assert result == mock_intent
			mock_db.execute.assert_called_once()
			mock_db.commit.assert_called_once()

	async def test_update_intent_variant_metrics(self):
		"""Test updating intent with variant impressions and resolutions."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.id = 1

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			mock_db.execute = AsyncMock()
			mock_db.commit = AsyncMock()
			mock_db.refresh = AsyncMock()

			intent_update = IntentUpdate(
				variant_a_impressions=100,
				variant_b_impressions=150,
				variant_a_resolutions=25,
				variant_b_resolutions=30
			)

			result = await update_intent(db=mock_db, intent_id=1, intent_data=intent_update)

			assert result == mock_intent
			mock_db.execute.assert_called_once()
			mock_db.commit.assert_called_once()


@pytest.mark.asyncio
class TestDeleteIntent:
	"""Test delete_intent operation."""

	async def test_delete_intent_success(self):
		"""Test successfully deleting intent."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.id = 1

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			mock_db.delete = AsyncMock()
			mock_db.commit = AsyncMock()

			result = await delete_intent(db=mock_db, intent_id=1)

			assert result is True
			mock_db.delete.assert_called_once_with(mock_intent)
			mock_db.commit.assert_called_once()

	async def test_delete_intent_not_found(self):
		"""Test deleting intent when intent doesn't exist."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=None)):
			result = await delete_intent(db=mock_db, intent_id=999)

			assert result is False


@pytest.mark.asyncio
class TestIncrementVariantImpressions:
	"""Test increment_variant_impressions for A/B testing."""

	async def test_increment_variant_a_impressions(self):
		"""Test incrementing variant A impressions."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.variant_a_impressions = 5
		mock_intent.variant_b_impressions = 3

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			mock_db.commit = AsyncMock()

			result = await increment_variant_impressions(db=mock_db, intent_id=1, variant="A")

			assert result is True
			assert mock_intent.variant_a_impressions == 6
			mock_db.commit.assert_called_once()

	async def test_increment_variant_b_impressions(self):
		"""Test incrementing variant B impressions."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.variant_a_impressions = 5
		mock_intent.variant_b_impressions = 3

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			mock_db.commit = AsyncMock()

			result = await increment_variant_impressions(db=mock_db, intent_id=1, variant="B")

			assert result is True
			assert mock_intent.variant_b_impressions == 4
			mock_db.commit.assert_called_once()

	async def test_increment_impressions_intent_not_found(self):
		"""Test incrementing impressions when intent doesn't exist."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=None)):
			result = await increment_variant_impressions(db=mock_db, intent_id=999, variant="A")

			assert result is False

	async def test_increment_impressions_invalid_variant(self):
		"""Test incrementing impressions with invalid variant."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.variant_a_impressions = 5

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			result = await increment_variant_impressions(db=mock_db, intent_id=1, variant="C")

			assert result is False


@pytest.mark.asyncio
class TestIncrementVariantResolutions:
	"""Test increment_variant_resolutions for A/B testing."""

	async def test_increment_variant_a_resolutions(self):
		"""Test incrementing variant A resolutions."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.variant_a_resolutions = 2
		mock_intent.variant_b_resolutions = 1

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			mock_db.commit = AsyncMock()

			result = await increment_variant_resolutions(db=mock_db, intent_id=1, variant="A")

			assert result is True
			assert mock_intent.variant_a_resolutions == 3
			mock_db.commit.assert_called_once()

	async def test_increment_variant_b_resolutions(self):
		"""Test incrementing variant B resolutions."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.variant_a_resolutions = 2
		mock_intent.variant_b_resolutions = 1

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			mock_db.commit = AsyncMock()

			result = await increment_variant_resolutions(db=mock_db, intent_id=1, variant="B")

			assert result is True
			assert mock_intent.variant_b_resolutions == 2
			mock_db.commit.assert_called_once()

	async def test_increment_resolutions_intent_not_found(self):
		"""Test incrementing resolutions when intent doesn't exist."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=None)):
			result = await increment_variant_resolutions(db=mock_db, intent_id=999, variant="A")

			assert result is False

	async def test_increment_resolutions_invalid_variant(self):
		"""Test incrementing resolutions with invalid variant."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_intent = MagicMock()
		mock_intent.variant_a_resolutions = 2

		with patch("ai_ticket_platform.database.CRUD.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			result = await increment_variant_resolutions(db=mock_db, intent_id=1, variant="X")

			assert result is False


@pytest.mark.asyncio
class TestGetABTestingTotals:
	"""Test get_ab_testing_totals for aggregated A/B metrics."""

	async def test_get_ab_testing_totals_with_data(self):
		"""Test getting aggregated A/B testing totals."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_row = MagicMock()
		mock_row.variant_a_impressions = 100
		mock_row.variant_b_impressions = 95
		mock_row.variant_a_resolutions = 20
		mock_row.variant_b_resolutions = 25

		mock_result = MagicMock()
		mock_result.one = MagicMock(return_value=mock_row)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_ab_testing_totals(db=mock_db)

		assert result["variant_a_impressions"] == 100
		assert result["variant_b_impressions"] == 95
		assert result["variant_a_resolutions"] == 20
		assert result["variant_b_resolutions"] == 25
		mock_db.execute.assert_called_once()

	async def test_get_ab_testing_totals_empty_database(self):
		"""Test getting totals when no intents exist."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_row = MagicMock()
		mock_row.variant_a_impressions = 0
		mock_row.variant_b_impressions = 0
		mock_row.variant_a_resolutions = 0
		mock_row.variant_b_resolutions = 0

		mock_result = MagicMock()
		mock_result.one = MagicMock(return_value=mock_row)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_ab_testing_totals(db=mock_db)

		assert result["variant_a_impressions"] == 0
		assert result["variant_b_impressions"] == 0
		assert result["variant_a_resolutions"] == 0
		assert result["variant_b_resolutions"] == 0

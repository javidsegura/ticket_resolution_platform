"""Unit tests for intent schema validation."""

import pytest
from pydantic import ValidationError
from unittest.mock import MagicMock


class TestIntentCategoryValidator:
	"""Test IntentBase category level validation."""

	def test_category_level_none_is_valid(self):
		"""Test that None category level is accepted."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentBase

		intent = IntentBase(
			name="Test Intent",
			category_level_1_id=None,
			category_level_2_id=None,
			category_level_3_id=None
		)

		assert intent.category_level_1_id is None
		assert intent.category_level_2_id is None
		assert intent.category_level_3_id is None

	def test_category_level_validation_without_db_context(self):
		"""Test that validation is skipped when no DB context is provided."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentBase

		# Without DB context, validation should pass
		intent = IntentBase(
			name="Test Intent",
			category_level_1_id=1,
			category_level_2_id=2,
			category_level_3_id=3
		)

		assert intent.category_level_1_id == 1
		assert intent.category_level_2_id == 2
		assert intent.category_level_3_id == 3

	def test_category_level_1_validation_with_db_valid(self):
		"""Test category level 1 validation with valid category."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentBase

		mock_db = MagicMock()
		mock_category = MagicMock()
		mock_category.id = 1
		mock_category.level = 1

		mock_db.query.return_value.filter_by.return_value.first.return_value = mock_category

		intent = IntentBase.model_validate(
			{
				"name": "Test Intent",
				"category_level_1_id": 1
			},
			context={"db": mock_db}
		)

		assert intent.category_level_1_id == 1

	def test_category_level_validation_category_not_exists(self):
		"""Test validation fails when category doesn't exist."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentBase

		mock_db = MagicMock()
		mock_db.query.return_value.filter_by.return_value.first.return_value = None

		with pytest.raises(ValidationError) as exc_info:
			IntentBase.model_validate(
				{
					"name": "Test Intent",
					"category_level_1_id": 999
				},
				context={"db": mock_db}
			)

		errors = exc_info.value.errors()
		assert any("does not exist" in str(error) for error in errors)

	def test_category_level_validation_wrong_level(self):
		"""Test validation fails when category level doesn't match."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentBase

		mock_db = MagicMock()
		mock_category = MagicMock()
		mock_category.id = 1
		mock_category.level = 2  # Wrong level - should be 1

		mock_db.query.return_value.filter_by.return_value.first.return_value = mock_category

		with pytest.raises(ValidationError) as exc_info:
			IntentBase.model_validate(
				{
					"name": "Test Intent",
					"category_level_1_id": 1
				},
				context={"db": mock_db}
			)

		errors = exc_info.value.errors()
		assert any("level" in str(error).lower() for error in errors)

	def test_category_level_2_validation_with_db_valid(self):
		"""Test category level 2 validation with valid category."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentBase

		mock_db = MagicMock()
		mock_category = MagicMock()
		mock_category.id = 2
		mock_category.level = 2

		mock_db.query.return_value.filter_by.return_value.first.return_value = mock_category

		intent = IntentBase.model_validate(
			{
				"name": "Test Intent",
				"category_level_2_id": 2
			},
			context={"db": mock_db}
		)

		assert intent.category_level_2_id == 2

	def test_category_level_3_validation_with_db_valid(self):
		"""Test category level 3 validation with valid category."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentBase

		mock_db = MagicMock()
		mock_category = MagicMock()
		mock_category.id = 3
		mock_category.level = 3

		mock_db.query.return_value.filter_by.return_value.first.return_value = mock_category

		intent = IntentBase.model_validate(
			{
				"name": "Test Intent",
				"category_level_3_id": 3
			},
			context={"db": mock_db}
		)

		assert intent.category_level_3_id == 3


class TestIntentCreate:
	"""Test IntentCreate schema."""

	def test_intent_create_valid(self):
		"""Test creating valid IntentCreate."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentCreate

		intent = IntentCreate(
			name="Test Intent",
			category_level_1_id=1
		)

		assert intent.name == "Test Intent"
		assert intent.category_level_1_id == 1

	def test_intent_create_missing_required_field(self):
		"""Test IntentCreate with missing required fields."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentCreate

		with pytest.raises(ValidationError):
			IntentCreate(name="Test Intent")  # Missing category_level_1_id


class TestIntentUpdate:
	"""Test IntentUpdate schema."""

	def test_intent_update_all_none(self):
		"""Test IntentUpdate with all fields as None."""
		from ai_ticket_platform.schemas.endpoints.intent import IntentUpdate

		intent = IntentUpdate()

		assert intent.name is None
		assert intent.category_level_1_id is None
		assert intent.is_processed is None

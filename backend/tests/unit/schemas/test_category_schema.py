"""Unit tests for category schema validation."""

import pytest
from pydantic import ValidationError


class TestCategoryBaseValidator:
	"""Test CategoryBase model validator."""

	def test_level_1_with_parent_raises_error(self):
		"""Test that level 1 category with parent raises ValidationError."""
		from ai_ticket_platform.schemas.endpoints.category import CategoryBase

		with pytest.raises(ValidationError) as exc_info:
			CategoryBase(name="Test Category", level=1, parent_id=5)

		errors = exc_info.value.errors()
		assert any("Level 1 categories cannot have a parent" in str(error) for error in errors)

	def test_level_2_without_parent_raises_error(self):
		"""Test that level 2 category without parent raises ValidationError."""
		from ai_ticket_platform.schemas.endpoints.category import CategoryBase

		with pytest.raises(ValidationError) as exc_info:
			CategoryBase(name="Test Category", level=2, parent_id=None)

		errors = exc_info.value.errors()
		assert any("Level 2 categories must have a parent" in str(error) for error in errors)

	def test_level_3_without_parent_raises_error(self):
		"""Test that level 3 category without parent raises ValidationError."""
		from ai_ticket_platform.schemas.endpoints.category import CategoryBase

		with pytest.raises(ValidationError) as exc_info:
			CategoryBase(name="Test Category", level=3, parent_id=None)

		errors = exc_info.value.errors()
		assert any("Level 3 categories must have a parent" in str(error) for error in errors)

	def test_level_1_without_parent_is_valid(self):
		"""Test that level 1 category without parent is valid."""
		from ai_ticket_platform.schemas.endpoints.category import CategoryBase

		category = CategoryBase(name="Test Category", level=1, parent_id=None)

		assert category.name == "Test Category"
		assert category.level == 1
		assert category.parent_id is None

	def test_level_2_with_parent_is_valid(self):
		"""Test that level 2 category with parent is valid."""
		from ai_ticket_platform.schemas.endpoints.category import CategoryBase

		category = CategoryBase(name="Test Category", level=2, parent_id=1)

		assert category.name == "Test Category"
		assert category.level == 2
		assert category.parent_id == 1

	def test_level_3_with_parent_is_valid(self):
		"""Test that level 3 category with parent is valid."""
		from ai_ticket_platform.schemas.endpoints.category import CategoryBase

		category = CategoryBase(name="Test Category", level=3, parent_id=5)

		assert category.name == "Test Category"
		assert category.level == 3
		assert category.parent_id == 5

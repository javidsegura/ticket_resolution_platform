"""Tests for Category schema validation"""
import pytest
from pydantic import ValidationError
from ai_ticket_platform.schemas.endpoints.category import CategoryCreate, CategoryUpdate, CategoryRead


class TestCategoryCreate:
    """Test CategoryCreate validation"""

    def test_level_1_valid(self):
        """Test valid level 1 category without parent"""
        category = CategoryCreate(name="Root", level=1)
        assert category.level == 1
        assert category.parent_id is None

    def test_level_2_with_parent(self):
        """Test level 2 requires parent"""
        category = CategoryCreate(name="Sub", level=2, parent_id=1)
        assert category.level == 2
        assert category.parent_id == 1

    def test_level_3_with_parent(self):
        """Test level 3 requires parent"""
        category = CategoryCreate(name="SubSub", level=3, parent_id=2)
        assert category.level == 3

    def test_name_validation(self):
        """Test name length constraints"""
        with pytest.raises(ValidationError):
            CategoryCreate(name="", level=1)
        with pytest.raises(ValidationError):
            CategoryCreate(name="x" * 256, level=1)

    def test_level_range(self):
        """Test level must be 1-3"""
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", level=0)
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", level=4)

    def test_parent_id_validation(self):
        """Test parent_id must be positive"""
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", level=2, parent_id=0)
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", level=2, parent_id=-1)

    def test_level_1_cannot_have_parent(self):
        """Test level 1 rejects parent_id"""
        with pytest.raises(ValidationError):
            CategoryCreate(name="Root", level=1, parent_id=1)


class TestCategoryUpdate:
    """Test CategoryUpdate validation"""

    def test_all_optional(self):
        """Test all fields are optional"""
        category = CategoryUpdate()
        assert category.name is None
        assert category.level is None
        assert category.parent_id is None

    def test_partial_update(self):
        """Test updating individual fields"""
        cat1 = CategoryUpdate(name="Updated")
        assert cat1.name == "Updated"
        assert cat1.level is None

    def test_validation_on_provided_fields(self):
        """Test validation only on provided fields"""
        with pytest.raises(ValidationError):
            CategoryUpdate(name="")
        with pytest.raises(ValidationError):
            CategoryUpdate(level=5)


class TestCategoryRead:
    """Test CategoryRead validation"""

    def test_read_structure(self):
        """Test CategoryRead has required fields"""
        category = CategoryRead(
            id=1, name="Test", level=1, created_at="2024-01-01T00:00:00"
        )
        assert category.id == 1
        assert category.name == "Test"

    def test_id_required(self):
        """Test id is required"""
        with pytest.raises(ValidationError):
            CategoryRead(name="Test", level=1, created_at="2024-01-01T00:00:00")
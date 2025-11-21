"""Tests for Intent schema validation"""
import pytest
from pydantic import ValidationError
from ai_ticket_platform.schemas.endpoints.intent import IntentCreate, IntentUpdate, IntentRead


class TestIntentCreate:
    """Test IntentCreate validation"""

    def test_valid_creation(self):
        """Test valid intent creation"""
        intent = IntentCreate(
            name="User Login Issue",
            category_level_1_id=1
        )
        assert intent.name == "User Login Issue"
        assert intent.category_level_1_id == 1
        assert intent.is_processed is False

    def test_name_validation(self):
        """Test name length constraints"""
        with pytest.raises(ValidationError):
            IntentCreate(name="", category_level_1_id=1)
        with pytest.raises(ValidationError):
            IntentCreate(name="x" * 256, category_level_1_id=1)

    def test_category_level_1_required(self):
        """Test category_level_1_id is required"""
        with pytest.raises(ValidationError):
            IntentCreate(name="Test")

    def test_category_id_validation(self):
        """Test category IDs must be positive"""
        with pytest.raises(ValidationError):
            IntentCreate(name="Test", category_level_1_id=0)
        with pytest.raises(ValidationError):
            IntentCreate(name="Test", category_level_1_id=1, category_level_2_id=0)
        with pytest.raises(ValidationError):
            IntentCreate(name="Test", category_level_1_id=1, category_level_3_id=-1)

    def test_area_validation(self):
        """Test area length constraints"""
        with pytest.raises(ValidationError):
            IntentCreate(name="Test", category_level_1_id=1, area="")
        with pytest.raises(ValidationError):
            IntentCreate(name="Test", category_level_1_id=1, area="x" * 256)

    def test_full_hierarchy(self):
        """Test intent with all category levels"""
        intent = IntentCreate(
            name="Complex Issue",
            category_level_1_id=1,
            category_level_2_id=2,
            category_level_3_id=3,
            area="Backend",
            is_processed=True
        )
        assert intent.category_level_3_id == 3
        assert intent.is_processed is True


class TestIntentUpdate:
    """Test IntentUpdate validation"""

    def test_all_optional(self):
        """Test all fields are optional"""
        intent = IntentUpdate()
        assert intent.name is None
        assert intent.category_level_1_id is None
        assert intent.is_processed is None

    def test_field_updates(self):
        """Test partial field updates"""
        intent = IntentUpdate(name="Updated")
        assert intent.name == "Updated"

        intent = IntentUpdate(category_level_1_id=2)
        assert intent.category_level_1_id == 2

    def test_validation(self):
        """Test validation on updates"""
        with pytest.raises(ValidationError):
            IntentUpdate(name="")
        with pytest.raises(ValidationError):
            IntentUpdate(category_level_1_id=0)


class TestIntentRead:
    """Test IntentRead validation"""

    def test_read_structure(self):
        """Test IntentRead structure"""
        intent = IntentRead(
            id=1,
            name="Test Issue",
            category_level_1_id=1,
            created_at="2024-01-01T00:00:00"
        )
        assert intent.id == 1
        assert intent.name == "Test Issue"

    def test_id_required(self):
        """Test id is required"""
        with pytest.raises(ValidationError):
            IntentRead(
                name="Test",
                category_level_1_id=1,
                created_at="2024-01-01T00:00:00"
            )
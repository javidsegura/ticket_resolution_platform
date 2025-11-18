"""Tests for User schema validation"""
import pytest
from pydantic import ValidationError
from ai_ticket_platform.schemas.endpoints.user import UserCreate, UserUpdate, UserRead


class TestUserCreate:
    """Test UserCreate validation"""

    def test_valid_creation(self):
        """Test valid user creation"""
        user = UserCreate(
            name="John Doe",
            email="john@example.com",
            role="support",
            slack_user_id="U12345ABC"
        )
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.role == "support"
        assert user.slack_user_id == "U12345ABC"
        assert user.area is None

    def test_name_validation(self):
        """Test name length constraints"""
        with pytest.raises(ValidationError):
            UserCreate(name="", email="j@e.com", role="support", slack_user_id="U123")
        with pytest.raises(ValidationError):
            UserCreate(name="x" * 256, email="j@e.com", role="support", slack_user_id="U123")

    def test_email_validation(self):
        """Test email format and length"""
        with pytest.raises(ValidationError):
            UserCreate(name="John", email="invalid", role="support", slack_user_id="U123")
        with pytest.raises(ValidationError):
            UserCreate(name="John", email="x" * 250 + "@e.com", role="support", slack_user_id="U123")

    def test_role_validation(self):
        """Test role length constraints"""
        with pytest.raises(ValidationError):
            UserCreate(name="John", email="j@e.com", role="", slack_user_id="U123")
        with pytest.raises(ValidationError):
            UserCreate(name="John", email="j@e.com", role="x" * 101, slack_user_id="U123")

    def test_slack_user_id_required(self):
        """Test slack_user_id is required"""
        with pytest.raises(ValidationError):
            UserCreate(name="John", email="j@e.com", role="support")
        with pytest.raises(ValidationError):
            UserCreate(name="John", email="j@e.com", role="support", slack_user_id="")

    def test_area_validation(self):
        """Test area length constraints"""
        with pytest.raises(ValidationError):
            UserCreate(
                name="John", 
                email="j@e.com", 
                role="support", 
                slack_user_id="U123",
                area=""
            )
        with pytest.raises(ValidationError):
            UserCreate(
                name="John",
                email="j@e.com",
                role="support",
                slack_user_id="U123",
                area="x" * 256
            )

    def test_full_user_creation(self):
        """Test user creation with all fields"""
        user = UserCreate(
            name="Jane Doe",
            email="jane@example.com",
            role="admin",
            area="Billing",
            slack_user_id="U98765XYZ"
        )
        assert user.name == "Jane Doe"
        assert user.role == "admin"
        assert user.area == "Billing"
        assert user.slack_user_id == "U98765XYZ"


class TestUserUpdate:
    """Test UserUpdate validation"""

    def test_all_optional(self):
        """Test all fields are optional"""
        user = UserUpdate()
        assert user.name is None
        assert user.email is None
        assert user.role is None
        assert user.area is None
        assert user.slack_user_id is None

    def test_partial_updates(self):
        """Test partial field updates"""
        user = UserUpdate(name="Updated Name")
        assert user.name == "Updated Name"

        user = UserUpdate(role="product")
        assert user.role == "product"

        user = UserUpdate(area="API")
        assert user.area == "API"

    def test_field_validation(self):
        """Test validation on provided fields"""
        with pytest.raises(ValidationError):
            UserUpdate(email="invalid")
        with pytest.raises(ValidationError):
            UserUpdate(name="")
        with pytest.raises(ValidationError):
            UserUpdate(role="")
        with pytest.raises(ValidationError):
            UserUpdate(area="")


class TestUserRead:
    """Test UserRead validation"""

    def test_read_structure(self):
        """Test UserRead contains all fields"""
        user = UserRead(
            id=1,
            name="John Doe",
            email="john@example.com",
            role="support",
            slack_user_id="U12345ABC",
            created_at="2024-01-01T00:00:00"
        )
        assert user.id == 1
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.role == "support"
        assert user.slack_user_id == "U12345ABC"

    def test_id_required(self):
        """Test id is required"""
        with pytest.raises(ValidationError):
            UserRead(
                name="John",
                email="j@e.com",
                role="support",
                slack_user_id="U123",
                created_at="2024-01-01T00:00:00"
            )

    def test_created_at_required(self):
        """Test created_at is required"""
        with pytest.raises(ValidationError):
            UserRead(
                id=1,
                name="John",
                email="j@e.com",
                role="support",
                slack_user_id="U123"
            )

    def test_optional_fields(self):
        """Test optional fields in UserRead"""
        user = UserRead(
            id=1,
            name="John",
            email="j@e.com",
            role="support",
            slack_user_id="U123",
            created_at="2024-01-01T00:00:00",
            area="Billing",
            updated_at="2024-01-02T00:00:00"
        )
        assert user.area == "Billing"
        assert user.updated_at is not None
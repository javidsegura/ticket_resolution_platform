"""Tests for User schema validation"""
import pytest
from pydantic import ValidationError
from ai_ticket_platform.schemas.endpoints.user import UserCreate, UserUpdate, UserRead


class TestUserCreate:
    """Test UserCreate validation"""

    def test_valid_creation(self):
        """Test valid user creation"""
        user = UserCreate(
            user_id="user123",
            displayable_name="John Doe",
            email="john@example.com",
            country="US"
        )
        assert user.user_id == "user123"
        assert user.email == "john@example.com"

    def test_user_id_validation(self):
        """Test user_id length constraints"""
        with pytest.raises(ValidationError):
            UserCreate(
                user_id="", displayable_name="J", email="j@e.com", country="US"
            )
        with pytest.raises(ValidationError):
            UserCreate(
                user_id="x" * 300, displayable_name="J", email="j@e.com", country="US"
            )

    def test_displayable_name_validation(self):
        """Test displayable_name length constraints"""
        with pytest.raises(ValidationError):
            UserCreate(
                user_id="u1", displayable_name="", email="j@e.com", country="US"
            )
        with pytest.raises(ValidationError):
            UserCreate(
                user_id="u1", displayable_name="x" * 101, email="j@e.com", country="US"
            )

    def test_email_validation(self):
        """Test email format and length"""
        with pytest.raises(ValidationError):
            UserCreate(
                user_id="u1", displayable_name="John", email="invalid", country="US"
            )


class TestUserUpdate:
    """Test UserUpdate validation"""

    def test_all_optional(self):
        """Test all fields are optional"""
        user = UserUpdate()
        assert user.displayable_name is None
        assert user.email is None
        assert user.country is None

    def test_partial_updates(self):
        """Test partial field updates"""
        user = UserUpdate(displayable_name="Jane")
        assert user.displayable_name == "Jane"

    def test_field_validation(self):
        """Test validation on provided fields"""
        with pytest.raises(ValidationError):
            UserUpdate(email="invalid")
        with pytest.raises(ValidationError):
            UserUpdate(country="USA")


class TestUserRead:
    """Test UserRead validation"""

    def test_read_structure(self):
        """Test UserRead contains all fields"""
        user = UserRead(
            user_id="u1",
            displayable_name="John",
            email="j@e.com",
            profile_pic_object_name="p.jpg",
            country="US"
        )
        assert user.user_id == "u1"
        assert user.email == "j@e.com"

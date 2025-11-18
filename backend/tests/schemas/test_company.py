"""Tests for Company profile schema validation"""
import pytest
from pydantic import ValidationError
from ai_ticket_platform.schemas.endpoints.company import (
    CompanyProfileCreate,
    CompanyProfileUpdate,
    CompanyProfileRead
)


class TestCompanyProfileCreate:
    """Test CompanyProfileCreate validation"""

    def test_valid_creation(self):
        """Test valid company profile creation"""
        company = CompanyProfileCreate(
            name="Acme Corp",
            domain="acme.com",
            industry="Technology",
            support_email="support@acme.com"
        )
        assert company.name == "Acme Corp"
        assert company.domain == "acme.com"

    def test_name_validation(self):
        """Test name length constraints"""
        with pytest.raises(ValidationError):
            CompanyProfileCreate(name="", domain="test.com")
        with pytest.raises(ValidationError):
            CompanyProfileCreate(name="x" * 256, domain="test.com")

    def test_domain_validation(self):
        """Test domain format validation"""
        with pytest.raises(ValidationError):
            CompanyProfileCreate(name="Test", domain="invalid..com")
        with pytest.raises(ValidationError):
            CompanyProfileCreate(name="Test", domain="-example.com")

        # Valid domains
        company = CompanyProfileCreate(name="Test", domain="example.com")
        assert company.domain == "example.com"

        company = CompanyProfileCreate(name="Test", domain="SUB.EXAMPLE.COM")
        assert company.domain == "sub.example.com"  # Lowercased

    def test_domain_optional(self):
        """Test domain is optional"""
        company = CompanyProfileCreate(name="Test")
        assert company.domain is None

    def test_industry_validation(self):
        """Test industry length constraints"""
        with pytest.raises(ValidationError):
            CompanyProfileCreate(name="Test", industry="")
        with pytest.raises(ValidationError):
            CompanyProfileCreate(name="Test", industry="x" * 101)

    def test_support_email_validation(self):
        """Test support_email format"""
        with pytest.raises(ValidationError):
            CompanyProfileCreate(name="Test", support_email="invalid")

        company = CompanyProfileCreate(
            name="Test",
            support_email="support@example.com"
        )
        assert "support@example.com" in company.support_email


class TestCompanyProfileUpdate:
    """Test CompanyProfileUpdate validation"""

    def test_all_optional(self):
        """Test all fields are optional"""
        company = CompanyProfileUpdate()
        assert company.name is None
        assert company.domain is None

    def test_field_updates(self):
        """Test partial field updates"""
        company = CompanyProfileUpdate(name="Updated")
        assert company.name == "Updated"

        company = CompanyProfileUpdate(domain="NEW.COM")
        assert company.domain == "new.com"

    def test_validation(self):
        """Test validation on updates"""
        with pytest.raises(ValidationError):
            CompanyProfileUpdate(name="")
        with pytest.raises(ValidationError):
            CompanyProfileUpdate(domain="invalid..com")


class TestCompanyProfileRead:
    """Test CompanyProfileRead validation"""

    def test_read_structure(self):
        """Test CompanyProfileRead structure"""
        company = CompanyProfileRead(
            id=1,
            name="Test Corp",
            domain="test.com",
            industry="Tech",
            support_email="support@test.com",
            created_at="2024-01-01T00:00:00"
        )
        assert company.id == 1
        assert company.name == "Test Corp"

    def test_id_required(self):
        """Test id is required"""
        with pytest.raises(ValidationError):
            CompanyProfileRead(
                name="Test",
                domain="test.com",
                created_at="2024-01-01T00:00:00"
            )
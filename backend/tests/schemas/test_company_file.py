"""Tests for CompanyFile schema validation"""
import pytest
from pydantic import ValidationError
from ai_ticket_platform.schemas.endpoints.company_file import (
    CompanyFileCreate,
    CompanyFileRead
)


class TestCompanyFileCreate:
    """Test CompanyFileCreate validation"""

    def test_valid_creation(self):
        """Test valid company file creation"""
        file = CompanyFileCreate(
            original_filename="document.pdf",
            area="Contracts"
        )
        assert file.original_filename == "document.pdf"
        assert file.area == "Contracts"

    def test_filename_validation(self):
        """Test original_filename security"""
        with pytest.raises(ValidationError):
            CompanyFileCreate(original_filename="", area="Test")
        with pytest.raises(ValidationError):
            CompanyFileCreate(original_filename="x" * 256, area="Test")

        # Path traversal rejection
        with pytest.raises(ValidationError):
            CompanyFileCreate(original_filename="../../etc/passwd", area="Test")
        with pytest.raises(ValidationError):
            CompanyFileCreate(original_filename="folder/document.pdf", area="Test")
        with pytest.raises(ValidationError):
            CompanyFileCreate(original_filename="folder\\document.pdf", area="Test")

    def test_filename_with_extension(self):
        """Test filename with extensions"""
        file = CompanyFileCreate(
            original_filename="report.pdf",
            area="Reports"
        )
        assert "report.pdf" in file.original_filename

    def test_area_optional(self):
        """Test area is optional"""
        file = CompanyFileCreate(original_filename="test.pdf")
        assert file.area is None

    def test_area_validation(self):
        """Test area length constraints"""
        with pytest.raises(ValidationError):
            CompanyFileCreate(original_filename="test.pdf", area="x" * 256)

        file = CompanyFileCreate(
            original_filename="test.pdf",
            area="x" * 255
        )
        assert len(file.area) == 255


class TestCompanyFileRead:
    """Test CompanyFileRead validation"""

    def test_valid_read(self):
        """Test valid company file read"""
        file = CompanyFileRead(
            id=1,
            original_filename="document.pdf",
            blob_path="azure://container/document_12345.pdf",
            area="Contracts",
            created_at="2024-01-01T00:00:00"
        )
        assert file.id == 1
        assert file.blob_path == "azure://container/document_12345.pdf"

    def test_blob_path_validation(self):
        """Test blob_path constraints"""
        with pytest.raises(ValidationError):
            CompanyFileRead(
                id=1,
                original_filename="test.pdf",
                blob_path="",
                created_at="2024-01-01T00:00:00"
            )
        with pytest.raises(ValidationError):
            CompanyFileRead(
                id=1,
                original_filename="test.pdf",
                blob_path="x" * 1001,
                created_at="2024-01-01T00:00:00"
            )

    def test_read_required_fields(self):
        """Test required fields in Read"""
        with pytest.raises(ValidationError):
            CompanyFileRead(
                id=1,
                original_filename="test.pdf",
                created_at="2024-01-01T00:00:00"
            )

        with pytest.raises(ValidationError):
            CompanyFileRead(
                id=1,
                blob_path="azure://path",
                created_at="2024-01-01T00:00:00"
            )

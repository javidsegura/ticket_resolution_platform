"""Unit tests for company file schema validation."""

import pytest
from pydantic import ValidationError


class TestCompanyFileFilenameValidator:
	"""Test CompanyFile filename validation."""

	def test_valid_filename(self):
		"""Test that valid filename is accepted."""
		from ai_ticket_platform.schemas.endpoints.company_file import CompanyFileBase

		file_obj = CompanyFileBase(original_filename="document.pdf")

		assert file_obj.original_filename == "document.pdf"

	def test_filename_with_path_traversal_rejected(self):
		"""Test that filename with .. is rejected."""
		from ai_ticket_platform.schemas.endpoints.company_file import CompanyFileBase

		with pytest.raises(ValidationError) as exc_info:
			CompanyFileBase(original_filename="../etc/passwd")

		errors = exc_info.value.errors()
		assert any("Filename contains invalid characters" in str(error) for error in errors)

	def test_filename_with_forward_slash_rejected(self):
		"""Test that filename with forward slash is rejected."""
		from ai_ticket_platform.schemas.endpoints.company_file import CompanyFileBase

		with pytest.raises(ValidationError) as exc_info:
			CompanyFileBase(original_filename="folder/document.pdf")

		errors = exc_info.value.errors()
		assert any("Filename contains invalid characters" in str(error) for error in errors)

	def test_filename_with_backslash_rejected(self):
		"""Test that filename with backslash is rejected."""
		from ai_ticket_platform.schemas.endpoints.company_file import CompanyFileBase

		with pytest.raises(ValidationError) as exc_info:
			CompanyFileBase(original_filename="folder\\document.pdf")

		errors = exc_info.value.errors()
		assert any("Filename contains invalid characters" in str(error) for error in errors)

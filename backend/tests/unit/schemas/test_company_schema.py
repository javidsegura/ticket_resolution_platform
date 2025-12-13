"""Unit tests for company schema validation."""

import pytest
from pydantic import ValidationError


class TestCompanyProfileDomainValidator:
	"""Test CompanyProfile domain validation."""

	def test_valid_domain(self):
		"""Test that valid domain is accepted."""
		from ai_ticket_platform.schemas.endpoints.company import CompanyProfileBase

		profile = CompanyProfileBase(name="Test Company", domain="example.com")

		assert profile.name == "Test Company"
		assert profile.domain == "example.com"

	def test_valid_subdomain(self):
		"""Test that valid subdomain is accepted."""
		from ai_ticket_platform.schemas.endpoints.company import CompanyProfileBase

		profile = CompanyProfileBase(name="Test Company", domain="app.example.com")

		assert profile.domain == "app.example.com"

	def test_domain_converted_to_lowercase(self):
		"""Test that domain is converted to lowercase."""
		from ai_ticket_platform.schemas.endpoints.company import CompanyProfileBase

		profile = CompanyProfileBase(name="Test Company", domain="Example.COM")

		assert profile.domain == "example.com"

	def test_domain_stripped_of_whitespace(self):
		"""Test that domain whitespace is stripped."""
		from ai_ticket_platform.schemas.endpoints.company import CompanyProfileBase

		profile = CompanyProfileBase(name="Test Company", domain="  example.com  ")

		assert profile.domain == "example.com"

	def test_invalid_domain_format(self):
		"""Test that invalid domain format raises ValidationError."""
		from ai_ticket_platform.schemas.endpoints.company import CompanyProfileBase

		with pytest.raises(ValidationError) as exc_info:
			CompanyProfileBase(name="Test Company", domain="invalid domain!")

		errors = exc_info.value.errors()
		assert any("Invalid domain format" in str(error) for error in errors)

	def test_domain_with_invalid_characters(self):
		"""Test that domain with invalid characters raises ValidationError."""
		from ai_ticket_platform.schemas.endpoints.company import CompanyProfileBase

		with pytest.raises(ValidationError) as exc_info:
			CompanyProfileBase(name="Test Company", domain="exa_mple.com")

		errors = exc_info.value.errors()
		assert any("Invalid domain format" in str(error) for error in errors)

	def test_none_domain_is_valid(self):
		"""Test that None domain is valid."""
		from ai_ticket_platform.schemas.endpoints.company import CompanyProfileBase

		profile = CompanyProfileBase(name="Test Company", domain=None)

		assert profile.domain is None

	def test_company_profile_update_domain_validation(self):
		"""Test that CompanyProfileUpdate also validates domain."""
		from ai_ticket_platform.schemas.endpoints.company import CompanyProfileUpdate

		with pytest.raises(ValidationError) as exc_info:
			CompanyProfileUpdate(domain="invalid domain!")

		errors = exc_info.value.errors()
		assert any("Invalid domain format" in str(error) for error in errors)

"""Unit tests for base settings validation."""

import pytest
from ai_ticket_platform.core.settings.environment.base import BaseSettings


class MockSettings(BaseSettings):
	"""Mock settings class for testing."""

	def __init__(self, missing_var=False):
		self.TEST_VAR_1 = "value1" if not missing_var else None
		self.TEST_VAR_2 = "value2"

	def extract_all_variables(self):
		"""Mock implementation."""
		pass

	@property
	def required_vars(self):
		"""Mock required vars."""
		return ["TEST_VAR_1", "TEST_VAR_2"]


class TestBaseSettings:
	"""Test BaseSettings validation."""

	def test_validate_required_vars_all_present(self):
		"""Test that validation passes when all required vars are present."""
		settings = MockSettings(missing_var=False)
		
		# Should not raise exception
		settings.validate_required_vars()

	def test_validate_required_vars_missing_var(self):
		"""Test that validation raises ValueError when required var is missing."""
		settings = MockSettings(missing_var=True)
		
		with pytest.raises(ValueError) as exc_info:
			settings.validate_required_vars()
		
		assert "Missing required environment variables" in str(exc_info.value)
		assert "TEST_VAR_1" in str(exc_info.value)

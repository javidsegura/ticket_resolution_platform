"""Unit tests for app_settings module."""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestSettings:
	"""Test Settings class initialization."""

	def test_settings_valid_environment(self):
		"""Test Settings initialization with valid environment."""
		with patch.dict(os.environ, {"ENVIRONMENT": "test"}, clear=False):
			from ai_ticket_platform.core.settings.app_settings import Settings

			settings = Settings()

			assert settings.ENVIRONMENT == "test"

	def test_settings_invalid_environment(self):
		"""Test Settings raises error for invalid environment."""
		with patch.dict(os.environ, {"ENVIRONMENT": "invalid"}, clear=False):
			from ai_ticket_platform.core.settings.app_settings import Settings

			with pytest.raises(ValueError, match="not an accepted environment"):
				Settings()

	def test_settings_staging_environment(self):
		"""Test Settings with staging environment."""
		with patch.dict(os.environ, {"ENVIRONMENT": "staging"}, clear=False):
			from ai_ticket_platform.core.settings.app_settings import Settings

			settings = Settings()

			assert settings.ENVIRONMENT == "staging"

	def test_settings_production_environment(self):
		"""Test Settings with production environment."""
		with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
			from ai_ticket_platform.core.settings.app_settings import Settings

			settings = Settings()

			assert settings.ENVIRONMENT == "production"


class TestSettingsExtraction:
	"""Test Settings get_settings method."""

	def test_get_settings_dev_environment(self):
		"""Test get_settings returns DevSettings for dev environment."""
		with patch.dict(os.environ, {"ENVIRONMENT": "dev"}, clear=False):
			from ai_ticket_platform.core.settings.app_settings import Settings

			settings = Settings()

			# _get_resolve_per_environment should return DevSettings for dev
			resolver = settings._get_resolve_per_environment()

			from ai_ticket_platform.core.settings.environment.dev import DevSettings

			assert isinstance(resolver, DevSettings)

	def test_get_settings_test_environment(self):
		"""Test get_settings returns DevSettings for test environment."""
		with patch.dict(os.environ, {"ENVIRONMENT": "test"}, clear=False):
			from ai_ticket_platform.core.settings.app_settings import Settings

			settings = Settings()
			resolver = settings._get_resolve_per_environment()

			from ai_ticket_platform.core.settings.environment.dev import DevSettings

			assert isinstance(resolver, DevSettings)

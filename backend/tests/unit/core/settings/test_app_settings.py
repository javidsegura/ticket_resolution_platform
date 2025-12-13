"""Unit tests for app settings initialization."""

import pytest
from unittest.mock import patch, MagicMock
import os


class TestSettings:
	"""Test Settings class initialization."""

	def test_settings_init_missing_environment(self):
		"""Test that missing ENVIRONMENT variable raises ValueError."""
		from ai_ticket_platform.core.settings.app_settings import Settings

		with patch.dict(os.environ, {}, clear=True):
			with pytest.raises(AttributeError):
				# When ENVIRONMENT is missing, os.getenv returns None
				# Calling .lower() on None raises AttributeError
				Settings()

	def test_settings_init_invalid_environment(self):
		"""Test that invalid ENVIRONMENT value raises ValueError."""
		from ai_ticket_platform.core.settings.app_settings import Settings

		with patch.dict(os.environ, {"ENVIRONMENT": "invalid_env"}):
			with pytest.raises(ValueError) as exc_info:
				Settings()

			assert "not an accepted environment" in str(exc_info.value)

	def test_settings_init_valid_test_environment(self):
		"""Test successful initialization with test environment."""
		from ai_ticket_platform.core.settings.app_settings import Settings

		with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
			settings = Settings()

			assert settings.ENVIRONMENT == "test"

	def test_settings_init_valid_dev_environment(self):
		"""Test successful initialization with dev environment."""
		from ai_ticket_platform.core.settings.app_settings import Settings

		with patch.dict(os.environ, {"ENVIRONMENT": "dev"}):
			settings = Settings()

			assert settings.ENVIRONMENT == "dev"

	def test_settings_init_valid_staging_environment(self):
		"""Test successful initialization with staging environment."""
		from ai_ticket_platform.core.settings.app_settings import Settings

		with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
			settings = Settings()

			assert settings.ENVIRONMENT == "staging"

	def test_settings_init_valid_production_environment(self):
		"""Test successful initialization with production environment."""
		from ai_ticket_platform.core.settings.app_settings import Settings

		with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
			settings = Settings()

			assert settings.ENVIRONMENT == "production"

	def test_get_resolve_per_environment_dev(self):
		"""Test _get_resolve_per_environment returns DevSettings for dev."""
		from ai_ticket_platform.core.settings.app_settings import Settings
		from ai_ticket_platform.core.settings.environment import DevSettings

		with patch.dict(os.environ, {"ENVIRONMENT": "dev"}):
			settings = Settings()
			resolver = settings._get_resolve_per_environment()

			assert isinstance(resolver, DevSettings)

	def test_get_resolve_per_environment_test(self):
		"""Test _get_resolve_per_environment returns DevSettings for test."""
		from ai_ticket_platform.core.settings.app_settings import Settings
		from ai_ticket_platform.core.settings.environment import DevSettings

		with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
			settings = Settings()
			resolver = settings._get_resolve_per_environment()

			assert isinstance(resolver, DevSettings)

	def test_get_resolve_per_environment_staging(self):
		"""Test _get_resolve_per_environment returns DeploymentSettings for staging."""
		from ai_ticket_platform.core.settings.app_settings import Settings
		from ai_ticket_platform.core.settings.environment import DeploymentSettings

		with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
			settings = Settings()
			resolver = settings._get_resolve_per_environment()

			assert isinstance(resolver, DeploymentSettings)

	def test_get_resolve_per_environment_production(self):
		"""Test _get_resolve_per_environment returns DeploymentSettings for production."""
		from ai_ticket_platform.core.settings.app_settings import Settings
		from ai_ticket_platform.core.settings.environment import DeploymentSettings

		with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
			settings = Settings()
			resolver = settings._get_resolve_per_environment()

			assert isinstance(resolver, DeploymentSettings)


class TestInitializeSettings:
	"""Test initialize_settings function."""

	def test_initialize_settings_first_call(self):
		"""Test first call to initialize_settings creates settings."""
		mock_resolver = MagicMock()
		mock_resolver.MYSQL_HOST = "localhost"

		with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
			with patch("ai_ticket_platform.core.settings.app_settings.app_settings", None):
				with patch("ai_ticket_platform.core.settings.app_settings.Settings") as mock_settings_class:
					mock_settings_instance = MagicMock()
					mock_settings_instance.get_settings.return_value = mock_resolver
					mock_settings_class.return_value = mock_settings_instance

					from ai_ticket_platform.core.settings.app_settings import initialize_settings
					result = initialize_settings()

					assert result == mock_resolver
					mock_settings_class.assert_called_once()

	def test_initialize_settings_already_initialized(self):
		"""Test that subsequent calls return cached settings."""
		mock_settings = MagicMock()

		with patch("ai_ticket_platform.core.settings.app_settings.app_settings", mock_settings):
			from ai_ticket_platform.core.settings.app_settings import initialize_settings
			result = initialize_settings()

			assert result == mock_settings

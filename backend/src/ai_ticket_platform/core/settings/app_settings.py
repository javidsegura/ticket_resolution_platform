import os
from pathlib import Path

import logging
from .environment import DevSettings, DeploymentSettings

logger = logging.getLogger(__name__)

POSSIBLE_ENVIRONMENTS = ["test", "dev", "staging", "production"]


class Settings:
	"""Application settings loaded from environment variables."""

	def __init__(self):
		self.ENVIRONMENT = os.getenv("ENVIRONMENT").lower()
		logger.debug(f"ENVIRONMENT IS: {self.ENVIRONMENT}")
		if not self.ENVIRONMENT:
			raise ValueError(
				"Environment is not provided. \
				Do export ENVIRONMENT=<value>"
			)
		if self.ENVIRONMENT not in POSSIBLE_ENVIRONMENTS:
			raise ValueError(
				f"{self.ENVIRONMENT} not an accepted environment. Accepted environment is: {POSSIBLE_ENVIRONMENTS}"
			)

	def get_settings(self):
		return self._extract_all_variables()

	def _get_resolve_per_environment(self):
		if self.ENVIRONMENT in ["test", "dev"]:
			return DevSettings()
		elif self.ENVIRONMENT in ["staging", "production"]:
			return DeploymentSettings()

	def _extract_all_variables(self):
		resolver = self._get_resolve_per_environment()

		resolver.extract_all_variables()
		resolver.validate_required_vars()
		return resolver


app_settings = None


def initialize_settings():
	global app_settings
	print(f"Intiliazing settings")
	if not app_settings:
		print(f"Instantiating settings for the first time")
		app_settings = Settings().get_settings()
	else:
		print("Settings already existed")
	print(f"APP SETTINGS: {dir(app_settings)}")  # Delete in prod
	print("=" * 30)
	return app_settings

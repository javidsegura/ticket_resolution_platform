import os

from .base import BaseSettings


class DeploymentSettings(BaseSettings):
	def __init__(self) -> None:
		super().__init__()

	@property
	def required_vars(self):
		base_vars = [
			"REDIS_URL",
			"MYSQL_USER",
			"MYSQL_PASSWORD",
			"MYSQL_HOST",
			"MYSQL_PORT",
			"MYSQL_DATABASE",
			"MYSQL_SYNC_DRIVER",
			"MYSQL_ASYNC_DRIVER",
			"CLOUD_PROVIDER",
			"GEMINI_API_KEY"
		]

		# Dynamically add cloud-specific required vars
		cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower()
		if cloud_provider == "aws":
			base_vars.extend(["S3_MAIN_BUCKET_NAME", "AWS_MAIN_REGION"])
		elif cloud_provider == "azure":
			base_vars.extend(
				[
					"AZURE_STORAGE_CONTAINER_NAME",
					"AZURE_STORAGE_ACCOUNT_NAME",
					"AZURE_STORAGE_ACCOUNT_KEY",
					"AZURE_KEY_VAULT_NAME",
				]
			)

		return base_vars

	def extract_all_variables(self):
		self.CLOUD_PROVIDER = os.getenv("CLOUD_PROVIDER", "aws").lower().strip()

		self._extract_storage_variables()
		self._extract_app_logic_variables()
		self._extract_database_variables()
		self._extract_llm_variables()

	def _extract_llm_variables(self):
		self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
		self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
		self.CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
		self.CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")
		self.CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "company-docs")

	def _extract_secret_manger_databaseb_credentials(self):
		from ai_ticket_platform.services.infra.secrets import get_secrets_service

		secret_key = os.getenv("SECRETS_MANAGER_DB_CREDENTIALS_KEY")
		if not secret_key:
			raise ValueError(
				"Database credentials secret key is needed! Set SECRETS_MANAGER_DB_CREDENTIALS_KEY"
			)

		secrets_service = get_secrets_service(cloud_provider=self.CLOUD_PROVIDER)
		if self.CLOUD_PROVIDER == "azure":
			self.AZURE_KEY_VAULT_NAME = os.getenv("AZURE_KEY_VAULT_NAME")
		db_credentials = secrets_service.fetch_secret(secret_key=secret_key)
		self.MYSQL_USER = db_credentials["username"]
		self.MYSQL_PASSWORD = db_credentials["password"]

	def _extract_database_variables(self):
		self.REDIS_URL = os.getenv("REDIS_URL")
		self.MYSQL_PORT = os.getenv("MYSQL_PORT")
		self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
		self.MYSQL_SYNC_DRIVER = os.getenv("MYSQL_SYNC_DRIVER")
		self.MYSQL_ASYNC_DRIVER = os.getenv("MYSQL_ASYNC_DRIVER")
		if self.CLOUD_PROVIDER == "aws":
			self.MYSQL_HOST = os.getenv("RDS_MYSQL_HOST")
		elif self.CLOUD_PROVIDER == "azure":
			self.MYSQL_HOST = os.getenv("MYSQL_HOST")
		self._extract_secret_manger_databaseb_credentials()

	def _extract_storage_variables(self):
		self.CLOUD_PROVIDER = os.getenv("CLOUD_PROVIDER", "aws").lower()

		if self.CLOUD_PROVIDER == "aws":
			self.S3_MAIN_BUCKET_NAME = os.getenv("S3_MAIN_BUCKET_NAME")
			self.AWS_MAIN_REGION = os.getenv("AWS_MAIN_REGION")
		elif self.CLOUD_PROVIDER == "azure":
			self.AZURE_STORAGE_CONTAINER_NAME = os.getenv(
				"AZURE_STORAGE_CONTAINER_NAME"
			)
			self.AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
			self.AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
		else:
			raise ValueError(
				f"Unsupported CLOUD_PROVIDER: {self.CLOUD_PROVIDER}. Use 'aws' or 'azure'"
			)

from .base import BaseSettings
import os

"""
MISSING STUFF:
D) Create user manually, then test
E) Create confetst dependency (create an user and get its token)


"""

from dotenv import load_dotenv


class DevSettings(BaseSettings):
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
			"CHROMA_HOST",
			"CHROMA_PORT",
			"GEMINI_API_KEY",
			# "OPENAI_API_KEY",  # Required for LLM clustering
			# "USING_FIREBASE_EMULATOR", "FB_AUTH_EMULATOR_HOST", "FB_PROJECT_ID"
		]

		# Cloud-specific vars
		cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower()
		if cloud_provider == "aws":
			base_vars.extend(["S3_MAIN_BUCKET_NAME", "AWS_MAIN_REGION"])
		elif cloud_provider == "azure":
			base_vars.extend(
				[
					"AZURE_STORAGE_CONTAINER_NAME",
					"AZURE_STORAGE_ACCOUNT_NAME",
					"AZURE_STORAGE_ACCOUNT_KEY",
				]
			)

		return base_vars

	def extract_all_variables(self):
		# Define multi-cloud strategy
		self.CLOUD_PROVIDER = os.getenv("CLOUD_PROVIDER", "aws").lower()

		# Extract different categories of variables
		self._extract_database_variables()
		self._extract_storage_variables()
		self._extract_app_logic_variables()
		self._extract_slack_variables()
		self._extract_llm_variables()
		self._extract_chroma_variables()

	def _extract_database_variables(self):
		self.REDIS_URL = os.getenv("REDIS_URL")
		self.REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
		self.MYSQL_USER = os.getenv("MYSQL_USER")
		self.MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
		self.MYSQL_ASYNC_DRIVER = os.getenv("MYSQL_ASYNC_DRIVER")
		self.MYSQL_PORT = os.getenv("MYSQL_PORT")
		self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
		self.MYSQL_SYNC_DRIVER = os.getenv("MYSQL_SYNC_DRIVER")
		self.MYSQL_HOST = os.getenv("MYSQL_HOST")

	def _extract_storage_variables(self):
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

	def _extract_slack_variables(self):
		self.SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
		self.SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
	
	def _extract_app_logic_variables(self):
		self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

	def _extract_llm_variables(self):
		self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
		self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
		self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

	def _extract_chroma_variables(self):
		self.CHROMA_HOST = os.getenv("CHROMA_HOST")
		self.CHROMA_PORT = os.getenv("CHROMA_PORT")
		self.CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME")

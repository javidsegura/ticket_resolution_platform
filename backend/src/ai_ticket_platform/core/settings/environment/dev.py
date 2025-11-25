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
                  "REDIS_URL", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_HOST",
                  "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_SYNC_DRIVER", 
                  "MYSQL_ASYNC_DRIVER", 

                  "CLOUD_PROVIDER",

                  
                  "OPENAI_API_KEY",  # Required for LLM clustering
                  #"USING_FIREBASE_EMULATOR", "FB_AUTH_EMULATOR_HOST", "FB_PROJECT_ID"
            ]
            
            # Cloud-specific vars 
            cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower()
            if cloud_provider == "aws":
                  base_vars.extend(["S3_MAIN_BUCKET_NAME", "AWS_MAIN_REGION"])
            elif cloud_provider == "azure":
                  base_vars.extend([
                        "AZURE_STORAGE_CONTAINER_NAME",
                        "AZURE_STORAGE_ACCOUNT_NAME", 
                        "AZURE_STORAGE_ACCOUNT_KEY"
                  ])
            
            return base_vars

      def extract_all_variables(self):
            """
            Populate the DevSettings instance by running each environment-variable extractor.
            
            Calls the internal extraction helpers to read and assign configuration from environment variables: database, storage, application logic, Slack, and LLM settings (the Firebase extractor is present but commented out).
            """
            self._extract_database_variables()
            self._extract_storage_variables()
            self._extract_app_logic_variables()
            self._extract_slack_variables()
            self._extract_llm_variables()
            #self._extract_firebase_variables()
      def _extract_database_variables(self):
            """
            Populate instance attributes for database and Redis configuration from environment variables.
            
            Sets the following attributes from their corresponding environment variables:
            - REDIS_URL: Redis connection URL.
            - REDIS_MAX_CONNECTIONS: Maximum Redis connections (defaults to 10 if unset).
            - MYSQL_USER: MySQL username.
            - MYSQL_PASSWORD: MySQL password.
            - MYSQL_ASYNC_DRIVER: MySQL async driver identifier.
            - MYSQL_PORT: MySQL port.
            - MYSQL_DATABASE: MySQL database name.
            - MYSQL_SYNC_DRIVER: MySQL sync driver identifier.
            - MYSQL_HOST: MySQL host.
            """
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
            """
            Populate storage-related settings from environment variables based on the selected cloud provider.
            
            Reads CLOUD_PROVIDER (default "aws") and sets corresponding attributes:
            - For "aws": sets `S3_MAIN_BUCKET_NAME` and `AWS_MAIN_REGION`.
            - For "azure": sets `AZURE_STORAGE_CONTAINER_NAME`, `AZURE_STORAGE_ACCOUNT_NAME`, and `AZURE_STORAGE_ACCOUNT_KEY`.
            
            Raises:
                ValueError: If CLOUD_PROVIDER is not "aws" or "azure".
            """
            self.CLOUD_PROVIDER = os.getenv("CLOUD_PROVIDER", "aws").lower()
            
            if self.CLOUD_PROVIDER == "aws":
                  self.S3_MAIN_BUCKET_NAME = os.getenv("S3_MAIN_BUCKET_NAME")
                  self.AWS_MAIN_REGION = os.getenv("AWS_MAIN_REGION")
            elif self.CLOUD_PROVIDER == "azure":
                  self.AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
                  self.AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
                  self.AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
            else:
                  raise ValueError(f"Unsupported CLOUD_PROVIDER: {self.CLOUD_PROVIDER}. Use 'aws' or 'azure'")

      def _extract_slack_variables(self):
            """
            Populate the instance with Slack configuration values from environment variables.
            
            Sets the instance attributes:
            - `SLACK_BOT_TOKEN`: value of the `SLACK_BOT_TOKEN` environment variable or `None` if unset.
            - `SLACK_CHANNEL_ID`: value of the `SLACK_CHANNEL_ID` environment variable or `None` if unset.
            """
            self.SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
            self.SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

      def _extract_llm_variables(self):
            """
            Populate LLM-related settings from environment variables.
            
            Sets self.OPENAI_API_KEY from OPENAI_API_KEY (or None if unset) and sets self.OPENAI_MODEL from OPENAI_MODEL with a default of "gpt-4o".
            """
            self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
      # def _extract_firebase_variables(self):
      #       self.USING_FIREBASE_EMULATOR = os.getenv("USING_FIREBASE_EMULATOR")
      #       self.FB_AUTH_EMULATOR_HOST= os.getenv("FB_AUTH_EMULATOR_HOST")
      #       self.FB_PROJECT_ID = os.getenv("FB_PROJECT_ID")
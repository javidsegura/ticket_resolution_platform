from .base import BaseSettings
import os


class DeploymentSettings(BaseSettings):
      def __init__(self) -> None:
            super().__init__()

      @property
      def required_vars(self):
            base_vars = [
                  "REDIS_URL", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_HOST",
                  "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_SYNC_DRIVER", 
                  "MYSQL_ASYNC_DRIVER", 
                  "CLOUD_PROVIDER"
            ]
            
            # Dynamically add cloud-specific required vars
            cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower()
            if cloud_provider == "aws":
                  base_vars.extend(["S3_MAIN_BUCKET_NAME", "AWS_MAIN_REGION",
                  "OPENAI_API_KEY", ])
            elif cloud_provider == "azure":
                  base_vars.extend([
                        "AZURE_STORAGE_CONTAINER_NAME",
                        "AZURE_STORAGE_ACCOUNT_NAME", 
                        "AZURE_STORAGE_ACCOUNT_KEY"
                  ])
            
            return base_vars

      def extract_all_variables(self):
            self._extract_database_variables()
            self._extract_storage_variables()
            self._extract_app_logic_variables()
            self._extract_slack_variables()
            self._extract_llm_variables()
      def _extract_secret_manager_databaseb_credentials(self):
            from ai_ticket_platform.services.storage.secretsmanager import SecretsManager 
            secret_key = os.getenv("SECRETS_MANAGER_DB_CREDENTIALS_KEY")
            if not secret_key:
                  raise ValueError("RDS db credentials key is needed!")
            db_credentials = SecretsManager().fetch_secret(secret_key=secret_key)
            self.MYSQL_USER = db_credentials["username"]
            self.MYSQL_PASSWORD = db_credentials["password"]
      def _extract_database_variables(self):
            self.REDIS_URL = os.getenv("REDIS_URL")
            self.REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
            self.MYSQL_PORT = os.getenv("MYSQL_PORT")
            self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
            self.MYSQL_SYNC_DRIVER = os.getenv("MYSQL_SYNC_DRIVER")
            self.MYSQL_ASYNC_DRIVER = os.getenv("MYSQL_ASYNC_DRIVER")
            self.MYSQL_HOST = os.getenv("RDS_MYSQL_HOST")
            self._extract_secret_manger_databaseb_credentials()

      def _extract_storage_variables(self):
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
      def _extract_aws_variables(self):
            self.S3_MAIN_BUCKET_NAME = os.getenv("S3_MAIN_BUCKET_NAME")
            self.AWS_MAIN_REGION = os.getenv("AWS_MAIN_REGION")

      def _extract_slack_variables(self):
            self.SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
            self.SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

      def _extract_llm_variables(self):
            self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")




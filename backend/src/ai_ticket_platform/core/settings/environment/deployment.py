from .base import BaseSettings
import os


class DeploymentSettings(BaseSettings):
      def __init__(self) -> None:
            super().__init__()

      @property
      def required_vars(self):
            return [
                  "REDIS_URL", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_HOST",
                  "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_SYNC_DRIVER", 
                  "MYSQL_ASYNC_DRIVER", "S3_MAIN_BUCKET_NAME", "AWS_MAIN_REGION"
            ]

      def extract_all_variables(self):
            self._extract_database_variables()
            self._extract_aws_variables()
            self._extract_app_logic_variables()
      def _extract_secret_manger_databaseb_credentials(self):
            from ai_ticket_platform.services.infra.aws.secretsmanager import SecretsManager 
            secret_key = os.getenv("SECRETS_MANAGER_DB_CREDENTIALS_KEY")
            if not secret_key:
                  raise ValueError("RDS db credentials key is needed!")
            db_credentials = SecretsManager().fetch_secret(secret_key=secret_key)
            self.MYSQL_USER = db_credentials["username"]
            self.MYSQL_PASSWORD = db_credentials["password"]
      def _extract_database_variables(self):
            self.REDIS_URL = os.getenv("REDIS_URL")
            self.MYSQL_PORT = os.getenv("MYSQL_PORT")
            self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
            self.MYSQL_SYNC_DRIVER = os.getenv("MYSQL_SYNC_DRIVER")
            self.MYSQL_ASYNC_DRIVER = os.getenv("MYSQL_ASYNC_DRIVER")
            self.MYSQL_HOST = os.getenv("RDS_MYSQL_HOST")
            self._extract_secret_manger_databaseb_credentials()
      def _extract_aws_variables(self):
            self.S3_MAIN_BUCKET_NAME = os.getenv("S3_MAIN_BUCKET_NAME")
            self.AWS_MAIN_REGION = os.getenv("AWS_MAIN_REGION")

      




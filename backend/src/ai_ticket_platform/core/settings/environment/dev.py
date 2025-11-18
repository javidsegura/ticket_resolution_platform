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
            self._extract_database_variables()

            self._extract_storage_variables()

            self._extract_app_logic_variables()
            self._extract_slack_variables()
            #self._extract_firebase_variables()
      def _extract_database_variables(self):
            self.REDIS_URL = os.getenv("REDIS_URL")
            self.MYSQL_USER = os.getenv("MYSQL_USER")
            self.MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
            self.MYSQL_ASYNC_DRIVER = os.getenv("MYSQL_ASYNC_DRIVER")
            self.MYSQL_PORT = os.getenv("MYSQL_PORT")
            self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
            self.MYSQL_SYNC_DRIVER = os.getenv("MYSQL_SYNC_DRIVER")
            self.MYSQL_HOST = os.getenv("MYSQL_HOST")

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

      # def _extract_firebase_variables(self):
      #       self.USING_FIREBASE_EMULATOR = os.getenv("USING_FIREBASE_EMULATOR")
      #       self.FB_AUTH_EMULATOR_HOST= os.getenv("FB_AUTH_EMULATOR_HOST")
      #       self.FB_PROJECT_ID = os.getenv("FB_PROJECT_ID")
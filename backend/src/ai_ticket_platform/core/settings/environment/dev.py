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
            return [
                  "REDIS_URL", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_HOST",
                  "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_SYNC_DRIVER", 
                  "MYSQL_ASYNC_DRIVER", 
                  # AWS variables are optional - only required if using AWS services
                  # "S3_MAIN_BUCKET_NAME", "AWS_MAIN_REGION",
                  #"USING_FIREBASE_EMULATOR", "FB_AUTH_EMULATOR_HOST", "FB_PROJECT_ID"
            ]

      def extract_all_variables(self):
            self._extract_database_variables()
            # self._extract_aws_variables()  # Commented out - AWS variables are optional
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
      # def _extract_aws_variables(self):
      #       self.S3_MAIN_BUCKET_NAME = os.getenv("S3_MAIN_BUCKET_NAME")
      #       self.AWS_MAIN_REGION = os.getenv("AWS_MAIN_REGION")
      def _extract_slack_variables(self):
            self.SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
            self.SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
      # def _extract_firebase_variables(self):
      #       self.USING_FIREBASE_EMULATOR = os.getenv("USING_FIREBASE_EMULATOR")
      #       self.FB_AUTH_EMULATOR_HOST= os.getenv("FB_AUTH_EMULATOR_HOST")
      #       self.FB_PROJECT_ID = os.getenv("FB_PROJECT_ID")
      




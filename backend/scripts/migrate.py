#!/usr/bin/env python3

import subprocess
import sys
import logging
import pymysql
from ai_ticket_platform.core.settings import initialize_settings

logger = logging.getLogger(__name__)

class Migrator():
    def __init__(self) -> None:
        self.app_settings = initialize_settings()

    def start_migrations(self):
        self._create_database()
        self._run_migrations()
    def _create_database(self):
        """Create the database if it doesn't exist."""
        logger.info(f"Creating database '{self.app_settings.MYSQL_DATABASE}' if not exists...")

        try:
            logger.info("Connecting to MySQL with the following settings:")
            logger.info(f"  Host: {self.app_settings.MYSQL_HOST}")
            logger.info(f"  Port: {self.app_settings.MYSQL_PORT}")
            logger.info(f"  User: {self.app_settings.MYSQL_USER}")
            logger.debug(f"  Password: {self.app_settings.MYSQL_PASSWORD}")
            logger.info(f"  Database: {self.app_settings.MYSQL_DATABASE}")
            connection = pymysql.connect(
                host=self.app_settings.MYSQL_HOST,
                port=int(self.app_settings.MYSQL_PORT),
                user=self.app_settings.MYSQL_USER,
                password=self.app_settings.MYSQL_PASSWORD
            )

            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.app_settings.MYSQL_DATABASE}")
                logger.info(f"✅ Database ready")

            connection.commit()
            connection.close()

        except Exception as e:
            logger.error(f"❌ Error creating database: {e}", exc_info=True)
            sys.exit(1)

    def _run_migrations(self):
        """Run Alembic migrations."""
        logger.info("Running Alembic migrations...")
        try:
            result = subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True, text=True)
            logger.info("STDOUT:", result.stdout)
            logger.info("STDERR:", result.stderr)
            logger.info("✅ Migrations completed")

            result = subprocess.run(["alembic", "current"], check=True, capture_output=True, text=True)
            logger.info("Current migration:", result.stdout)
            logger.info("✅ Current migration status shown")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Migration failed: {e}", exc_info=True)
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            sys.exit(1)

if __name__ == "__main__":
    migrator = Migrator()
    migrator.start_migrations()
#!/usr/bin/env python3

import subprocess
import sys
import pymysql
from ai_ticket_platform.core.settings import initialize_settings

class Migrator():
    def __init__(self) -> None:
        self.app_settings = initialize_settings()

    def start_migrations(self):
        self._create_database()
        self._run_migrations()
    def _create_database(self):
        """Create the database if it doesn't exist."""
        print(f"Creating database '{self.app_settings.MYSQL_DATABASE}' if not exists...")
        
        try:
            print("Connecting to MySQL with the following settings:")
            print(f"  Host: {self.app_settings.MYSQL_HOST}")
            print(f"  Port: {self.app_settings.MYSQL_PORT}")
            print(f"  User: {self.app_settings.MYSQL_USER}")
            print(f"  Password: {self.app_settings.MYSQL_PASSWORD}")
            print(f"  Database: {self.app_settings.MYSQL_DATABASE}")
            connection = pymysql.connect(
                host=self.app_settings.MYSQL_HOST,
                port=int(self.app_settings.MYSQL_PORT),
                user=self.app_settings.MYSQL_USER,
                password=self.app_settings.MYSQL_PASSWORD
            )
            
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.app_settings.MYSQL_DATABASE}")
                print(f"✅ Database ready")
            
            connection.commit()
            connection.close()
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            sys.exit(1)

    def _run_migrations(self):
        """Run Alembic migrations."""
        print("Running Alembic migrations...")
        try:
            subprocess.run(["alembic", "upgrade", "head"], check=True)
            print("✅ Migrations completed")
            
            subprocess.run(["alembic", "current"], check=True)
            print("✅ Current migration status shown")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrator = Migrator()
    migrator.start_migrations()
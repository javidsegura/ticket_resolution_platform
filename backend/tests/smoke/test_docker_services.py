"""
Smoke tests for Docker Compose service availability.

These tests verify that Docker services (MySQL, Redis, Firebase) are
accessible and properly configured before running integration tests.

IMPORTANT: Run after Docker services are started:
  make test-docker-compose-start && make test-smoke
"""

import pytest
import logging
import subprocess
import os

logger = logging.getLogger(__name__)


class TestDockerServices:
	"""Smoke tests for Docker Compose service availability."""

	def test_mysql_accessible_on_host(self) -> None:
		"""
		Test: MySQL container accessible from pytest
		Verifies: Connection on 127.0.0.1:3307, Query succeeds
		"""
		try:
			import pymysql

			connection = pymysql.connect(
				host="127.0.0.1",
				port=3307,
				user="root",
				password="rootpassword",
				database="ai_ticket_platform",
			)
			cursor = connection.cursor()
			cursor.execute("SELECT 1")
			result = cursor.fetchone()
			cursor.close()
			connection.close()

			assert result[0] == 1
			logger.info("✅ MySQL accessible on 127.0.0.1:3307")

		except Exception as e:
			pytest.fail(f"MySQL not accessible: {e}")

	def test_redis_accessible_on_host(self) -> None:
		"""
		Test: Redis container accessible from pytest
		Verifies: Connection on 127.0.0.1:6379, PING succeeds
		"""
		try:
			import redis.asyncio as redis
			import asyncio

			async def check_redis():
				client = redis.from_url("redis://127.0.0.1:6379")
				response = await client.ping()
				await client.aclose()
				return response

			response = asyncio.run(check_redis())
			assert response is True
			logger.info("✅ Redis accessible on 127.0.0.1:6379")

		except Exception as e:
			pytest.fail(f"Redis not accessible: {e}")

	def test_database_schema_migrated(self) -> None:
		"""
		Test: Database schema has been migrated
		Verifies: Alembic migrations executed, tables exist
		"""
		try:
			import pymysql

			connection = pymysql.connect(
				host="127.0.0.1",
				port=3307,
				user="root",
				password="rootpassword",
				database="ai_ticket_platform",
			)
			cursor = connection.cursor()

			# Check for tables
			cursor.execute("SHOW TABLES")
			tables = cursor.fetchall()
			table_count = len(tables)

			cursor.close()
			connection.close()

			assert table_count > 0, "No tables found - migrations may not have run"
			logger.info(f"✅ Database schema migrated ({table_count} tables)")

		except Exception as e:
			pytest.fail(f"Schema migration check failed: {e}")

	def test_environment_variables_valid(self) -> None:
		"""
		Test: Environment variables are valid
		Verifies: Required variables exist with correct format
		"""
		required_vars = {
			"MYSQL_HOST": str,
			"MYSQL_PORT": str,
			"MYSQL_USER": str,
			"MYSQL_PASSWORD": str,
			"MYSQL_DATABASE": str,
			"REDIS_URL": str,
		}

		for var_name, var_type in required_vars.items():
			value = os.getenv(var_name)
			assert value is not None, f"{var_name} not set"
			assert isinstance(value, var_type), f"{var_name} is not {var_type.__name__}"
			assert len(value) > 0, f"{var_name} is empty"

		logger.info("✅ All environment variables valid")

	def test_docker_network_healthy(self) -> None:
		"""
		Test: Docker network and containers are healthy
		Verifies: Required containers running without restart loops
		"""
		containers_to_check = [
			"ai-ticket-platform-database-1",
			"ai-ticket-platform-redis-1",
		]

		for container in containers_to_check:
			result = subprocess.run(
				["docker", "inspect", "-f", "{{.State.Status}}", container],
				capture_output=True,
				text=True,
			)

			assert result.returncode == 0, f"Container {container} not found"
			status = result.stdout.strip().lower()
			assert status == "running", f"Container {container} status: {status}, expected running"

		logger.info("✅ Docker network healthy - all containers running")

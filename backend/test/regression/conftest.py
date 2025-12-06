import os
import sys
from fastapi.testclient import TestClient
import pytest
import uuid
import subprocess
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv



ORIGINAL_ENV_KEYS = None

def pytest_configure(config):
    """Mock all required environment variables for tests."""
    global ORIGINAL_ENV_KEYS
    ORIGINAL_ENV_KEYS = set(os.environ.keys())
    if "ENVIRONMENT" in set(os.environ.keys()):
        del os.environ["ENVIRONMENT"]
    path_to_dotenv = "./env_config/synced/.env.test"
    if not os.path.exists(path_to_dotenv):
        raise FileNotFoundError(f"Could not find dotenv file at {path_to_dotenv}")
    else:
        print(f"Path found for {path_to_dotenv}")
    load_dotenv(path_to_dotenv)
    if "MYSQL_HOST" in set(os.environ.keys()): # DB migration container and test (usage needed now) use different vals for the same key
        os.environ["MYSQL_HOST"] = "localhost"
        print("Just modified MYSQL_HOST")
    if "MYSQL_PORT" in set(os.environ.keys()):
        os.environ["MYSQL_PORT"] = "3307"
        print("Just modified MYSQL_PORT")
    print(f"ENV FOR INITIALIZATION IS: {set(os.environ.keys())}")



def pytest_unconfigure(config):
    """
    This hook runs after the entire test session finishes,
    perfect for cleanup.
    """
    print("\nCleaning up environment variables...")
    CURRENT_ENV_KEYS = set(os.environ.keys())
    keys_to_del = ORIGINAL_ENV_KEYS - CURRENT_ENV_KEYS
    for key in keys_to_del:
        if key in os.environ:
                del os.environ[key]

@pytest.fixture(scope="session")
def fastapi_client():
      from ai_ticket_platform.main import app
      with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def start_docker_compose_services():
    """Start docker compose and wait for migrations to complete."""

    # Start docker compose services in detached mode
    try:
        print("🚀 Starting Docker Compose services...")
        subprocess.run(
            ["make", "test-start"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Docker Compose services started")

        # Wait for the migration container to finish
        print("⏳ Waiting for database migrations to complete...")
        try:
            result = subprocess.run(
                ["docker", "wait", "url-shortener-db-migration-1"],
                check=True,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            exit_code = result.stdout.strip()

            if exit_code != "0":
                # Migration failed - get logs
                logs_result = subprocess.run(
                    ["docker", "logs", "url-shortener-db-migration-1"],
                    capture_output=True,
                    text=True
                )
                print("❌ Migration container failed!")
                print("Migration logs:")
                print(logs_result.stdout)
                print(logs_result.stderr)
                raise RuntimeError(f"Migration exited with code {exit_code}")

            print("✅ Migrations completed successfully")

        except subprocess.TimeoutExpired:
            print("❌ Migration timeout - fetching logs...")
            logs_result = subprocess.run(
                ["docker", "logs", "url-shortener-db-migration-1"],
                capture_output=True,
                text=True
            )
            print(logs_result.stdout)
            print(logs_result.stderr)
            raise RuntimeError("Migration took too long to complete")

    except subprocess.CalledProcessError as e:
        print("❌ Failed to start docker-compose:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        raise

    yield

    # Cleanup
    print("🧹 Cleaning up Docker Compose services...")
    subprocess.run(
        args=["make", "test-stop"],
        check=True
    )


# @ALEX ADJUST THIS BELOW IF NEEDED
# @pytest_asyncio.fixture(scope="session")
# async def db_session(start_docker_compose_services):
#     """Provide a database session for tests."""
#     async for session in get_db():
#         yield session
#         break

# @pytest_asyncio.fixture(scope="session", autouse=True)
# async def populate_database(db_session):
#     """Populate the database with test data."""
#     users = [
#         User(
#             user_id="12345",
#             displayable_name="testUserName",
#             email="test@gmail.com",
#             profile_pic_object_name="images/user1",
#             country="USA",
#         )
#     ]

#     for user in users:
#         await create_user(db_session, user_data=user)

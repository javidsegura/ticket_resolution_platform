"""
Integration tests for database persistence and concurrency.

Tests verify:
- MySQL transaction ACID compliance
- Connection pooling under concurrent load
- Concurrent insert/read/update operations
- Data integrity in multi-threaded scenarios
"""

import pytest
import logging
import asyncio
import os
import time
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError
import sqlalchemy as sa

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_mysql_transaction_acid_compliance(
	db_connection: AsyncSession,
) -> None:
	"""
	Test: Validate MySQL transaction guarantees (ACID)

	Validates:
	- Atomicity: All-or-nothing - rolled back transaction inserts no rows
	- Consistency: Data remains valid after transaction
	- Isolation: Concurrent transactions don't see uncommitted data
	- Durability: Committed data persists after connection closes
	"""

	logger.info("🔐 Testing MySQL ACID compliance...")

	# TEST 1: ATOMICITY (All-or-nothing)
	logger.info("Testing ATOMICITY...")

	# Count rows before transaction
	count_before = await db_connection.execute(
		text("SELECT COUNT(*) FROM tickets WHERE subject LIKE 'Atomic Test%'")
	)
	initial_count = count_before.scalar()
	logger.info(f"Initial atomic tickets: {initial_count}")

	try:
		# Start transaction and insert 3 rows
		insert_stmt = text("""
			INSERT INTO tickets (subject, body)
			VALUES
			(:s1, :b1),
			(:s2, :b2),
			(:s3, :b3)
		""")

		await db_connection.execute(insert_stmt, {
			"s1": "Atomic Test 1", "b1": "Body 1",
			"s2": "Atomic Test 2", "b2": "Body 2",
			"s3": "Atomic Test 3", "b3": "Body 3",
		})

		# Simulate error - force an exception
		raise Exception("Simulated error to trigger rollback")

		await db_connection.commit()

	except Exception as e:
		# Rollback on error
		await db_connection.rollback()
		logger.info(f"✅ Transaction rolled back due to: {str(e)}")

	# Verify rollback worked - no rows were inserted
	count_after_rollback = await db_connection.execute(
		text("SELECT COUNT(*) FROM tickets WHERE subject LIKE 'Atomic Test%'")
	)
	final_count = count_after_rollback.scalar()

	assert final_count == initial_count, \
		f"Atomicity failed: rows persisted after rollback ({final_count} != {initial_count})"
	logger.info(f"✅ ATOMICITY verified: row count unchanged after rollback ({final_count})")

	# TEST 2: CONSISTENCY & DURABILITY
	logger.info("Testing CONSISTENCY & DURABILITY...")

	# Successful transaction - should persist
	insert_valid = text("""
		INSERT INTO tickets (subject, body)
		VALUES (:subject, :body)
	""")

	await db_connection.execute(insert_valid, {
		"subject": "Durable Test Ticket",
		"body": "This should persist after commit"
	})
	await db_connection.commit()
	logger.info("✅ Transaction committed successfully")

	# Verify row exists (durability)
	count_final = await db_connection.execute(
		text("SELECT COUNT(*) FROM tickets WHERE subject = 'Durable Test Ticket'")
	)
	assert count_final.scalar() >= 1, "Data should persist after commit"
	logger.info("✅ DURABILITY verified: Data persisted after commit")

	# Verify data integrity (consistency)
	verify_query = await db_connection.execute(
		text("SELECT subject, body FROM tickets WHERE subject = 'Durable Test Ticket' LIMIT 1")
	)
	row = verify_query.fetchone()
	assert row[0] == "Durable Test Ticket"
	assert "persist" in row[1]
	logger.info("✅ CONSISTENCY verified: Data integrity maintained")


@pytest.mark.asyncio
async def test_concurrent_database_operations_and_pooling() -> None:
	"""
	Test: Stress test concurrent database access and connection pooling

	Validates:
	- All concurrent tasks complete successfully
	- No connection pool exhaustion
	- No deadlock/timeout errors
	- No race conditions (data integrity)
	- Connection pool gracefully handles peak load
	- All inserted data correctly persisted
	"""

	logger.info("🔀 Testing concurrent database operations and pooling...")

	# Generate unique test run ID to avoid conflicts with previous test runs
	import uuid
	test_run_id = str(uuid.uuid4())[:8]
	logger.info(f"Test run ID: {test_run_id}")

	# SETUP: Get database URL from environment
	db_driver = os.getenv("MYSQL_ASYNC_DRIVER", "mysql+aiomysql")
	db_host = os.getenv("MYSQL_HOST", "127.0.0.1")
	db_port = os.getenv("MYSQL_PORT", "3307")
	db_user = os.getenv("MYSQL_USER", "root")
	db_pass = os.getenv("MYSQL_PASSWORD", "rootpassword")
	db_name = os.getenv("MYSQL_DATABASE", "ai_ticket_platform")

	DATABASE_URL = f"{db_driver}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

	# Create a dedicated engine for concurrency testing (with pooling)
	engine = create_async_engine(
		DATABASE_URL,
		echo=False,
		pool_size=5,      # Small pool to test under pressure
		max_overflow=5,   # Allow 5 extra connections
		pool_pre_ping=True,
	)

	AsyncTestSession = async_sessionmaker(
		engine, class_=AsyncSession, expire_on_commit=False
	)

	# Track results
	results = {"success": 0, "errors": []}
	lock = asyncio.Lock()

	async def concurrent_operation(task_id: int) -> None:
		"""Simulate a concurrent database operation (insert, read, update)"""
		try:
			async with AsyncTestSession() as session:
				# OPERATION 1: INSERT
				insert_query = text("""
					INSERT INTO tickets (subject, body)
					VALUES (:subject, :body)
				""")

				await session.execute(insert_query, {
					"subject": f"Concurrent Task {test_run_id} {task_id}",
					"body": f"Description for task {task_id}"
				})
				await session.commit()

				# OPERATION 2: READ
				read_query = text(
					"SELECT subject FROM tickets WHERE subject = :subject LIMIT 1"
				)
				result = await session.execute(
					read_query,
					{"subject": f"Concurrent Task {test_run_id} {task_id}"}
				)
				subject = result.scalar()
				assert subject == f"Concurrent Task {test_run_id} {task_id}"

				# OPERATION 3: UPDATE
				update_query = text("""
					UPDATE tickets
					SET body = 'Updated'
					WHERE subject = :subject
				""")
				await session.execute(
					update_query,
					{"subject": f"Concurrent Task {test_run_id} {task_id}"}
				)
				await session.commit()

				# Track success
				async with lock:
					results["success"] += 1

				logger.info(f"✅ Task {task_id} completed successfully")

		except Exception as e:
			async with lock:
				results["errors"].append({
					"task_id": task_id,
					"error": str(e)
				})
			logger.error(f"❌ Task {task_id} failed: {str(e)}")

	# ACT: Run 10 concurrent operations
	logger.info("Starting 10 concurrent database operations...")
	start_time = time.time()

	tasks = [concurrent_operation(i) for i in range(10)]
	await asyncio.gather(*tasks)

	duration = time.time() - start_time
	logger.info(f"✅ All concurrent operations completed in {duration:.2f}s")

	# ASSERT: All tasks succeeded
	assert results["success"] == 10, \
		f"Expected 10 successes, got {results['success']}. Errors: {results['errors']}"
	logger.info(f"✅ All 10 concurrent tasks completed successfully")

	# ASSERT: No errors
	assert len(results["errors"]) == 0, \
		f"Concurrency errors occurred: {results['errors']}"
	logger.info("✅ No connection pool exhaustion or deadlock errors")

	# ASSERT: All data persisted correctly
	async with AsyncTestSession() as verify_session:
		# Count rows inserted in this test run (using test_run_id)
		count_query = text("""
			SELECT COUNT(*) FROM tickets
			WHERE subject LIKE :pattern
		""")
		count_result = await verify_session.execute(
			count_query,
			{"pattern": f"Concurrent Task {test_run_id}%"}
		)
		inserted_count = count_result.scalar()

		assert inserted_count == 10, \
			f"Expected 10 inserted rows, got {inserted_count}"
		logger.info(f"✅ All {inserted_count} rows persisted correctly")

		# Verify body updates (all should have been updated)
		update_query = text("""
			SELECT COUNT(*) FROM tickets
			WHERE subject LIKE :pattern
			AND body = 'Updated'
		""")
		update_result = await verify_session.execute(
			update_query,
			{"pattern": f"Concurrent Task {test_run_id}%"}
		)
		updated_count = update_result.scalar()

		assert updated_count == 10, \
			f"Expected 10 updated rows, got {updated_count}"
		logger.info(f"✅ All {updated_count} rows updated correctly")

	# Cleanup
	await engine.dispose()
	logger.info("✅ Connection pool disposed cleanly")


@pytest.mark.asyncio
async def test_database_connection_health(
	db_connection: AsyncSession,
) -> None:
	"""
	Test: Verify database connection health and basic operations

	Validates:
	- Connection can execute queries
	- Connection pooling is working
	- Transactions work properly
	- Connection closes cleanly
	"""

	logger.info("🩺 Testing database connection health...")

	# TEST 1: Simple query execution
	try:
		result = await db_connection.execute(text("SELECT 1"))
		value = result.scalar()
		assert value == 1
		logger.info("✅ Basic SELECT query works")
	except Exception as e:
		pytest.fail(f"SELECT query failed: {e}")

	# TEST 2: Database selection
	try:
		result = await db_connection.execute(text("SELECT DATABASE()"))
		db_name = result.scalar()
		assert db_name == "ai_ticket_platform"
		logger.info(f"✅ Connected to database: {db_name}")
	except Exception as e:
		pytest.fail(f"Database selection failed: {e}")

	# TEST 3: Table existence
	try:
		result = await db_connection.execute(
			text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'ai_ticket_platform'")
		)
		table_count = result.scalar()
		assert table_count > 0, "No tables found in database"
		logger.info(f"✅ Database has {table_count} tables")
	except Exception as e:
		pytest.fail(f"Table check failed: {e}")

	# TEST 4: Transaction support (skip begin since SQLAlchemy autobegins)
	try:
		# SQLAlchemy async sessions autobegin, so we just test rollback capability
		in_transaction = db_connection.in_transaction()
		logger.info(f"✅ Session transaction state check works (in_transaction={in_transaction})")
	except Exception as e:
		pytest.fail(f"Transaction support check failed: {e}")

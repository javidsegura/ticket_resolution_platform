"""Unit tests for user CRUD operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from ai_ticket_platform.database.CRUD.user import (
	create_user,
	get_user_by_id,
	get_all_users,
	update_user,
	delete_user,
)


@pytest.mark.asyncio
class TestCreateUser:
	"""Test create_user function."""

	async def test_create_user_success(self):
		"""Test successful user creation."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.user.User") as mock_user_class:
			mock_user = MagicMock()
			mock_user.id = 1
			mock_user.name = "John Doe"
			mock_user.email = "john@example.com"
			mock_user.role = "admin"
			mock_user.slack_user_id = "U12345"
			mock_user.area = "Engineering"
			mock_user_class.return_value = mock_user

			result = await create_user(
				db=mock_db,
				name="John Doe",
				email="john@example.com",
				role="admin",
				slack_user_id="U12345",
				area="Engineering",
			)

			assert result.name == "John Doe"
			assert result.email == "john@example.com"
			assert result.role == "admin"
			assert result.slack_user_id == "U12345"
			assert result.area == "Engineering"
			mock_db.add.assert_called_once_with(mock_user)
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once_with(mock_user)

	async def test_create_user_without_area(self):
		"""Test user creation without optional area field."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.user.User") as mock_user_class:
			mock_user = MagicMock()
			mock_user.id = 1
			mock_user.name = "Jane Doe"
			mock_user.email = "jane@example.com"
			mock_user.role = "user"
			mock_user.slack_user_id = "U67890"
			mock_user.area = None
			mock_user_class.return_value = mock_user

			result = await create_user(
				db=mock_db,
				name="Jane Doe",
				email="jane@example.com",
				role="user",
				slack_user_id="U67890",
			)

			assert result.name == "Jane Doe"
			assert result.area is None
			mock_db.commit.assert_called_once()

	async def test_create_user_db_error(self):
		"""Test user creation with database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
		mock_db.rollback = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.user.User"):
			with pytest.raises(RuntimeError, match="Failed to create user"):
				await create_user(
					db=mock_db,
					name="Test User",
					email="test@example.com",
					role="user",
					slack_user_id="U11111",
				)

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestGetUserById:
	"""Test get_user_by_id function."""

	async def test_get_user_by_id_success(self):
		"""Test successful retrieval of user by ID."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_user = MagicMock()
		mock_user.id = 1
		mock_user.name = "John Doe"
		mock_user.email = "john@example.com"
		mock_result.scalar_one_or_none.return_value = mock_user

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_user_by_id(db=mock_db, user_id=1)

		assert result.id == 1
		assert result.name == "John Doe"
		assert result.email == "john@example.com"
		mock_db.execute.assert_called_once()

	async def test_get_user_by_id_not_found(self):
		"""Test retrieval of non-existent user."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_user_by_id(db=mock_db, user_id=999)

		assert result is None


@pytest.mark.asyncio
class TestGetAllUsers:
	"""Test get_all_users function."""

	async def test_get_all_users_success(self):
		"""Test successful retrieval of all users."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_user_1 = MagicMock()
		mock_user_1.id = 1
		mock_user_2 = MagicMock()
		mock_user_2.id = 2

		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [mock_user_1, mock_user_2]

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_users(db=mock_db, skip=0, limit=100)

		assert len(result) == 2
		assert result[0].id == 1
		assert result[1].id == 2
		mock_db.execute.assert_called_once()

	async def test_get_all_users_empty(self):
		"""Test retrieval when no users exist."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = []

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_users(db=mock_db, skip=0, limit=100)

		assert len(result) == 0

	async def test_get_all_users_with_pagination(self):
		"""Test retrieval with custom pagination."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_user = MagicMock()
		mock_user.id = 1

		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [mock_user]

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_users(db=mock_db, skip=10, limit=5)

		assert len(result) == 1
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestUpdateUser:
	"""Test update_user function."""

	async def test_update_user_all_fields(self):
		"""Test updating all fields of user."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		mock_user = MagicMock()
		mock_user.id = 1
		mock_user.name = "Old Name"
		mock_user.email = "old@example.com"
		mock_user.role = "user"
		mock_user.slack_user_id = "U11111"
		mock_user.area = "Old Area"

		with patch(
			"ai_ticket_platform.database.CRUD.user.get_user_by_id",
			new=AsyncMock(return_value=mock_user),
		):
			result = await update_user(
				db=mock_db,
				user_id=1,
				name="New Name",
				email="new@example.com",
				role="admin",
				slack_user_id="U22222",
				area="New Area",
			)

			assert result.name == "New Name"
			assert result.email == "new@example.com"
			assert result.role == "admin"
			assert result.slack_user_id == "U22222"
			assert result.area == "New Area"
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once_with(mock_user)

	async def test_update_user_partial_fields(self):
		"""Test updating only some fields of user."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		mock_user = MagicMock()
		mock_user.id = 1
		mock_user.name = "Original Name"
		mock_user.email = "original@example.com"
		mock_user.role = "user"

		with patch(
			"ai_ticket_platform.database.CRUD.user.get_user_by_id",
			new=AsyncMock(return_value=mock_user),
		):
			result = await update_user(db=mock_db, user_id=1, name="Updated Name")

			assert result.name == "Updated Name"
			assert result.email == "original@example.com"
			assert result.role == "user"
			mock_db.commit.assert_called_once()

	async def test_update_user_not_found(self):
		"""Test updating non-existent user."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch(
			"ai_ticket_platform.database.CRUD.user.get_user_by_id",
			new=AsyncMock(return_value=None),
		):
			result = await update_user(db=mock_db, user_id=999, name="New Name")

			assert result is None

	async def test_update_user_db_error(self):
		"""Test updating user with database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
		mock_db.rollback = AsyncMock()

		mock_user = MagicMock()
		mock_user.id = 1

		with patch(
			"ai_ticket_platform.database.CRUD.user.get_user_by_id",
			new=AsyncMock(return_value=mock_user),
		):
			with pytest.raises(RuntimeError, match="Failed to update user"):
				await update_user(db=mock_db, user_id=1, name="New Name")

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestDeleteUser:
	"""Test delete_user function."""

	async def test_delete_user_success(self):
		"""Test successful deletion of user."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.delete = AsyncMock()
		mock_db.commit = AsyncMock()

		mock_user = MagicMock()
		mock_user.id = 1

		with patch(
			"ai_ticket_platform.database.CRUD.user.get_user_by_id",
			new=AsyncMock(return_value=mock_user),
		):
			result = await delete_user(db=mock_db, user_id=1)

			assert result is True
			mock_db.delete.assert_called_once_with(mock_user)
			mock_db.commit.assert_called_once()

	async def test_delete_user_not_found(self):
		"""Test deletion of non-existent user."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch(
			"ai_ticket_platform.database.CRUD.user.get_user_by_id",
			new=AsyncMock(return_value=None),
		):
			result = await delete_user(db=mock_db, user_id=999)

			assert result is False

	async def test_delete_user_db_error(self):
		"""Test deletion with database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.delete = AsyncMock()
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
		mock_db.rollback = AsyncMock()

		mock_user = MagicMock()
		mock_user.id = 1

		with patch(
			"ai_ticket_platform.database.CRUD.user.get_user_by_id",
			new=AsyncMock(return_value=mock_user),
		):
			with pytest.raises(RuntimeError, match="Failed to delete user"):
				await delete_user(db=mock_db, user_id=1)

			mock_db.rollback.assert_called_once()

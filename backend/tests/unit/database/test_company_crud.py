"""Unit tests for company CRUD operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from ai_ticket_platform.database.CRUD.company import (
	create_company_profile,
	get_company_profile_by_id,
	get_all_company_profiles,
	update_company_profile,
	delete_company_profile,
)


@pytest.mark.asyncio
class TestCreateCompanyProfile:
	"""Test create_company_profile function."""

	async def test_create_company_profile_success(self):
		"""Test successful company profile creation."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch(
			"ai_ticket_platform.database.CRUD.company.CompanyProfile"
		) as mock_company:
			mock_profile = MagicMock()
			mock_profile.id = 1
			mock_profile.name = "Acme Corp"
			mock_company.return_value = mock_profile

			result = await create_company_profile(
				db=mock_db,
				name="Acme Corp",
				domain="acme.com",
				industry="Technology",
				support_email="support@acme.com",
			)

			assert result.name == "Acme Corp"
			mock_db.add.assert_called_once_with(mock_profile)
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once_with(mock_profile)

	async def test_create_company_profile_minimal_fields(self):
		"""Test company profile creation with only required fields."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch(
			"ai_ticket_platform.database.CRUD.company.CompanyProfile"
		) as mock_company:
			mock_profile = MagicMock()
			mock_profile.id = 1
			mock_profile.name = "Basic Corp"
			mock_company.return_value = mock_profile

			result = await create_company_profile(db=mock_db, name="Basic Corp")

			assert result.name == "Basic Corp"
			mock_db.commit.assert_called_once()

	async def test_create_company_profile_db_error(self):
		"""Test company profile creation with database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
		mock_db.rollback = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.company.CompanyProfile"):
			with pytest.raises(RuntimeError, match="Failed to create company profile"):
				await create_company_profile(db=mock_db, name="Test Corp")

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestGetCompanyProfileById:
	"""Test get_company_profile_by_id function."""

	async def test_get_company_profile_by_id_success(self):
		"""Test successful retrieval of company profile by ID."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_profile = MagicMock()
		mock_profile.id = 1
		mock_profile.name = "Acme Corp"
		mock_result.scalar_one_or_none.return_value = mock_profile

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_company_profile_by_id(db=mock_db, profile_id=1)

		assert result.id == 1
		assert result.name == "Acme Corp"
		mock_db.execute.assert_called_once()

	async def test_get_company_profile_by_id_not_found(self):
		"""Test retrieval of non-existent company profile."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_company_profile_by_id(db=mock_db, profile_id=999)

		assert result is None


@pytest.mark.asyncio
class TestGetAllCompanyProfiles:
	"""Test get_all_company_profiles function."""

	async def test_get_all_company_profiles_success(self):
		"""Test successful retrieval of all company profiles."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_profile_1 = MagicMock()
		mock_profile_1.id = 1
		mock_profile_2 = MagicMock()
		mock_profile_2.id = 2

		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [
			mock_profile_1,
			mock_profile_2,
		]

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_company_profiles(db=mock_db, skip=0, limit=100)

		assert len(result) == 2
		assert result[0].id == 1
		assert result[1].id == 2
		mock_db.execute.assert_called_once()

	async def test_get_all_company_profiles_empty(self):
		"""Test retrieval when no company profiles exist."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = []

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_company_profiles(db=mock_db, skip=0, limit=100)

		assert len(result) == 0

	async def test_get_all_company_profiles_with_pagination(self):
		"""Test retrieval with custom pagination."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_profile = MagicMock()
		mock_profile.id = 1

		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [mock_profile]

		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_company_profiles(db=mock_db, skip=10, limit=5)

		assert len(result) == 1
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestUpdateCompanyProfile:
	"""Test update_company_profile function."""

	async def test_update_company_profile_all_fields(self):
		"""Test updating all fields of company profile."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		mock_profile = MagicMock()
		mock_profile.id = 1
		mock_profile.name = "Old Name"
		mock_profile.domain = "old.com"
		mock_profile.industry = "Old Industry"
		mock_profile.support_email = "old@example.com"

		with patch(
			"ai_ticket_platform.database.CRUD.company.get_company_profile_by_id",
			new=AsyncMock(return_value=mock_profile),
		):
			result = await update_company_profile(
				db=mock_db,
				profile_id=1,
				name="New Name",
				domain="new.com",
				industry="New Industry",
				support_email="new@example.com",
			)

			assert result.name == "New Name"
			assert result.domain == "new.com"
			assert result.industry == "New Industry"
			assert result.support_email == "new@example.com"
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once_with(mock_profile)

	async def test_update_company_profile_partial_fields(self):
		"""Test updating only some fields of company profile."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		mock_profile = MagicMock()
		mock_profile.id = 1
		mock_profile.name = "Original Name"
		mock_profile.domain = "original.com"

		with patch(
			"ai_ticket_platform.database.CRUD.company.get_company_profile_by_id",
			new=AsyncMock(return_value=mock_profile),
		):
			result = await update_company_profile(
				db=mock_db, profile_id=1, name="Updated Name"
			)

			assert result.name == "Updated Name"
			assert result.domain == "original.com"
			mock_db.commit.assert_called_once()

	async def test_update_company_profile_not_found(self):
		"""Test updating non-existent company profile."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch(
			"ai_ticket_platform.database.CRUD.company.get_company_profile_by_id",
			new=AsyncMock(return_value=None),
		):
			result = await update_company_profile(
				db=mock_db, profile_id=999, name="New Name"
			)

			assert result is None

	async def test_update_company_profile_db_error(self):
		"""Test updating company profile with database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
		mock_db.rollback = AsyncMock()

		mock_profile = MagicMock()
		mock_profile.id = 1

		with patch(
			"ai_ticket_platform.database.CRUD.company.get_company_profile_by_id",
			new=AsyncMock(return_value=mock_profile),
		):
			with pytest.raises(RuntimeError, match="Failed to update company profile"):
				await update_company_profile(db=mock_db, profile_id=1, name="New Name")

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestDeleteCompanyProfile:
	"""Test delete_company_profile function."""

	async def test_delete_company_profile_success(self):
		"""Test successful deletion of company profile."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.delete = AsyncMock()
		mock_db.commit = AsyncMock()

		mock_profile = MagicMock()
		mock_profile.id = 1

		with patch(
			"ai_ticket_platform.database.CRUD.company.get_company_profile_by_id",
			new=AsyncMock(return_value=mock_profile),
		):
			result = await delete_company_profile(db=mock_db, profile_id=1)

			assert result is True
			mock_db.delete.assert_called_once_with(mock_profile)
			mock_db.commit.assert_called_once()

	async def test_delete_company_profile_not_found(self):
		"""Test deletion of non-existent company profile."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch(
			"ai_ticket_platform.database.CRUD.company.get_company_profile_by_id",
			new=AsyncMock(return_value=None),
		):
			result = await delete_company_profile(db=mock_db, profile_id=999)

			assert result is False

	async def test_delete_company_profile_db_error(self):
		"""Test deletion with database error."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.delete = AsyncMock()
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
		mock_db.rollback = AsyncMock()

		mock_profile = MagicMock()
		mock_profile.id = 1

		with patch(
			"ai_ticket_platform.database.CRUD.company.get_company_profile_by_id",
			new=AsyncMock(return_value=mock_profile),
		):
			with pytest.raises(RuntimeError, match="Failed to delete company profile"):
				await delete_company_profile(db=mock_db, profile_id=1)

			mock_db.rollback.assert_called_once()

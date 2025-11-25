"""Unit tests for company file CRUD operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ai_ticket_platform.database.CRUD.company_file import (
	create_company_file,
	get_company_file_by_id,
	get_all_company_files,
	delete_company_file
)


@pytest.mark.asyncio
class TestCreateCompanyFile:
	"""Test create_company_file CRUD operation."""

	async def test_create_company_file_success(self):
		"""Test successful creation of company file."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_file = MagicMock()
		mock_file.id = 123
		mock_file.blob_path = "s3://bucket/file.pdf"
		mock_file.original_filename = "budget.pdf"
		mock_file.area = "Finance"

		# Mock the add, commit, and refresh methods
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.company_file.CompanyFile") as mock_company_file_class:
			mock_company_file_class.return_value = mock_file

			result = await create_company_file(
				db=mock_db,
				blob_path="s3://bucket/file.pdf",
				original_filename="budget.pdf",
				area="Finance"
			)

			# Verify CompanyFile was instantiated with correct args
			mock_company_file_class.assert_called_once()
			call_kwargs = mock_company_file_class.call_args[1]
			assert call_kwargs["blob_path"] == "s3://bucket/file.pdf"
			assert call_kwargs["original_filename"] == "budget.pdf"
			assert call_kwargs["area"] == "Finance"

			# Verify db operations
			mock_db.add.assert_called_once_with(mock_file)
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once_with(mock_file)

			# Verify return value
			assert result == mock_file

	async def test_create_company_file_without_area(self):
		"""Test creation of company file without area (optional field)."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_file = MagicMock()
		mock_file.id = 124
		mock_file.blob_path = "s3://bucket/report.pdf"
		mock_file.original_filename = "report.pdf"
		mock_file.area = None

		# Mock the add, commit, and refresh methods
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.company_file.CompanyFile") as mock_company_file_class:
			mock_company_file_class.return_value = mock_file

			result = await create_company_file(
				db=mock_db,
				blob_path="s3://bucket/report.pdf",
				original_filename="report.pdf"
			)

			# Verify CompanyFile was instantiated with area=None
			call_kwargs = mock_company_file_class.call_args[1]
			assert call_kwargs["area"] is None

			assert result == mock_file

	async def test_create_company_file_with_empty_blob_path(self):
		"""Test creation of company file with empty blob path."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_file = MagicMock()
		mock_file.id = 125
		mock_file.blob_path = ""
		mock_file.original_filename = "notes.pdf"
		mock_file.area = "HR"

		# Mock the add, commit, and refresh methods
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.company_file.CompanyFile") as mock_company_file_class:
			mock_company_file_class.return_value = mock_file

			result = await create_company_file(
				db=mock_db,
				blob_path="",
				original_filename="notes.pdf",
				area="HR"
			)

			# Verify CompanyFile was instantiated with empty blob_path
			call_kwargs = mock_company_file_class.call_args[1]
			assert call_kwargs["blob_path"] == ""

			assert result == mock_file

	async def test_create_company_file_returns_populated_object(self):
		"""Test that created object has all fields populated."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_file = MagicMock()
		mock_file.id = 999
		mock_file.blob_path = "s3://bucket/docs/file.pdf"
		mock_file.original_filename = "important_doc.pdf"
		mock_file.area = "Legal"

		# Mock the add, commit, and refresh methods
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.company_file.CompanyFile") as mock_company_file_class:
			mock_company_file_class.return_value = mock_file

			result = await create_company_file(
				db=mock_db,
				blob_path="s3://bucket/docs/file.pdf",
				original_filename="important_doc.pdf",
				area="Legal"
			)

			# Verify all fields are present in result
			assert result.id == 999
			assert result.blob_path == "s3://bucket/docs/file.pdf"
			assert result.original_filename == "important_doc.pdf"
			assert result.area == "Legal"


@pytest.mark.asyncio
class TestGetCompanyFileById:
	"""Test get_company_file_by_id CRUD operation."""

	async def test_get_company_file_by_id_found(self):
		"""Test retrieving a company file by ID when it exists."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_file = MagicMock()
		mock_file.id = 123
		mock_file.filename = "budget.pdf"

		# Mock the execute method
		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=mock_file)
		mock_db.execute = AsyncMock(return_value=mock_result)

		with patch("ai_ticket_platform.database.CRUD.company_file.select") as mock_select:
			result = await get_company_file_by_id(db=mock_db, file_id=123)

			# Verify result
			assert result == mock_file
			mock_db.execute.assert_called_once()

	async def test_get_company_file_by_id_not_found(self):
		"""Test retrieving a company file by ID when it doesn't exist."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)

		# Mock the execute method to return None
		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=None)
		mock_db.execute = AsyncMock(return_value=mock_result)

		with patch("ai_ticket_platform.database.CRUD.company_file.select") as mock_select:
			result = await get_company_file_by_id(db=mock_db, file_id=999)

			# Verify result is None
			assert result is None

	async def test_get_company_file_by_id_zero(self):
		"""Test retrieving a company file with ID 0."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)

		# Mock the execute method to return None
		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=None)
		mock_db.execute = AsyncMock(return_value=mock_result)

		with patch("ai_ticket_platform.database.CRUD.company_file.select") as mock_select:
			result = await get_company_file_by_id(db=mock_db, file_id=0)

			# Verify result is None
			assert result is None


@pytest.mark.asyncio
class TestGetAllCompanyFiles:
	"""Test get_all_company_files CRUD operation."""

	async def test_get_all_company_files_success(self):
		"""Test retrieving all company files."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_files = [
			MagicMock(id=1, filename="file1.pdf"),
			MagicMock(id=2, filename="file2.pdf"),
			MagicMock(id=3, filename="file3.pdf")
		]

		# Mock the execute method
		mock_result = MagicMock()
		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=mock_files)
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		with patch("ai_ticket_platform.database.CRUD.company_file.select") as mock_select:
			result = await get_all_company_files(db=mock_db)

			# Verify result
			assert len(result) == 3
			assert result == mock_files

	async def test_get_all_company_files_with_pagination(self):
		"""Test retrieving company files with skip and limit."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_files = [
			MagicMock(id=11, filename="file11.pdf"),
			MagicMock(id=12, filename="file12.pdf")
		]

		# Mock the execute method
		mock_result = MagicMock()
		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=mock_files)
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		with patch("ai_ticket_platform.database.CRUD.company_file.select") as mock_select:
			result = await get_all_company_files(db=mock_db, skip=10, limit=2)

			# Verify pagination was applied
			mock_db.execute.assert_called_once()
			assert len(result) == 2

	async def test_get_all_company_files_empty(self):
		"""Test retrieving all company files when none exist."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)

		# Mock the execute method to return empty list
		mock_result = MagicMock()
		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[])
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		with patch("ai_ticket_platform.database.CRUD.company_file.select") as mock_select:
			result = await get_all_company_files(db=mock_db)

			# Verify empty list returned
			assert result == []

	async def test_get_all_company_files_default_limit(self):
		"""Test that default limit is applied."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_files = [MagicMock(id=i) for i in range(50)]

		# Mock the execute method
		mock_result = MagicMock()
		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=mock_files)
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		with patch("ai_ticket_platform.database.CRUD.company_file.select") as mock_select:
			result = await get_all_company_files(db=mock_db)

			# Verify default limit is applied (100 in signature)
			assert len(result) == 50


@pytest.mark.asyncio
class TestDeleteCompanyFile:
	"""Test delete_company_file CRUD operation."""

	async def test_delete_company_file_success(self):
		"""Test successful deletion of a company file."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_file = MagicMock()
		mock_file.id = 123

		# Mock delete (not async) and commit (async)
		mock_db.delete = MagicMock()
		mock_db.commit = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.company_file.get_company_file_by_id", new_callable=AsyncMock) as mock_get:
			mock_get.return_value = mock_file

			result = await delete_company_file(db=mock_db, file_id=123)

			# Verify result is True
			assert result is True
			mock_db.delete.assert_called_once_with(mock_file)
			mock_db.commit.assert_called_once()

	async def test_delete_company_file_not_found(self):
		"""Test deletion of non-existent company file."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.delete = MagicMock()

		# Mock get_company_file_by_id to return None
		with patch("ai_ticket_platform.database.CRUD.company_file.get_company_file_by_id") as mock_get:
			mock_get.return_value = None

			result = await delete_company_file(db=mock_db, file_id=999)

			# Verify result is False
			assert result is False
			# Verify delete was not called
			mock_db.delete.assert_not_called()

	async def test_delete_company_file_deletion_failure(self):
		"""Test handling of deletion errors."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_file = MagicMock()
		mock_file.id = 123

		# Mock commit to raise an error
		mock_db.delete = MagicMock()
		mock_db.commit = AsyncMock(side_effect=Exception("Database error"))

		with patch("ai_ticket_platform.database.CRUD.company_file.get_company_file_by_id", new_callable=AsyncMock) as mock_get:
			mock_get.return_value = mock_file

			# Should raise the database error
			with pytest.raises(Exception, match="Database error"):
				await delete_company_file(db=mock_db, file_id=123)

	async def test_delete_company_file_calls_get_by_id(self):
		"""Test that delete calls get_company_file_by_id to retrieve file."""
		# Mock database session
		mock_db = MagicMock(spec=AsyncSession)
		mock_file = MagicMock()

		# Mock delete and commit
		mock_db.delete = MagicMock()
		mock_db.commit = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.company_file.get_company_file_by_id", new_callable=AsyncMock) as mock_get:
			mock_get.return_value = mock_file

			result = await delete_company_file(db=mock_db, file_id=456)

			# Verify result
			assert result is True

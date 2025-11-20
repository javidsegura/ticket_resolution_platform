import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from ai_ticket_platform.database.CRUD.company_file import (
	create_company_file,
	get_company_file_by_id,
	get_all_company_files,
	delete_company_file,
)
from ai_ticket_platform.database.generated_models import CompanyFile


class TestCreateCompanyFile:
	"""Test suite for create_company_file function."""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session."""
		db = Mock(spec=Session)
		return db

	def test_create_company_file_with_area(self, mock_db):
		"""Test creating a company file with area specified."""
		# setup
		blob_path = "s3://bucket/path/to/file.pdf"
		original_filename = "test_document.pdf"
		area = "Tech"

		# mock the database behavior
		def side_effect_add(obj):
			obj.id = 1

		mock_db.add.side_effect = side_effect_add

		# execute
		result = create_company_file(
			db=mock_db,
			blob_path=blob_path,
			original_filename=original_filename,
			area=area
		)

		# verify
		mock_db.add.assert_called_once()
		mock_db.commit.assert_called_once()
		mock_db.refresh.assert_called_once()

		# verify the created object has correct attributes
		added_obj = mock_db.add.call_args[0][0]
		assert isinstance(added_obj, CompanyFile)
		assert added_obj.blob_path == blob_path
		assert added_obj.original_filename == original_filename
		assert added_obj.area == area

	def test_create_company_file_without_area(self, mock_db):
		"""Test creating a company file without area (defaults to None)."""
		# setup
		blob_path = "s3://bucket/path/to/file.pdf"
		original_filename = "test_document.pdf"

		# mock the database behavior
		def side_effect_add(obj):
			obj.id = 2

		mock_db.add.side_effect = side_effect_add

		# execute
		result = create_company_file(
			db=mock_db,
			blob_path=blob_path,
			original_filename=original_filename
		)

		# verify
		mock_db.add.assert_called_once()
		mock_db.commit.assert_called_once()

		# verify the created object has correct attributes
		added_obj = mock_db.add.call_args[0][0]
		assert added_obj.area is None


class TestGetCompanyFileById:
	"""Test suite for get_company_file_by_id function."""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session."""
		db = Mock(spec=Session)
		return db

	def test_get_company_file_by_id_found(self, mock_db):
		"""Test retrieving an existing company file by ID."""
		# setup
		file_id = 1
		mock_file = CompanyFile(
			id=file_id,
			blob_path="s3://bucket/file.pdf",
			original_filename="test.pdf",
			area="Finance"
		)

		mock_result = Mock()
		mock_result.scalar_one_or_none.return_value = mock_file
		mock_db.execute.return_value = mock_result

		# execute
		result = get_company_file_by_id(db=mock_db, file_id=file_id)

		# verify
		assert result == mock_file
		assert result.id == file_id
		assert result.area == "Finance"
		mock_db.execute.assert_called_once()

	def test_get_company_file_by_id_not_found(self, mock_db):
		"""Test retrieving a non-existent company file returns None."""
		# setup
		file_id = 999

		mock_result = Mock()
		mock_result.scalar_one_or_none.return_value = None
		mock_db.execute.return_value = mock_result

		# execute
		result = get_company_file_by_id(db=mock_db, file_id=file_id)

		# verify
		assert result is None
		mock_db.execute.assert_called_once()


class TestGetAllCompanyFiles:
	"""Test suite for get_all_company_files function."""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session."""
		db = Mock(spec=Session)
		return db

	def test_get_all_company_files_with_results(self, mock_db):
		"""Test retrieving all company files when files exist."""
		# setup
		mock_files = [
			CompanyFile(id=1, blob_path="path1.pdf", original_filename="file1.pdf", area="Tech"),
			CompanyFile(id=2, blob_path="path2.pdf", original_filename="file2.pdf", area="HR"),
			CompanyFile(id=3, blob_path="path3.pdf", original_filename="file3.pdf", area="Finance"),
		]

		mock_scalars = Mock()
		mock_scalars.all.return_value = mock_files

		mock_result = Mock()
		mock_result.scalars.return_value = mock_scalars
		mock_db.execute.return_value = mock_result

		# execute
		result = get_all_company_files(db=mock_db)

		# verify
		assert len(result) == 3
		assert result[0].id == 1
		assert result[1].area == "HR"
		assert result[2].original_filename == "file3.pdf"
		mock_db.execute.assert_called_once()

	def test_get_all_company_files_empty(self, mock_db):
		"""Test retrieving all company files when database is empty."""
		# setup
		mock_scalars = Mock()
		mock_scalars.all.return_value = []

		mock_result = Mock()
		mock_result.scalars.return_value = mock_scalars
		mock_db.execute.return_value = mock_result

		# execute
		result = get_all_company_files(db=mock_db)

		# verify
		assert result == []
		mock_db.execute.assert_called_once()


class TestDeleteCompanyFile:
	"""Test suite for delete_company_file function."""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session."""
		db = Mock(spec=Session)
		return db

	def test_delete_company_file_success(self, mock_db):
		"""Test successfully deleting an existing company file."""
		# setup
		file_id = 1
		mock_file = CompanyFile(
			id=file_id,
			blob_path="s3://bucket/file.pdf",
			original_filename="test.pdf",
			area="Tech"
		)

		mock_result = Mock()
		mock_result.scalar_one_or_none.return_value = mock_file
		mock_db.execute.return_value = mock_result

		# execute
		result = delete_company_file(db=mock_db, file_id=file_id)

		# verify
		assert result is True
		mock_db.delete.assert_called_once_with(mock_file)
		mock_db.commit.assert_called_once()

	def test_delete_company_file_not_found(self, mock_db):
		"""Test deleting a non-existent company file returns False."""
		# setup
		file_id = 999

		mock_result = Mock()
		mock_result.scalar_one_or_none.return_value = None
		mock_db.execute.return_value = mock_result

		# execute
		result = delete_company_file(db=mock_db, file_id=file_id)

		# verify
		assert result is False
		mock_db.delete.assert_not_called()
		mock_db.commit.assert_not_called()

"""Unit tests for CSV parser."""

import pytest
import tempfile
import os
from pathlib import Path


class TestParseCSVFile:
	"""Test parse_csv_file function."""

	def test_parse_csv_success(self):
		"""Test successful CSV parsing with valid data."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file

		# Create temporary CSV file
		with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
			f.write("id,created_at,subject,body\n")
			f.write("1,2024-01-01,Test Subject 1,Test body 1\n")
			f.write("2,2024-01-02,Test Subject 2,Test body 2\n")
			tmp_path = f.name

		try:
			result = parse_csv_file(tmp_path)

			assert result["success"] is True
			assert result["file_info"]["rows_processed"] == 2
			assert result["file_info"]["rows_skipped"] == 0
			assert result["file_info"]["tickets_extracted"] == 2
			assert len(result["tickets"]) == 2
			assert result["tickets"][0]["subject"] == "Test Subject 1"
			assert result["tickets"][0]["body"] == "Test body 1"
			assert result["tickets"][1]["subject"] == "Test Subject 2"
		finally:
			os.unlink(tmp_path)

	def test_parse_csv_file_not_found(self):
		"""Test that FileNotFoundError is raised for missing file."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file

		with pytest.raises(FileNotFoundError) as exc_info:
			parse_csv_file("/nonexistent/file.csv")

		assert "CSV file not found" in str(exc_info.value)

	def test_parse_csv_missing_required_columns(self):
		"""Test that ValueError is raised when required columns are missing."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file

		# Create CSV without required columns
		with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
			f.write("id,created_at\n")
			f.write("1,2024-01-01\n")
			tmp_path = f.name

		try:
			with pytest.raises(ValueError) as exc_info:
				parse_csv_file(tmp_path)

			assert "Missing:" in str(exc_info.value)
			assert "subject" in str(exc_info.value) or "body" in str(exc_info.value)
		finally:
			os.unlink(tmp_path)

	def test_parse_csv_empty_file(self):
		"""Test that ValueError is raised for empty CSV."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file

		# Create empty CSV
		with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
			tmp_path = f.name

		try:
			with pytest.raises(ValueError) as exc_info:
				parse_csv_file(tmp_path)

			assert "empty or invalid" in str(exc_info.value)
		finally:
			os.unlink(tmp_path)

	def test_parse_csv_skip_empty_rows(self):
		"""Test that rows with empty subject or body are skipped."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file

		with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
			f.write("subject,body\n")
			f.write("Test Subject 1,Test body 1\n")
			f.write(",Test body 2\n")  # Empty subject
			f.write("Test Subject 3,\n")  # Empty body
			f.write("Test Subject 4,Test body 4\n")
			tmp_path = f.name

		try:
			result = parse_csv_file(tmp_path)

			assert result["success"] is True
			assert result["file_info"]["rows_processed"] == 4
			assert result["file_info"]["rows_skipped"] == 2
			assert len(result["tickets"]) == 2
			assert result["tickets"][0]["subject"] == "Test Subject 1"
			assert result["tickets"][1]["subject"] == "Test Subject 4"
		finally:
			os.unlink(tmp_path)

	def test_parse_csv_invalid_created_at(self):
		"""Test handling of invalid created_at dates."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file

		with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
			f.write("subject,body,created_at\n")
			f.write("Test Subject 1,Test body 1,invalid-date\n")
			f.write("Test Subject 2,Test body 2,2024-01-02\n")
			tmp_path = f.name

		try:
			result = parse_csv_file(tmp_path)

			# Row with invalid date should be skipped
			assert result["success"] is True
			assert len(result["tickets"]) == 1
			assert result["tickets"][0]["subject"] == "Test Subject 2"
			assert len(result["errors"]) == 1
			assert "created_at" in result["errors"][0]
		finally:
			os.unlink(tmp_path)

	def test_parse_csv_no_valid_tickets(self):
		"""Test that ValueError is raised when no valid tickets are found."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file

		with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
			f.write("subject,body\n")
			f.write(",\n")  # Empty row
			f.write("  ,  \n")  # Whitespace only
			tmp_path = f.name

		try:
			with pytest.raises(ValueError) as exc_info:
				parse_csv_file(tmp_path)

			assert "No valid tickets found" in str(exc_info.value)
		finally:
			os.unlink(tmp_path)

	def test_parse_csv_with_datetime_timestamp(self):
		"""Test parsing CSV with full datetime timestamp."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file

		with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
			f.write("subject,body,created_at\n")
			f.write("Test Subject,Test body,2024-01-01 10:30:00\n")
			tmp_path = f.name

		try:
			result = parse_csv_file(tmp_path)

			assert result["success"] is True
			assert len(result["tickets"]) == 1
			assert result["tickets"][0]["created_at"] is not None
		finally:
			os.unlink(tmp_path)


class TestDetectEncoding:
	"""Test _detect_encoding function."""

	def test_detect_encoding_utf8(self):
		"""Test detecting UTF-8 encoding."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import _detect_encoding

		with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
			f.write("Test UTF-8 content")
			tmp_path = f.name

		try:
			encoding = _detect_encoding(Path(tmp_path))
			assert encoding in ['utf-8-sig', 'utf-8']
		finally:
			os.unlink(tmp_path)

	def test_detect_encoding_fallback(self):
		"""Test encoding detection falls back to utf-8 when all fail."""
		from ai_ticket_platform.services.csv_uploader.csv_parser import _detect_encoding
		from unittest.mock import patch

		# Create a real file but mock the open to always raise UnicodeDecodeError
		with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
			f.write("Test content")
			tmp_path = f.name

		try:
			with patch("builtins.open", side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test')):
				encoding = _detect_encoding(Path(tmp_path))
				assert encoding == "utf-8"
		finally:
			os.unlink(tmp_path)

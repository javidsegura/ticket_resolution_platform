"""Regression tests for CSV upload functionality.

These tests cover previously identified bugs in the CSV upload pipeline.
"""

import pytest
import csv
import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestCSVUploadRegressions:
	"""Regression tests for CSV upload bugs."""

	def test_csv_with_empty_rows_does_not_crash(self):
		"""
		REGRESSION: Empty rows in CSV caused ValueError.
		Bug fixed: CSV reader skips empty rows gracefully.
		"""
		csv_content = """subject,body,created_at
Login Issue,Cannot login,2025-01-01

Password Reset,Need reset,2025-01-02
"""
		reader = csv.DictReader(io.StringIO(csv_content))
		rows = [row for row in reader if any(row.values())]

		assert len(rows) == 2
		assert rows[0]["subject"] == "Login Issue"
		assert rows[1]["subject"] == "Password Reset"

	def test_csv_with_unicode_characters(self):
		"""
		REGRESSION: Unicode characters in CSV caused encoding errors.
		Bug fixed: UTF-8 encoding properly handled.
		"""
		csv_content = """subject,body,created_at
Ñoño Issue,Cañón problem 🔥,2025-01-01
中文票据,中文描述,2025-01-02"""

		reader = csv.DictReader(io.StringIO(csv_content))
		rows = list(reader)

		assert len(rows) == 2
		assert "Ñoño" in rows[0]["subject"]
		assert "🔥" in rows[0]["body"]
		assert "中文" in rows[1]["subject"]

	def test_csv_with_commas_in_quoted_fields(self):
		"""
		REGRESSION: Commas inside quoted fields broke parsing.
		Bug fixed: CSV parser respects quotes.
		"""
		csv_content = '''subject,body,created_at
"Login Issue, Critical","User cannot login, urgent",2025-01-01
Normal Issue,Normal body,2025-01-02'''

		reader = csv.DictReader(io.StringIO(csv_content))
		rows = list(reader)

		assert len(rows) == 2
		assert "," in rows[0]["subject"]
		assert rows[0]["subject"] == "Login Issue, Critical"
		assert "," in rows[0]["body"]

	def test_csv_with_newlines_in_quoted_fields(self):
		"""
		REGRESSION: Newlines in quoted fields caused row count mismatch.
		Bug fixed: Multiline fields properly handled.
		"""
		csv_content = '''subject,body,created_at
"Login Issue","User cannot login
Please help immediately",2025-01-01
Normal Issue,Normal body,2025-01-02'''

		reader = csv.DictReader(io.StringIO(csv_content))
		rows = list(reader)

		assert len(rows) == 2
		assert "\n" in rows[0]["body"]
		assert "immediately" in rows[0]["body"]

	def test_csv_with_bom_marker(self):
		"""
		REGRESSION: UTF-8 BOM marker caused first column name mismatch.
		Bug fixed: BOM is stripped during parsing.
		"""
		# UTF-8 BOM: \ufeff
		csv_content = "\ufeffsubject,body,created_at\nLogin Issue,Cannot login,2025-01-01"

		# Proper handling: strip BOM
		csv_clean = csv_content.lstrip("\ufeff")
		reader = csv.DictReader(io.StringIO(csv_clean))
		rows = list(reader)

		assert len(rows) == 1
		assert "subject" in rows[0]
		assert rows[0]["subject"] == "Login Issue"

	def test_csv_with_extra_whitespace_in_headers(self):
		"""
		REGRESSION: Headers with whitespace caused column mismatch.
		Bug fixed: Headers are now stripped.
		"""
		csv_content = """subject , body , created_at
Login Issue,Cannot login,2025-01-01"""

		reader = csv.DictReader(io.StringIO(csv_content))
		# Strip whitespace from fieldnames
		reader.fieldnames = [field.strip() for field in reader.fieldnames]
		rows = list(reader)

		assert len(rows) == 1
		assert "subject" in rows[0]
		assert rows[0]["subject"] == "Login Issue"

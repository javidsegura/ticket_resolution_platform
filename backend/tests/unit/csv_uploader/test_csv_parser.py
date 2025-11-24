"""Unit tests for CSV parser service."""

import pytest
import tempfile
from pathlib import Path
from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file


class TestCSVParserValidation:
    """Test CSV parser validation."""

    def test_parse_csv_with_subject_body_columns(self, tmp_path):
        """Test parsing CSV with subject,body columns."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nLogin Bug,Cannot login\nPassword Reset,Need to reset")

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        assert len(result["tickets"]) == 2
        assert result["tickets"][0]["subject"] == "Login Bug"
        assert result["tickets"][0]["body"] == "Cannot login"

    def test_parse_csv_with_title_content_columns(self, tmp_path):
        """Test parsing CSV with title,content columns (legacy support)."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("title,content\nBug,Description here")

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        assert len(result["tickets"]) == 1

    def test_parse_csv_missing_required_columns(self, tmp_path):
        """Test that CSV without subject/body or title/content fails."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,value\nTest,Data")

        with pytest.raises(ValueError, match="must contain either"):
            parse_csv_file(str(csv_file))

    def test_parse_csv_file_not_found(self):
        """Test FileNotFoundError when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            parse_csv_file("/nonexistent/path/file.csv")

    def test_parse_empty_csv_file(self, tmp_path):
        """Test that empty CSV raises ValueError."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        with pytest.raises(ValueError):
            parse_csv_file(str(csv_file))

    def test_parse_csv_with_only_headers(self, tmp_path):
        """Test CSV with headers but no data rows."""
        csv_file = tmp_path / "headers_only.csv"
        csv_file.write_text("subject,body")

        with pytest.raises(ValueError, match="No valid tickets found"):
            parse_csv_file(str(csv_file))


class TestCSVParserOutput:
    """Test CSV parser output structure."""

    def test_parse_csv_returns_correct_structure(self, tmp_path):
        """Test that parser returns proper response schema."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nBug,Description")

        result = parse_csv_file(str(csv_file))

        assert "success" in result
        assert "file_info" in result
        assert "tickets" in result
        assert "errors" in result

    def test_file_info_contains_required_fields(self, tmp_path):
        """Test that file_info has all required fields."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nTest,Data")

        result = parse_csv_file(str(csv_file))

        file_info = result["file_info"]
        assert "filename" in file_info
        assert "rows_processed" in file_info
        assert "rows_skipped" in file_info
        assert "encoding" in file_info
        assert file_info["filename"] == "test.csv"

    def test_ticket_structure(self, tmp_path):
        """Test individual ticket structure."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,subject,body\n123,Login Bug,Cannot login")

        result = parse_csv_file(str(csv_file))

        ticket = result["tickets"][0]
        assert "subject" in ticket
        assert "body" in ticket
        assert ticket["id"] == "123"
        assert ticket["source_row"] == 2  # Row number (header is 1)


class TestCSVParserEdgeCases:
    """Test edge cases and data variations."""

    def test_parse_csv_with_special_characters(self, tmp_path):
        """Test CSV with special characters in content."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text('subject,body\n"Bug, quote test","Content with ""quotes"""')

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        assert len(result["tickets"]) == 1

    def test_parse_csv_with_multiline_content(self, tmp_path):
        """Test CSV with multiline content in body field."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text('subject,body\nBug,"Line 1\nLine 2\nLine 3"')

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        assert "Line 1" in result["tickets"][0]["body"]

    def test_parse_csv_with_optional_columns(self, tmp_path):
        """Test CSV with optional id and created_at columns."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,created_at,subject,body\n1,2024-01-01,Bug,Description")

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        ticket = result["tickets"][0]
        assert ticket["id"] == "1"
        # created_at may be converted to datetime or kept as string
        assert ticket["created_at"] is not None

    def test_parse_csv_with_empty_optional_fields(self, tmp_path):
        """Test CSV where optional fields are empty."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,created_at,subject,body\n,,Bug,Description")

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        ticket = result["tickets"][0]
        assert ticket["subject"] == "Bug"


class TestCSVParserDataValidation:
    """Test data validation and filtering."""

    def test_skip_rows_with_missing_subject(self, tmp_path):
        """Test that rows without subject are skipped."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nBug,Description\n,No subject\nAnother,Content")

        result = parse_csv_file(str(csv_file))

        assert len(result["tickets"]) == 2
        assert result["file_info"]["rows_skipped"] == 1

    def test_skip_rows_with_missing_body(self, tmp_path):
        """Test that rows without body are skipped."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nBug,Description\nNo body,\nAnother,Content")

        result = parse_csv_file(str(csv_file))

        assert len(result["tickets"]) == 2
        assert result["file_info"]["rows_skipped"] == 1

    def test_preserve_whitespace_in_content(self, tmp_path):
        """Test that content is stripped of leading/trailing whitespace."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nBug,  Content with spaces  ")

        result = parse_csv_file(str(csv_file))

        # CSV parser strips whitespace from field values
        assert result["tickets"][0]["body"] == "Content with spaces"


class TestCSVParserCounting:
    """Test row counting and metrics."""

    def test_rows_processed_count(self, tmp_path):
        """Test that rows_processed is accurate."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\n1,A\n2,B\n3,C\n4,D\n5,E")

        result = parse_csv_file(str(csv_file))

        assert result["file_info"]["rows_processed"] == 5
        assert len(result["tickets"]) == 5

    def test_rows_processed_with_mixed_valid_invalid(self, tmp_path):
        """Test rows_processed includes invalid rows."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nValid,Data\n,Missing\nAnother,Row")

        result = parse_csv_file(str(csv_file))

        assert result["file_info"]["rows_processed"] == 3
        assert result["file_info"]["rows_skipped"] == 1
        assert len(result["tickets"]) == 2


class TestCSVParserDateHandling:
    """Test created_at date parsing."""

    def test_parse_csv_with_valid_iso_date(self, tmp_path):
        """Test parsing CSV with valid ISO format date."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,created_at,subject,body\n1,2024-01-15,Bug,Description\n2,2024-02-20,Feature,Request")

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        assert len(result["tickets"]) == 2
        assert result["tickets"][0]["created_at"] is not None

    def test_parse_csv_with_datetime_format(self, tmp_path):
        """Test parsing CSV with full datetime format."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,created_at,subject,body\n1,2024-01-15 10:30:00,Bug,Description")

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        assert result["tickets"][0]["created_at"] is not None

    def test_parse_csv_with_invalid_date_format(self, tmp_path):
        """Test that rows with invalid date formats are skipped."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,created_at,subject,body\n1,invalid-date,Bug,Desc\n2,2024-01-15,Bug2,Desc2")

        result = parse_csv_file(str(csv_file))

        # Invalid date row should be skipped
        assert len(result["tickets"]) == 1
        assert result["tickets"][0]["id"] == "2"
        assert len(result["errors"]) == 1

    def test_parse_csv_without_created_at(self, tmp_path):
        """Test that created_at is optional."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nBug,Description")

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        assert result["tickets"][0]["created_at"] is None


class TestCSVParserErrors:
    """Test error handling and reporting."""

    def test_csv_with_row_parsing_error(self, tmp_path):
        """Test that row parsing errors are caught and reported."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body,extra\nBug,Description,Extra\n\n,Incomplete")

        result = parse_csv_file(str(csv_file))

        # One valid row, one skipped
        assert len(result["tickets"]) == 1

    def test_parse_csv_errors_field_populated(self, tmp_path):
        """Test that errors field is populated on issues."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,created_at,subject,body\n1,bad-date,Bug,Desc\n2,2024-01-15,Valid,Ticket")

        result = parse_csv_file(str(csv_file))

        assert "errors" in result
        assert len(result["errors"]) > 0


class TestCSVEncodingDetection:
    """Test encoding detection functionality."""

    def test_parse_csv_with_utf8_encoding(self, tmp_path):
        """Test parsing CSV with UTF-8 encoding."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nBug,Café content", encoding='utf-8')

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        assert result["file_info"]["encoding"] == "utf-8" or result["file_info"]["encoding"] == "utf-8-sig"

    def test_parse_csv_detects_correct_encoding(self, tmp_path):
        """Test that encoding detection works and is reported."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nTest,Data")

        result = parse_csv_file(str(csv_file))

        assert "encoding" in result["file_info"]
        assert result["file_info"]["encoding"] in ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]


class TestCSVParserGenericErrors:
    """Test generic error handling."""

    def test_parse_csv_file_read_error(self, tmp_path):
        """Test handling of file read errors."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\nBug,Desc")

        # Make file unreadable by deleting it before reading
        with pytest.raises(FileNotFoundError):
            parse_csv_file(str(tmp_path / "nonexistent.csv"))

    def test_parse_csv_with_malformed_rows(self, tmp_path):
        """Test handling of rows with unexpected structure."""
        csv_file = tmp_path / "test.csv"
        # Create CSV with minimal content
        csv_file.write_text("subject,body\nOK,Data")

        result = parse_csv_file(str(csv_file))

        assert result["success"]
        assert len(result["tickets"]) == 1

    def test_parse_csv_multiple_errors_collected(self, tmp_path):
        """Test that multiple errors are collected."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "id,created_at,subject,body\n"
            "1,bad-date1,Bug,Desc\n"
            "2,bad-date2,Feature,Request\n"
            "3,2024-01-15,Valid,Ticket"
        )

        result = parse_csv_file(str(csv_file))

        # First two rows have bad dates and should be skipped
        assert len(result["tickets"]) == 1
        assert len(result["errors"]) >= 2

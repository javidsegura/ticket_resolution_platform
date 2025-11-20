"""Tests for CSV uploader"""
import pytest
from pathlib import Path
from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file


class TestParseCSVFile:
    """Test CSV parser"""

    @pytest.fixture
    def valid_csv(self, tmp_path):
        """Valid CSV with subject and body"""
        csv = tmp_path / "valid.csv"
        csv.write_text("id,subject,body\n1,Subject1,Body1\n2,Subject2,Body2\n")
        return str(csv)

    @pytest.fixture
    def csv_empty_subject(self, tmp_path):
        """CSV with one empty subject"""
        csv = tmp_path / "empty_subject.csv"
        csv.write_text("id,subject,body\n1,,Body1\n2,Subject2,Body2\n")
        return str(csv)

    @pytest.fixture
    def csv_empty_body(self, tmp_path):
        """CSV with one empty body"""
        csv = tmp_path / "empty_body.csv"
        csv.write_text("id,subject,body\n1,Subject1,\n2,Subject2,Body2\n")
        return str(csv)

    @pytest.fixture
    def csv_missing_columns(self, tmp_path):
        """CSV missing required columns"""
        csv = tmp_path / "missing.csv"
        csv.write_text("id,created_at\n1,2024-01-01\n")
        return str(csv)

    def test_parse_valid_csv(self, valid_csv):
        """Test parsing valid CSV"""
        result = parse_csv_file(valid_csv)
        
        assert result["success"] is True
        assert len(result["tickets"]) == 2
        assert result["file_info"]["rows_skipped"] == 0

    def test_ticket_structure(self, valid_csv):
        """Test ticket has correct fields"""
        result = parse_csv_file(valid_csv)
        ticket = result["tickets"][0]
        
        assert ticket["Ticket Subject"] == "Subject1"
        assert ticket["body"] == "Body1"
        assert "id" in ticket
        assert "source_row" in ticket

    def test_skip_empty_subject(self, csv_empty_subject):
        """Test skip rows with empty subject"""
        result = parse_csv_file(csv_empty_subject)
        assert len(result["tickets"]) == 1
        assert result["file_info"]["rows_skipped"] == 1

    def test_skip_empty_body(self, csv_empty_body):
        """Test skip rows with empty body"""
        result = parse_csv_file(csv_empty_body)
        assert len(result["tickets"]) == 1
        assert result["file_info"]["rows_skipped"] == 1

    def test_missing_columns_raises_error(self, csv_missing_columns):
        """Test error when required columns missing"""
        with pytest.raises(ValueError) as exc:
            parse_csv_file(csv_missing_columns)
        assert "subject" in str(exc.value).lower()
        assert "body" in str(exc.value).lower()

    def test_nonexistent_file_raises_error(self):
        """Test error for missing file"""
        with pytest.raises(FileNotFoundError):
            parse_csv_file("/nonexistent/file.csv")

    def test_file_info_present(self, valid_csv):
        """Test file_info has required fields"""
        result = parse_csv_file(valid_csv)
        assert "filename" in result["file_info"]
        assert "rows_processed" in result["file_info"]
        assert "encoding" in result["file_info"]
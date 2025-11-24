"""Unit tests for document decoder (PDF extraction)."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from io import BytesIO

from ai_ticket_platform.services.labeling.document_decoder import decode_document, MAX_CHARS


class TestDocumentDecoder:
    """Test PDF text extraction."""

    def test_decode_simple_pdf_success(self):
        """Test successful decoding of simple PDF."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 text"
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("test.pdf", content)

            assert result["success"] is True
            assert "Page 1 text" in result["content"]
            assert result["pages_read"] == 1

    def test_decode_multipage_pdf(self):
        """Test decoding PDF with multiple pages."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2"
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Page 3"

        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("test.pdf", content)

            assert result["success"] is True
            assert result["pages_read"] == 3
            assert "Page 1" in result["content"]
            assert "Page 2" in result["content"]
            assert "Page 3" in result["content"]

    def test_decode_respects_max_chars_limit(self):
        """Test that extraction stops at MAX_CHARS limit."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        # Create a page with text longer than MAX_CHARS
        long_text = "X" * (MAX_CHARS + 1000)
        mock_page = MagicMock()
        mock_page.extract_text.return_value = long_text

        mock_pdf.pages = [mock_page]
        mock_pdf.__len__ = 1
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("test.pdf", content)

            assert result["success"] is True
            assert len(result["content"]) <= MAX_CHARS

    def test_decode_stops_reading_at_max_chars(self):
        """Test that decoder stops reading pages at MAX_CHARS."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        # Page 1: 10000 chars
        # Page 2: would exceed MAX_CHARS
        # Page 3: shouldn't be read
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "X" * 10000
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Y" * 20000
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Z" * 5000

        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.__len__ = 3
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("test.pdf", content)

            assert result["success"] is True
            # Should have read only 2 pages (stopping partway through page 2)
            assert result["pages_read"] <= 2

    def test_decode_handles_empty_pages(self):
        """Test handling of pages with no extractable text."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = ""  # Empty page
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Page 3"

        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("test.pdf", content)

            assert result["success"] is True
            assert result["pages_read"] == 3
            assert "Page 1" in result["content"]
            assert "Page 3" in result["content"]

    def test_decode_handles_none_extract_text(self):
        """Test handling of pages with None extract_text result."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None  # None instead of empty string
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Page 3"

        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("test.pdf", content)

            assert result["success"] is True
            assert "Page 1" in result["content"]
            assert "Page 3" in result["content"]

    def test_decode_fails_on_extraction_exception(self):
        """Test handling of PDF extraction errors."""
        content = b"INVALID_PDF"

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.side_effect = Exception("PDF parsing error")

            result = decode_document("bad.pdf", content)

            assert result["success"] is False
            assert "error" in result

    def test_decode_no_text_extracted(self):
        """Test handling when no text can be extracted."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""  # No text

        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("empty.pdf", content)

            assert result["success"] is False
            assert "No text could be extracted" in result["error"]

    def test_decode_strips_content(self):
        """Test that extracted content is stripped of leading/trailing whitespace."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   Content   "

        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("test.pdf", content)

            assert result["success"] is True
            assert result["content"] == "Content"

    def test_decode_adds_newlines_between_pages(self):
        """Test that newlines are added between pages."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2"

        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("test.pdf", content)

            assert result["success"] is True
            # Should have newline between pages
            assert "Page 1\n" in result["content"]
            assert "Page 2" in result["content"]

    def test_decode_filename_preserved(self):
        """Test that filename is preserved in result."""
        content = b"PDF_CONTENT"

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Content"

        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None

        with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
            mock_open.return_value = mock_pdf

            result = decode_document("myfile.pdf", content)

            assert result["success"] is True
            # Filename is passed to document processor, not returned here

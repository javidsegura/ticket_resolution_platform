"""
Tests for document_decoder module.

Tests PDF text extraction using pdfplumber with mocked PDFs.
Tests are independent of external files.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from ai_ticket_platform.services.labeling.document_decoder import decode_document, MAX_CHARS


class TestDecodeDocument:
	"""Test suite for decode_document function with PDF processing."""

	def test_decode_pdf_success_single_page(self):
		"""Test successful PDF decoding with single page."""
		# setup
		filename = "test.pdf"
		content = b"fake pdf content"
		expected_text = "This is page 1 content"

		# mock pdfplumber
		with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
			mock_pdf = MagicMock()
			mock_page = Mock()
			mock_page.extract_text.return_value = expected_text
			mock_pdf.pages = [mock_page]
			mock_pdf.__enter__.return_value = mock_pdf
			mock_pdf.__exit__.return_value = None
			mock_open.return_value = mock_pdf

			# execute
			result = decode_document(filename, content)

			# verify
			assert result["success"] is True
			assert result["content"] == expected_text
			assert result["pages_read"] == 1
			assert "error" not in result

	def test_decode_pdf_success_multiple_pages(self):
		"""Test successful PDF decoding with multiple pages."""
		# setup
		filename = "multi_page.pdf"
		content = b"fake pdf content"
		page_texts = ["Page 1 text", "Page 2 text", "Page 3 text"]

		# mock pdfplumber
		with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
			mock_pdf = MagicMock()
			mock_pages = []
			for text in page_texts:
				mock_page = Mock()
				mock_page.extract_text.return_value = text
				mock_pages.append(mock_page)
			mock_pdf.pages = mock_pages
			mock_pdf.__enter__.return_value = mock_pdf
			mock_pdf.__exit__.return_value = None
			mock_open.return_value = mock_pdf

			# execute
			result = decode_document(filename, content)

			# verify
			assert result["success"] is True
			assert "Page 1 text" in result["content"]
			assert "Page 2 text" in result["content"]
			assert "Page 3 text" in result["content"]
			assert result["pages_read"] == 3

	def test_decode_pdf_empty_content(self):
		"""Test PDF with no extractable text."""
		# setup
		filename = "empty.pdf"
		content = b"fake pdf content"

		# mock pdfplumber with empty text
		with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
			mock_pdf = MagicMock()
			mock_page = Mock()
			mock_page.extract_text.return_value = ""
			mock_pdf.pages = [mock_page]
			mock_pdf.__enter__.return_value = mock_pdf
			mock_pdf.__exit__.return_value = None
			mock_open.return_value = mock_pdf

			# execute
			result = decode_document(filename, content)

			# verify
			assert result["success"] is False
			assert "error" in result
			assert "No text could be extracted" in result["error"]

	def test_decode_pdf_with_none_pages(self):
		"""Test handling of pages that return None for text."""
		# setup
		filename = "mixed.pdf"
		content = b"fake pdf content"

		# mock pdfplumber with mix of text and None
		with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
			mock_pdf = MagicMock()
			mock_page1 = Mock()
			mock_page1.extract_text.return_value = "Page 1"
			mock_page2 = Mock()
			mock_page2.extract_text.return_value = None  # Image-only page
			mock_page3 = Mock()
			mock_page3.extract_text.return_value = "Page 3"
			mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
			mock_pdf.__enter__.return_value = mock_pdf
			mock_pdf.__exit__.return_value = None
			mock_open.return_value = mock_pdf

			# execute
			result = decode_document(filename, content)

			# verify
			assert result["success"] is True
			assert "Page 1" in result["content"]
			assert "Page 3" in result["content"]
			assert result["pages_read"] == 3

	def test_decode_pdf_exception_handling(self):
		"""Test exception handling during PDF processing."""
		# setup
		filename = "corrupt.pdf"
		content = b"corrupted pdf content"

		# mock pdfplumber to raise exception
		with patch("ai_ticket_platform.services.labeling.document_decoder.pdfplumber.open") as mock_open:
			mock_open.side_effect = Exception("PDF is corrupted")

			# execute
			result = decode_document(filename, content)

			# verify
			assert result["success"] is False
			assert "error" in result
			assert "PDF extraction failed" in result["error"]
			assert "corrupted" in result["error"].lower()

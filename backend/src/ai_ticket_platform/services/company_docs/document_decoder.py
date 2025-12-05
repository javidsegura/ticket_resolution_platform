import logging
from typing import Dict
from io import BytesIO
import pdfplumber

logger = logging.getLogger(__name__)

# Maximum characters to extract from PDF
MAX_CHARS = 25000


def decode_document(filename: str, content: bytes) -> Dict:
	"""
	Extract text from PDF document, reading pages until MAX_CHARS limit.

	Args:
		filename: Original filename
		content: PDF file content as bytes

	Returns:
		Dict with either extracted text or error message
	"""
	try:
		text_content = ""
		pages_read = 0

		with pdfplumber.open(BytesIO(content)) as pdf:
			total_pages = len(pdf.pages)

			for page in pdf.pages:
				page_text = page.extract_text()

				if page_text:
					# Check if adding this page would exceed limit
					if len(text_content) + len(page_text) > MAX_CHARS:
						# Add partial page text to reach exactly MAX_CHARS
						remaining_chars = MAX_CHARS - len(text_content)
						text_content += page_text[:remaining_chars]
						pages_read += 1
						logger.info(
							f"Reached MAX_CHARS limit for {filename}. "
							f"Read {pages_read}/{total_pages} pages, {len(text_content)} chars"
						)
						break

					text_content += page_text + "\n"  # Add newline between pages
					pages_read += 1
				else:
					logger.debug(
						f"Page {pages_read + 1} of {filename} had no extractable text"
					)
					pages_read += 1

		if not text_content.strip():
			logger.warning(f"No text could be extracted from {filename}")
			return {"success": False, "error": "No text could be extracted from PDF"}

		logger.info(
			f"Extracted {len(text_content)} chars from {pages_read} pages of {filename}"
		)
		return {
			"success": True,
			"content": text_content.strip(),
			"pages_read": pages_read,
		}

	except Exception as e:
		logger.error(f"Error extracting text from {filename}: {str(e)}")
		return {"success": False, "error": f"PDF extraction failed: {str(e)}"}

"""
Document processor service.

Orchestrates the complete document processing workflow:
decode -> label -> store to database
"""

import asyncio
import logging
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.core.clients import LLMClient
from ai_ticket_platform.services.labeling.document_decoder import decode_document
from ai_ticket_platform.services.labeling.label_service import label_document
from ai_ticket_platform.database.CRUD.company_file import create_company_file

logger = logging.getLogger(__name__)


async def process_document(
	filename: str, content: bytes, llm_client: LLMClient, db: AsyncSession
) -> Dict:
	"""
	Process a single document: decode, label, and save to database.
	"""
	# decode content (CPU-bound operation)
	decode_result = await asyncio.to_thread(decode_document, filename, content)
	if not decode_result["success"]:
		return {"filename": filename, "success": False, "error": decode_result["error"]}

	# label document (I/O-bound operation)
	document = {"filename": filename, "content": decode_result["content"]}
	label_result = await asyncio.to_thread(
		label_document, document=document, llm_client=llm_client
	)

	if "error" in label_result:
		return {
			"filename": filename,
			"success": False,
			"error": f"Labeling failed: {label_result['error']}",
		}

	area = label_result.get("department_area", "Unknown")

	# save to database
	# TODO: upload content to blob storage and persist its path
	try:
		db_file = await create_company_file(
			db=db, blob_path="", original_filename=filename, area=area
		)

		logger.info(f"Processed document {filename} (ID: {db_file.id}, Area: {area})")

		return {
			"filename": filename,
			"success": True,
			"area": area,
			"file_id": db_file.id,
		}

	except Exception as e:
		logger.error(f"Error saving document {filename} to database: {str(e)}")
		return {
			"filename": filename,
			"success": False,
			"error": f"Database error: {str(e)}",
		}

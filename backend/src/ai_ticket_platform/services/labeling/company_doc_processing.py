"""
Complete company document processing: labeling + Azure AI Search indexing.

This service handles the full workflow:
1. Decode PDF document
2. Label with LLM (determine area/category)
3. Save to database
4. Index to Azure AI Search with embeddings
"""

import asyncio
import logging
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.core.clients import LLMClient
from ai_ticket_platform.services.labeling.document_decoder import decode_document
from ai_ticket_platform.services.labeling.label_service import label_document
from ai_ticket_platform.database.CRUD.company_file import create_company_file
from ai_ticket_platform.core.clients.azure_search import initialize_azure_search_indexer

logger = logging.getLogger(__name__)


async def process_and_index_document(
	filename: str, content: bytes, llm_client: LLMClient, db: AsyncSession, settings
) -> Dict:
	"""
	Complete document processing workflow:
	1. Decode PDF
	2. Label with LLM
	3. Save to database
	4. Index to Azure AI Search
	"""
	# Step 1: Decode PDF
	logger.info(f"[DOC PROCESSING] Step 1: Decoding {filename}")
	decode_result = await asyncio.to_thread(decode_document, filename, content)

	if not decode_result["success"]:
		return {
			"filename": filename,
			"success": False,
			"error": decode_result["error"],
			"indexed": False,
		}

	text_content = decode_result["content"]

	# Step 2: Label document with LLM
	logger.info(f"[DOC PROCESSING] Step 2: Labeling {filename}")
	document = {"filename": filename, "content": text_content}
	label_result = await asyncio.to_thread(
		label_document, document=document, llm_client=llm_client
	)

	if "error" in label_result:
		return {
			"filename": filename,
			"success": False,
			"error": f"Labeling failed: {label_result['error']}",
			"indexed": False,
		}

	area = label_result.get("department_area", "Unknown")

	# Step 3: Save to database
	logger.info(f"[DOC PROCESSING] Step 3: Saving {filename} to database (area: {area})")
	try:
		db_file = await create_company_file(
			db=db, blob_path="", original_filename=filename, area=area
		)

		logger.info(f"[DOC PROCESSING] Saved {filename} (ID: {db_file.id})")

		# Step 4: Index to Azure AI Search
		logger.info(f"[DOC PROCESSING] Step 4: Indexing {filename} to Azure AI Search")

		try:
			document_indexer = initialize_azure_search_indexer(settings)

			indexing_result = await document_indexer.index_document(
				file_id=db_file.id,
				filename=filename,
				content=text_content,
				area=area,
			)

			if indexing_result["status"] == "success":
				logger.info(
					f"[DOC PROCESSING] Successfully indexed {filename}: {indexing_result['successful']} chunks"
				)

				return {
					"filename": filename,
					"success": True,
					"area": area,
					"file_id": db_file.id,
					"indexed": True,
					"chunks_indexed": indexing_result["successful"],
				}
			else:
				logger.error(
					f"[DOC PROCESSING] Indexing failed for {filename}: {indexing_result.get('error')}"
				)

				return {
					"filename": filename,
					"success": True,  # DB save succeeded
					"area": area,
					"file_id": db_file.id,
					"indexed": False,
					"indexing_error": indexing_result.get("error"),
				}

		except Exception as index_error:
			logger.error(
				f"[DOC PROCESSING] Exception during indexing {filename}: {index_error}"
			)

			# Document is saved to DB, but indexing failed
			return {
				"filename": filename,
				"success": True,  # DB save succeeded
				"area": area,
				"file_id": db_file.id,
				"indexed": False,
				"indexing_error": str(index_error),
			}

	except Exception as e:
		logger.error(f"[DOC PROCESSING] Error saving {filename} to database: {str(e)}")
		return {
			"filename": filename,
			"success": False,
			"error": f"Database error: {str(e)}",
			"indexed": False,
		}

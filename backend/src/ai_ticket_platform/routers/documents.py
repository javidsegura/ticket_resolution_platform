import asyncio
from typing import Annotated, List
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ai_ticket_platform.core.clients import initialize_llm_client
from ai_ticket_platform.dependencies import get_app_settings, get_db
from ai_ticket_platform.core.settings import Settings
from ai_ticket_platform.services.labeling.document_processor import process_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents")


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_company_documents(
	files: List[UploadFile] = File(...),
	settings: Annotated[Settings, Depends(get_app_settings)] = None,
	db: Annotated[AsyncSession, Depends(get_db)] = None,
):
	"""
	Upload company PDF documents: label with LLM and save to database. Only PDF files are accepted (Right).
	"""
	llm_client = initialize_llm_client(settings)

	async def _process_single_file(file: UploadFile) -> dict:
		"""
		Process a single file with validation.
		"""
		# Validate PDF file type
		if not file.filename.lower().endswith(".pdf"):
			logger.warning(f"Rejected non-PDF file: {file.filename}")
			return {
				"filename": file.filename,
				"success": False,
				"error": "Only PDF files are accepted"
			}

		content = await file.read()

		# Process document using service layer
		result = await process_document(
			filename=file.filename,
			content=content,
			llm_client=llm_client,
			db=db,
		)

		return result

	# Process all files concurrently
	tasks = [_process_single_file(file) for file in files]
	results = await asyncio.gather(*tasks)

	# Count successes and failures
	successful_count = sum(1 for r in results if r["success"])
	failed_count = sum(1 for r in results if not r["success"])

	return {
		"total_processed": len(files),
		"successful": successful_count,
		"failed": failed_count,
		"results": list(results)
	}

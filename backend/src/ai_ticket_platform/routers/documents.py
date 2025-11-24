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
	Upload company PDF documents: label with LLM and save to database. Only PDF files are accepted.
	"""
	llm_client = initialize_llm_client(settings)

	# Process files sequentially to avoid concurrent use of a single AsyncSession
	results = []
	for file in files:
		# Validate PDF file type
		if not file.filename.lower().endswith(".pdf"):
			logger.warning(f"Rejected non-PDF file: {file.filename}")
			results.append({
				"filename": file.filename,
				"success": False,
				"error": "Only PDF files are accepted"
			})
			continue

		content = await file.read()

		# Process document using service layer
		result = await process_document(
			filename=file.filename,
			content=content,
			llm_client=llm_client,
			db=db,
		)

		results.append(result)

	# Count successes and failures
	successful_count = 0
	failed_count = 0
	for r in results:
		if r["success"]:
			successful_count += 1
		else:
			failed_count += 1

	return {
		"total_processed": len(files),
		"successful": successful_count,
		"failed": failed_count,
		"results": list(results)
	}

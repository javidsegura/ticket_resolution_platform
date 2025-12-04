from typing import Annotated, List
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ai_ticket_platform.core.clients.llm import get_llm_client
from ai_ticket_platform.dependencies import get_app_settings, get_db
from ai_ticket_platform.core.settings import Settings
from ai_ticket_platform.services.labeling.company_doc_processing import process_and_index_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents")


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_company_documents(
	files: List[UploadFile] = File(...),
	settings: Annotated[Settings, Depends(get_app_settings)] = None,
	db: Annotated[AsyncSession, Depends(get_db)] = None,
):
	"""
	Upload company PDF documents: automatically label + save + index to Azure AI Search.
	"""
	llm_client = get_llm_client(settings)

	# Process files sequentially to avoid concurrent use of a single AsyncSession
	results = []

	for file in files:
		# Validate PDF file type
		if not file.filename.lower().endswith(".pdf"):
			logger.warning(f"Rejected non-PDF file: {file.filename}")
			results.append({
				"filename": file.filename,
				"success": False,
				"error": "Only PDF files are accepted",
				"indexed": False
			})
			continue

		content = await file.read()

		# Process and index document 
		result = await process_and_index_document(
			filename=file.filename,
			content=content,
			llm_client=llm_client,
			db=db,
			settings=settings
		)

		results.append(result)

	# Count successes and failures
	successful_count = sum(1 for r in results if r["success"])
	failed_count = len(results) - successful_count
	indexed_count = sum(1 for r in results if r.get("indexed", False))

	return {
		"total_processed": len(files),
		"successful": successful_count,
		"failed": failed_count,
		"indexed": indexed_count,
		"results": results
	}

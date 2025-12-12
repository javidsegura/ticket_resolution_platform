from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from ai_ticket_platform.dependencies import get_db
from ai_ticket_platform.database.CRUD.intents import get_intent, list_intents
from ai_ticket_platform.database.CRUD.article import get_latest_articles_for_intent
from ai_ticket_platform.schemas.endpoints.intent import IntentRead
from ai_ticket_platform.schemas.endpoints.article import LatestArticlesResponse
from ai_ticket_platform.services.infra.storage.storage import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(
	prefix="/intents",
	tags=["intents"],
)


@router.get("/", response_model=list[IntentRead])
async def get_intents(
	skip: int = Query(0, ge=0),
	limit: int = Query(100, ge=1, le=500),
	is_processed: bool | None = None,
	db: AsyncSession = Depends(get_db),
):
	"""
	Return a paginated list of intents, optionally filtered by processing status.
	"""
	intents = await list_intents(
		db,
		skip=skip,
		limit=limit,
		is_processed=is_processed,
	)
	return [IntentRead.model_validate(intent) for intent in intents]


@router.get("/{intent_id}", response_model=IntentRead)
async def get_intent_by_id(intent_id: int, db: AsyncSession = Depends(get_db)):
	"""
	Retrieve a single intent by ID.
	"""
	intent = await get_intent(db, intent_id)
	if not intent:
		raise HTTPException(status_code=404, detail="Intent not found")

	return IntentRead.model_validate(intent)


@router.get("/{intent_id}/articles/latest", response_model=LatestArticlesResponse)
async def get_latest_articles_by_intent(
	intent_id: int, db: AsyncSession = Depends(get_db)
):
	"""
	Get the latest version of articles for a specific intent/cluster.

	Returns:
	- version: Latest version number
	- status: Article status (accepted, iteration, denied)
	- presigned_url_micro: Temporary URL to download micro article content from S3 (valid 1 hour)
	- presigned_url_full: Temporary URL to download full article content from S3 (valid 1 hour)

	If no articles exist for this intent, all fields will be null.
	"""
	# Verify intent exists
	intent = await get_intent(db, intent_id)
	if not intent:
		raise HTTPException(status_code=404, detail="Intent not found")

	# Get latest articles
	articles = await get_latest_articles_for_intent(db, intent_id)

	# Extract version, status, and IDs from articles (both should have same version/status)
	version = None
	status = None
	article_id_micro = None
	article_id_full = None
	
	if articles["micro"]:
		version = articles["micro"].version
		status = articles["micro"].status
		article_id_micro = articles["micro"].id
	elif articles["article"]:
		version = articles["article"].version
		status = articles["article"].status
	
	if articles["article"]:
		article_id_full = articles["article"].id

	# Generate presigned URLs for article content
	storage = get_storage_service()
	presigned_url_micro = None
	presigned_url_full = None

	if articles["micro"]:
		try:
			presigned_url_micro = storage.get_presigned_url(
				articles["micro"].blob_path, expiration_time_secs=3600
			)
		except Exception as e:
			# Log error
			logger.error(
				f"Failed to generate presigned URL for micro article: {e}",
				exc_info=True,
			)

	if articles["article"]:
		try:
			presigned_url_full = storage.get_presigned_url(
				articles["article"].blob_path, expiration_time_secs=3600
			)
		except Exception as e:
			# Log error
			logger.error(
				f"Failed to generate presigned URL for full article: {e}", exc_info=True
			)

	return LatestArticlesResponse(
		intent_id=intent_id,
		version=version,
		status=status,
		article_id_micro=article_id_micro,
		article_id_full=article_id_full,
		presigned_url_micro=presigned_url_micro,
		presigned_url_full=presigned_url_full,
	)

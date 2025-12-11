from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.dependencies import get_db
from pydantic import BaseModel
from ai_ticket_platform.database.CRUD.intents import (
	increment_variant_impressions,
	increment_variant_resolutions,
	get_intent,
	get_ab_testing_totals,
)
from ai_ticket_platform.services.micro_answer_service import get_micro_answer_html

router = APIRouter(
	prefix="/external",
	tags=["external"],
)


class CollectEvent(BaseModel):
	type: str
	intent_id: int
	variant: str  # "A" or "B"


logger = logging.getLogger(__name__)


@router.get("/")
async def get_external():
	return {"message": "External API"}


@router.post("/collect")
async def collect_event(event: CollectEvent, db: AsyncSession = Depends(get_db)):
	if event.variant not in ("A", "B"):
		raise HTTPException(status_code=400, detail="Invalid variant")

	match event.type:
		case "impression":
			await increment_variant_impressions(db, event.intent_id, event.variant)

		case "resolution":
			await increment_variant_resolutions(db, event.intent_id, event.variant)

		case "ticket_created":
			# Nothing for now
			logger.info(
				f"Ticket created for intent {event.intent_id}, variant {event.variant}"
			)

		case _:
			raise HTTPException(status_code=400, detail="Unknown event type")

	return {"success": True}


# Gets the SUM of totals for all intents
@router.get("/analytics/totals")
async def get_analytics_totals(db: AsyncSession = Depends(get_db)):
	totals = await get_ab_testing_totals(db)
	return totals


# Gets the totals for a specific intent
@router.get("/analytics/{intent_id}")
async def get_analytics(intent_id: int, db: AsyncSession = Depends(get_db)):
	intent = await get_intent(db, intent_id)
	if not intent:
		raise HTTPException(status_code=404, detail="Intent not found")

	return {
		"variant_a_impressions": intent.variant_a_impressions,
		"variant_b_impressions": intent.variant_b_impressions,
		"variant_a_resolutions": intent.variant_a_resolutions,
		"variant_b_resolutions": intent.variant_b_resolutions,
	}


@router.get("/microanswer", response_class=HTMLResponse)
async def get_microanswer(
	intent_id: int = Query(..., description="Intent ID to fetch the markdown article for"),
	container_path: str | None = Query(None, description="Optional container path. If not provided, will be constructed from intent_id"),
):
	"""
	Get markdown content from cloud storage and convert it to HTML.

	Returns the HTML body content (not a full HTML document).

	Args:
		intent_id: The intent ID to fetch content for
		container_path: Optional container path. If not provided, will mock a path based on intent_id

	Returns:
		HTMLResponse containing the converted HTML body
	"""
	try:
		# If container_path is not provided, construct a mock path from intent_id
		if not container_path:
			container_path = f"articles/article-{intent_id}.md"

		html_content = await get_micro_answer_html(container_path)
		logger.info(f"Successfully retrieved and converted markdown to HTML for intent {intent_id}")

		return HTMLResponse(content=html_content)

	except Exception as e:
		logger.error(f"Error retrieving micro answer for intent {intent_id}: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Error retrieving micro answer: {str(e)}")



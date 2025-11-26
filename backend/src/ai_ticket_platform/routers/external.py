from fastapi import APIRouter, HTTPException, Depends
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.dependencies import get_db
from pydantic import BaseModel
from ai_ticket_platform.database.CRUD.intents import increment_variant_impressions, increment_variant_resolutions, get_intent

router = APIRouter(
    prefix="/external",
    tags=["external"],
)

class CollectEvent(BaseModel):
    type: str
    intent_id: int
    variant: str   # "A" or "B"

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
            logger.info(f"Ticket created for intent {event.intent_id}, variant {event.variant}")

        case _:
            raise HTTPException(status_code=400, detail="Unknown event type")
    
    return {"success": True}


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
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.dependencies import get_db
from ai_ticket_platform.database.CRUD.intents import get_intent, list_intents
from ai_ticket_platform.schemas.endpoints.intent import IntentRead

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


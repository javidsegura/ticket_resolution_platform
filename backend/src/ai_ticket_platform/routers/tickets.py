from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.dependencies.database import get_db
from ai_ticket_platform.services.csv_uploader.orchestrator import upload_csv_file
from ai_ticket_platform.schemas.endpoints.ticket import CSVUploadResponse

router = APIRouter(tags=["tickets"])


@router.post("/upload-csv", response_model=CSVUploadResponse)
async def upload_tickets_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a CSV file with tickets.
    
    Expected CSV columns: id, created_at, subject, body, product_area
    """
    
    try:
        result = await upload_csv_file(file, db)
        return CSVUploadResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")
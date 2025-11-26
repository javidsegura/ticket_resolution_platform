from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.dependencies.database import get_db
from ai_ticket_platform.services.csv_uploader.csv_orchestrator import upload_csv_file
from ai_ticket_platform.schemas.endpoints.ticket import CSVUploadResponse

router = APIRouter(tags=["tickets"])


@router.post("/upload-csv", response_model=CSVUploadResponse)
async def upload_tickets_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Upload a CSV file with tickets.
    
    Expected CSV columns: id, created_at, subject, body
    """
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
    # Validate content type
    if file.content_type not in ['text/csv', 'application/csv']:
        raise HTTPException(status_code=400, detail="Invalid content type. Expected text/csv")
        
    # Validate file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    size_read = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    while chunk := await file.read(chunk_size):
        size_read += len(chunk)
        if size_read > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    await file.seek(0)  # Reset file pointer
    
    try:
        result = await upload_csv_file(file, db)
        return CSVUploadResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")

# ADD HERE FAKE CSV INGESTION, THEN CALL QUEUE SERVICE TO ADD STUFF
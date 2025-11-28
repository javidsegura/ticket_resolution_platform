from ai_ticket_platform.dependencies.queue import get_queue
from ai_ticket_platform.services.queue_manager.tasks import batch_finalizer, process_ticket_stage1
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ai_ticket_platform.dependencies import get_db
from ai_ticket_platform.services.csv_uploader.csv_orchestrator import upload_csv_file
from ai_ticket_platform.schemas.endpoints.ticket import (
    CSVUploadResponse,
    TicketListResponse,
    TicketResponse,
)
from ai_ticket_platform.database.CRUD.ticket import (
    get_ticket as crud_get_ticket,
    list_tickets as crud_list_tickets,
    count_tickets as crud_count_tickets,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])
logger = logging.getLogger(__name__)

from ai_ticket_platform.core.clients.redis import initialize_redis_client
from rq import Queue
from rq.job import Job, Retry



@router.get("/", response_model=TicketListResponse)
async def get_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Return a paginated list of tickets.
    """
    tickets = await crud_list_tickets(db, skip=skip, limit=limit)
    total_count = await crud_count_tickets(db)
    ticket_models = [TicketResponse.model_validate(ticket) for ticket in tickets]
    return TicketListResponse(
        total=total_count,
        skip=skip,
        limit=limit,
        tickets=ticket_models,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket_by_id(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a single ticket by ID.
    """
    ticket = await crud_get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketResponse.model_validate(ticket)


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
@router.post("/upload-csv-with-pub-sub-model")
async def process_tickets_endpoint(queue: Queue = Depends(get_queue)):
    """Process mock tickets in two stages (no CSV needed for demo)"""
    
    logger.info("[PUB/SUB] Starting ticket processing pipeline")
    
    # Mock ticket data
    mock_tickets = [
        {
            "id": "TICKET-001",
            "description": "Bug in login form - users cannot authenticate",
            "category": "technical",
            "priority": "high"
        },
        {
            "id": "TICKET-002",
            "description": "Add dark mode feature to the dashboard",
            "category": "enhancement",
            "priority": "medium"
        },
        {
            "id": "TICKET-003",
            "description": "Question about billing cycle",
            "category": "support",
            "priority": "low"
        },
        {
            "id": "TICKET-004",
            "description": "Error 500 when uploading large files",
            "category": "technical",
            "priority": "critical"
        },
        {
            "id": "TICKET-005",
            "description": "Feature request: export data to Excel",
            "category": "enhancement",
            "priority": "medium"
        }
    ]
    
    try:
        # Stage 1: Enqueue all tickets
        stage1_jobs = []
        for ticket in mock_tickets:
            job = queue.enqueue(
                process_ticket_stage1,
                ticket,
                retry=Retry(max=3, interval=[10, 30, 60]),
                job_timeout='5m'
            )
            stage1_jobs.append(job.id)
            logger.info(f"[PUB/SUB] Enqueued stage1 job {job.id} for ticket {ticket['id']}")
        
        logger.info(f"[PUB/SUB] Stage 1 complete: {len(stage1_jobs)} jobs enqueued")
        
        # Finalizer: waits for stage1, then triggers stage2
        finalizer_job = queue.enqueue(
            batch_finalizer,
            stage1_jobs,
            job_timeout='30m'
        )
        logger.info(f"[PUB/SUB] Enqueued batch_finalizer job {finalizer_job.id} to process {len(stage1_jobs)} stage1 jobs")
        
        logger.info("[PUB/SUB] Pipeline initialized successfully")
        
        return {
            "message": f"Processing {len(mock_tickets)} tickets",
            "total": len(mock_tickets),
            "tickets": [t["id"] for t in mock_tickets]
        }
        
    except Exception as e:
        logger.error(f"[PUB/SUB] Pipeline initialization failed: {str(e)}")
        raise HTTPException(500, str(e))



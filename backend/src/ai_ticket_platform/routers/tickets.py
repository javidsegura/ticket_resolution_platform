from ai_ticket_platform.dependencies.queue import get_queue
from ai_ticket_platform.services.queue_manager.tasks import (
	process_ticket_stage1,
	batch_finalizer,
)
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import tempfile
import os

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
from rq import Queue
from rq.job import Retry

router = APIRouter(prefix="/tickets", tags=["tickets"])
logger = logging.getLogger(__name__)



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

@router.post("/upload-csv-with-queue")
async def upload_csv_with_queue(
	file: UploadFile = File(...),
	queue: Queue = Depends(get_queue)
):
	"""
	Upload CSV file and process through 3-stage queue workflow:
	Stage 1: Parse CSV and save tickets to DB
	Finalizer: Cluster tickets in batches of 20, create intents
	Stage 2+3: Create intents then Generate article content using RAG
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

	tmp_path = None

	try:
		logger.info(f"[CSV QUEUE] Processing CSV upload: {file.filename}")

		# Save uploaded file temporarily
		with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
			while chunk := await file.read(1024 * 1024):  # 1MB chunks
				tmp.write(chunk)
			tmp_path = tmp.name

		logger.info(f"[CSV QUEUE] Saved temp file to: {tmp_path}")

		# Stage 1: Enqueue CSV parsing and ticket saving
		stage1_job = queue.enqueue(
			process_ticket_stage1,
			tmp_path,
			retry=Retry(max=3, interval=[10, 30, 60]),
			job_timeout='10m'
		)
		logger.info(f"[CSV QUEUE] Enqueued stage1 job {stage1_job.id}")

		# Batch Finalizer: Waits for stage1, clusters in batches of 20, enqueues stage2+3
		finalizer_job = queue.enqueue(
			batch_finalizer,
			[stage1_job.id],  # List of stage1 job IDs to wait for
			20,  # batch_size for clustering
			job_timeout='30m'
		)
		logger.info(f"[CSV QUEUE] Enqueued batch_finalizer job {finalizer_job.id}")

		return {
			"message": f"CSV upload queued for processing: {file.filename}",
			"filename": file.filename,
			"jobs": {
				"stage1_job_id": stage1_job.id,
				"finalizer_job_id": finalizer_job.id
			},
			"workflow": "Stage1: Parse CSV then Finalizer: Cluster (20/batch) then Stage2: Create Intents then Stage3: Generate Articles"
		}

	except Exception as e:
		logger.error(f"[CSV QUEUE] Pipeline initialization failed: {str(e)}")
		# Clean up temp file on error
		if tmp_path and os.path.exists(tmp_path):
			try:
				os.unlink(tmp_path)
			except Exception:
				pass
		raise HTTPException(500, str(e))



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


@router.post("/upload-csv-with-queue")
async def upload_csv_with_queue(
	file: UploadFile = File(...),
	queue: Queue = Depends(get_queue),
	batch_size: int = Query(10, ge=1, le=50, description="Number of tickets to process per batch job")
):
	"""
	Upload CSV file and process through queue workflow with TRUE batching:
	1. Parse CSV synchronously
	2. Enqueue Stage 1 jobs (one per BATCH of tickets): Filter validation + create in DB + cluster/assign intent
	3. Enqueue Batch Finalizer: Wait for all Stage 1 jobs, group by unique intent
	4. Finalizer enqueues Stage 2 jobs (one per unique intent): Generate article content using RAG

	Args:
		file: CSV file with ticket data
		batch_size: Number of tickets per batch job (default: 10, max: 50)
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
		logger.info(f"[CSV QUEUE] Processing CSV upload: {file.filename} with batch_size={batch_size}")

		# Save uploaded file temporarily
		with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
			while chunk := await file.read(1024 * 1024):  # 1MB chunks
				tmp.write(chunk)
			tmp_path = tmp.name

		logger.info(f"[CSV QUEUE] Saved temp file to: {tmp_path}")

		# Parse CSV file to extract tickets
		from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file
		parse_result = parse_csv_file(tmp_path)

		if not parse_result.get("success"):
			raise ValueError(f"CSV parsing failed: {parse_result}")

		tickets = parse_result.get("tickets", [])
		logger.info(f"[CSV QUEUE] Parsed {len(tickets)} tickets from CSV")

		# Stage 1: Enqueue one job per BATCH of tickets (filter + cluster)
		stage1_job_ids = []
		ticket_batches = [tickets[i:i + batch_size] for i in range(0, len(tickets), batch_size)]

		logger.info(f"[CSV QUEUE] Created {len(ticket_batches)} batches of tickets (batch_size={batch_size})")

		for batch_idx, ticket_batch in enumerate(ticket_batches):
			stage1_job = queue.enqueue(
				process_ticket_stage1,
				ticket_batch,  # Pass entire batch
				retry=Retry(max=3, interval=[10, 30, 60]),
				job_timeout='10m'  # Increased timeout for batch processing
			)
			stage1_job_ids.append(stage1_job.id)
			logger.info(f"[CSV QUEUE] Enqueued batch {batch_idx + 1}/{len(ticket_batches)} with {len(ticket_batch)} tickets (job_id: {stage1_job.id})")

		logger.info(f"[CSV QUEUE] Enqueued {len(stage1_job_ids)} stage1 batch jobs for {len(tickets)} tickets")

		# Batch Finalizer: Waits for all stage1 jobs, groups by cluster, enqueues stage2
		finalizer_job = queue.enqueue(
			batch_finalizer,
			stage1_job_ids,
			job_timeout='30m'
		)
		logger.info(f"[CSV QUEUE] Enqueued batch_finalizer job {finalizer_job.id}")

		# Clean up temp file
		if tmp_path and os.path.exists(tmp_path):
			try:
				os.unlink(tmp_path)
			except Exception as e:
				logger.warning(f"Failed to delete temp file {tmp_path}: {e}")

		return {
			"message": f"CSV upload queued for processing: {file.filename}",
			"filename": file.filename,
			"tickets_count": len(tickets),
			"jobs": {
				"batch_size": batch_size,
				"batch_count": len(ticket_batches),
				"stage1_job_count": len(stage1_job_ids),
				"finalizer_job_id": finalizer_job.id
			},
			"workflow": f"Stage1: Filter+Cluster {batch_size} tickets per batch -> Finalizer: Group by intent -> Stage2: Generate article per intent"
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

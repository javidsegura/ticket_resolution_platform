from datetime import timedelta
import asyncio
import logging
from typing import Dict, Any, List

from ai_ticket_platform.core.clients.redis import initialize_redis_client
from ai_ticket_platform.core.settings.app_settings import initialize_settings
from ai_ticket_platform.database.main import initialize_db_engine
from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file
from ai_ticket_platform.database.CRUD.ticket import create_tickets
from ai_ticket_platform.services.clustering.cluster_service import cluster_tickets
from ai_ticket_platform.core.clients import llm_client
from ai_ticket_platform.services.content_generation.rag_queue_interface import generate_article_task
from rq import Queue, Retry, get_current_job
from rq.job import Job

logger = logging.getLogger(__name__)


# Lazy initialization - only initialize when actually needed
redis_client_connector = None
sync_redis_connection = None
queue = None


def _get_queue():
	"""Get or initialize the RQ queue."""
	global redis_client_connector, sync_redis_connection, queue
	if queue is None:
		redis_client_connector = initialize_redis_client()
		sync_redis_connection = redis_client_connector.get_sync_connection()
		queue = Queue("default", connection=sync_redis_connection)
	return queue


def _run_async(coro):
	"""Helper to run async functions in sync RQ context."""
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	try:
		return loop.run_until_complete(coro)
	finally:
		loop.close()



def process_ticket_stage1(csv_file_path: str) -> Dict[str, Any]:
	"""Stage 1: Parse CSV and save tickets to database"""
	logger.info(f"[STAGE1] Parsing CSV file: {csv_file_path}")

	try:
		# Parse CSV file
		csv_result = parse_csv_file(csv_file_path)
		logger.info(f"[STAGE1] Parsed CSV: {csv_result['file_info']['tickets_extracted']} tickets extracted")

		# Save tickets to database
		async def save_tickets():
			AsyncSessionLocal = initialize_db_engine()
			async with AsyncSessionLocal() as db:
				created_tickets = await create_tickets(db, csv_result["tickets"])
				return created_tickets

		created_tickets = _run_async(save_tickets())
		logger.info(f"[STAGE1] Saved {len(created_tickets)} tickets to database")

		# Return ticket data for clustering
		return {
			"tickets_created": len(created_tickets),
			"tickets": [
				{
					"id": ticket.id,
					"subject": ticket.subject,
					"body": ticket.body
				}
				for ticket in created_tickets
			],
			"file_info": csv_result["file_info"]
		}

	except ValueError as e:
		logger.error(f"[STAGE1] Validation error: {str(e)}")
		return {"error": str(e)}
	except Exception as e:
		logger.error(f"[STAGE1] Unexpected error, will retry: {str(e)}")
		raise  # Will be automatically requeued 


def process_ticket_stage2(ticket_ids: List[int], batch_size: int = 20) -> Dict[str, Any]:
	"""Stage 2: Cluster all tickets and enqueue Stage 3 for each new intent"""
	logger.info(f"[STAGE2] Starting clustering for {len(ticket_ids)} tickets")

	try:
		# Run clustering using cluster_tickets service
		async def run_clustering():
			from ai_ticket_platform.database.CRUD.ticket import get_ticket

			AsyncSessionLocal = initialize_db_engine()
			async with AsyncSessionLocal() as db:
				# Fetch actual Ticket objects from DB
				ticket_objects = []
				for ticket_id in ticket_ids:
					ticket_obj = await get_ticket(db, ticket_id)
					if ticket_obj:
						ticket_objects.append(ticket_obj)

				logger.info(f"[STAGE2] Fetched {len(ticket_objects)} ticket objects from DB")

				# Run clustering with batch_size
				result = await cluster_tickets(db, llm_client, ticket_objects, batch_size=batch_size)
				return result

		clustering_result = _run_async(run_clustering())
		logger.info(f"[STAGE2] Clustering complete: {clustering_result.get('total_intents', 0)} intents created/matched")

		# Extract intent assignments
		assignments = clustering_result.get("assignments", [])

		if not assignments:
			logger.warning("[STAGE2] No intent assignments from clustering")
			return {
				"status": "completed",
				"tickets_clustered": len(ticket_ids),
				"intents_created": 0,
				"stage3_enqueued": 0
			}

		# Group assignments by intent_id to enqueue stage3 once per new intent
		intent_groups = {}
		for assignment in assignments:
			intent_id = assignment.get("intent_id")
			if intent_id and assignment.get("is_new_intent"):
				# Only enqueue for newly created intents
				if intent_id not in intent_groups:
					intent_groups[intent_id] = {
						"intent_id": intent_id,
						"intent_name": assignment.get("intent_name", "Unknown"),
						"category_l1_name": assignment.get("category_l1_name", "General"),
						"category_l2_name": assignment.get("category_l2_name", "General"),
						"category_l3_name": assignment.get("category_l3_name", "General"),
						"ticket_ids": []
					}
				intent_groups[intent_id]["ticket_ids"].append(assignment.get("ticket_id"))

		# Enqueue stage3 ONCE per newly created intent
		logger.info(f"[STAGE2] Enqueueing stage3 jobs for {len(intent_groups)} new intents")
		stage3_jobs = []
		for intent_id, intent_data in intent_groups.items():
			cluster_data = {
				"intent_id": intent_id,
				"cluster_name": intent_data["intent_name"],
				"category": intent_data["category_l1_name"],
				"subcategory": intent_data["category_l2_name"],
				"ticket_count": len(intent_data["ticket_ids"]),
				"summary": f"Intent for {len(intent_data['ticket_ids'])} tickets"
			}

			job = _get_queue().enqueue(
				process_ticket_stage3,
				intent_id,
				cluster_data,
				retry=Retry(max=3, interval=[10, 30, 60]),
				job_timeout="15m"
			)
			stage3_jobs.append(job.id)
			logger.info(f"[STAGE2] Enqueued stage3 job {job.id} for intent {intent_id}: {intent_data['intent_name']}")

		logger.info(f"[STAGE2] Complete: {len(stage3_jobs)} stage3 jobs enqueued")

		return {
			"status": "completed",
			"tickets_clustered": len(ticket_ids),
			"intents_created": clustering_result.get("intents_created", 0),
			"intents_matched": clustering_result.get("intents_matched", 0),
			"stage3_enqueued": len(stage3_jobs),
			"stage3_job_ids": stage3_jobs
		}

	except Exception as e:
		logger.error(f"[STAGE2] Error during clustering: {str(e)}")
		raise  # Will be automatically requeued


def process_ticket_stage3(intent_id: int, cluster_data: Dict[str, Any]) -> Dict[str, Any]:
	"""Stage 3: Generate article content using RAG"""
	logger.info(f"[STAGE3] Generating article for intent {intent_id}")

	try:
		# Call the content generation task (which uses RAG workflow)
		result = generate_article_task(intent_id=intent_id)

		logger.info(f"[STAGE3] Article generation for intent {intent_id}: {result.get('status')}")

		return {
			"intent_id": intent_id,
			"cluster_name": cluster_data.get("cluster_name", "Unknown"),
			"article_id": result.get("article_id"),
			"generation_result": result,
			"status": "article_generated"
		}

	except Exception as e:
		logger.error(f"[STAGE3] Error generating article for intent {intent_id}: {str(e)}")
		raise  # Will be automatically requeued 


def batch_finalizer(stage1_job_ids: List[str], batch_size: int = 20) -> Dict[str, Any]:
	"""Wait for all stage1 jobs to finish, then enqueue a single stage2 job for clustering"""
	logger.info(f"[FINALIZER] Starting - checking {len(stage1_job_ids)} stage1 jobs")

	# Fetch all jobs once
	jobs = [Job.fetch(job_id, connection=sync_redis_connection) for job_id in stage1_job_ids]

	# Separate finished/failed jobs from pending ones
	pending_jobs = [j for j in jobs if not j.is_finished and not j.is_failed]
	finished_jobs = [j for j in jobs if j.is_finished and not j.is_failed]

	if pending_jobs:
		# Not all jobs are done, re-enqueue self to run in 30 seconds
		current_job = get_current_job()
		if current_job:
			_get_queue().enqueue_in(timedelta(seconds=30), batch_finalizer, stage1_job_ids, batch_size, job_id=current_job.id)
			logger.info(f"[FINALIZER] Re-enqueued finalizer job {current_job.id}, {len(finished_jobs)}/{len(stage1_job_ids)} jobs complete. {len(pending_jobs)} pending.")
			return {
				"message": f"Re-enqueued finalizer, {len(finished_jobs)}/{len(stage1_job_ids)} jobs complete.",
				"status": "pending",
				"finished_count": len(finished_jobs),
				"total_count": len(stage1_job_ids)
			}
		else:
			logger.error("[FINALIZER] Could not get current job context to re-enqueue.")
			return {"message": "Error: Could not re-enqueue finalizer.", "status": "failed"}

	# All stage1 jobs are finished
	logger.info(f"[FINALIZER] All stage1 jobs complete: {len(finished_jobs)}/{len(stage1_job_ids)} processed")

	# Collect all ticket IDs from finished jobs
	all_ticket_ids = []
	for job in finished_jobs:
		if job.result and "tickets" in job.result and "error" not in job.result:
			# Extract ticket IDs from stage1 results
			all_ticket_ids.extend([ticket["id"] for ticket in job.result["tickets"]])

	if not all_ticket_ids:
		logger.warning("[FINALIZER] No tickets to cluster")
		return {"status": "completed", "tickets_processed": 0, "stage2_enqueued": 0}

	logger.info(f"[FINALIZER] Enqueueing stage2 job for clustering {len(all_ticket_ids)} tickets")

	# Enqueue a single stage2 job that will handle all clustering
	stage2_job = _get_queue().enqueue(
		process_ticket_stage2,
		all_ticket_ids,
		batch_size,
		retry=Retry(max=3, interval=[10, 30, 60]),
		job_timeout="30m"  # Give enough time for clustering all tickets
	)

	logger.info(f"[FINALIZER] Complete: Enqueued stage2 job {stage2_job.id} for {len(all_ticket_ids)} tickets")

	return {
		"status": "completed",
		"stage1_jobs_processed": len(finished_jobs),
		"tickets_collected": len(all_ticket_ids),
		"stage2_job_id": stage2_job.id,
		"stage2_enqueued": 1
	}
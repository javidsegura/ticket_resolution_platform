from datetime import timedelta
import asyncio
import logging
from typing import Dict, Any, List

from ai_ticket_platform.core.clients.redis import initialize_redis_client
from ai_ticket_platform.core.settings.app_settings import initialize_settings
from ai_ticket_platform.database.main import initialize_db_engine
from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file
from ai_ticket_platform.database.CRUD.ticket import create_tickets
from ai_ticket_platform.services.clustering.cluster_service import cluster_and_categorize_tickets
from ai_ticket_platform.core.clients import llm_client
from ai_ticket_platform.services.content_generation.rag_queue_interface import generate_article_task
from rq import Queue, Retry, get_current_job
from rq.job import Job

logger = logging.getLogger(__name__)


redis_client_connector = initialize_redis_client()
sync_redis_connection = redis_client_connector.get_sync_connection()
queue = Queue("default", connection=sync_redis_connection)


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


def process_ticket_stage2(cluster_data: Dict[str, Any]) -> Dict[str, Any]:
	"""Stage 2: Create intent and enqueue content generation"""
	cluster_name = cluster_data.get("cluster_name", "Unknown")
	logger.info(f"[STAGE2] Creating intent for cluster: {cluster_name}")

	try:
		# Create Intent record in database
		async def create_intent_record():
			from ai_ticket_platform.database.CRUD.intents import create_intent

			AsyncSessionLocal = initialize_db_engine()
			async with AsyncSessionLocal() as db:
				intent = await create_intent(
					db,
					name=cluster_data.get("cluster_name", "Untitled Intent"),
					area=cluster_data.get("category", "General"),
					description=cluster_data.get("summary", ""),
					is_processed=False
				)
				return intent

		intent = _run_async(create_intent_record())
		logger.info(f"[STAGE2] Created intent {intent.id} for cluster: {cluster_name}")

		# Enqueue Stage 3: Article generation for this intent
		job = queue.enqueue(
			process_ticket_stage3,
			intent.id,
			cluster_data,
			retry=Retry(max=3, interval=[10, 30, 60]),
			job_timeout="15m"
		)
		logger.info(f"[STAGE2] Enqueued stage3 job {job.id} for intent {intent.id}")

		return {
			"cluster_name": cluster_name,
			"intent_id": intent.id,
			"stage3_job_id": job.id,
			"status": "intent_created"
		}

	except Exception as e:
		logger.error(f"[STAGE2] Error creating intent for {cluster_name}: {str(e)}")
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
	"""Wait for stage1 jobs, then cluster tickets in batches and enqueue stage2"""
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
			queue.enqueue_in(timedelta(seconds=30), batch_finalizer, stage1_job_ids, batch_size, job_id=current_job.id)
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

	# All jobs are finished
	logger.info(f"[FINALIZER] Phase 1 complete: {len(finished_jobs)}/{len(stage1_job_ids)} jobs processed")

	# Collect all tickets from finished jobs
	all_tickets = []
	for job in finished_jobs:
		if job.result and "tickets" in job.result and "error" not in job.result:
			all_tickets.extend(job.result["tickets"])

	if not all_tickets:
		logger.warning("[FINALIZER] No tickets to cluster")
		return {"status": "completed", "tickets_clustered": 0, "stage2_enqueued": 0}

	logger.info(f"[FINALIZER] Phase 2: Clustering {len(all_tickets)} tickets in batches of {batch_size}")

	# Split into batches
	batches = [all_tickets[i:i + batch_size] for i in range(0, len(all_tickets), batch_size)]
	logger.info(f"[FINALIZER] Split into {len(batches)} batches")

	# Cluster each batch and collect results
	all_clusters = []
	for batch_idx, batch in enumerate(batches):
		logger.info(f"[FINALIZER] Clustering batch {batch_idx + 1}/{len(batches)} ({len(batch)} tickets)")

		async def cluster_batch():
			return await cluster_and_categorize_tickets(batch, llm_client)

		batch_result = _run_async(cluster_batch())
		clusters = batch_result.get("clusters", [])
		all_clusters.extend(clusters)
		logger.info(f"[FINALIZER] Batch {batch_idx + 1} clustered: {len(clusters)} clusters created")

	logger.info(f"[FINALIZER] Phase 2 complete: {len(all_clusters)} total clusters created")

	# Enqueue stage2 ONCE per cluster for content generation
	logger.info("[FINALIZER] Phase 3: Enqueueing stage2 jobs (one per cluster)")
	stage2_jobs = []
	for cluster_idx, cluster in enumerate(all_clusters):
		# Each cluster becomes an "intent" that needs content generated
		cluster_data = {
			"cluster_index": cluster_idx,
			"cluster_name": cluster.get("topic_name", "Unknown"),
			"category": cluster.get("product_category", "Unknown"),
			"subcategory": cluster.get("product_subcategory", "Unknown"),
			"ticket_count": cluster.get("ticket_count", 0),
			"tickets": cluster.get("example_tickets", []),
			"summary": cluster.get("summary", "")
		}

		job = queue.enqueue(
			process_ticket_stage2,
			cluster_data,
			retry=Retry(max=3, interval=[10, 30, 60]),
			job_timeout="10m"
		)
		stage2_jobs.append(job.id)
		logger.info(f"[FINALIZER] Enqueued stage2 job {job.id} for cluster: {cluster_data['cluster_name']}")

	logger.info(f"[FINALIZER] Complete: {len(stage2_jobs)} stage2 jobs enqueued")

	return {
		"stage1_processed": len(finished_jobs),
		"tickets_clustered": len(all_tickets),
		"clusters_created": len(all_clusters),
		"stage2_enqueued": len(stage2_jobs),
		"status": "completed"
	}
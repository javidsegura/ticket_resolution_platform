from datetime import timedelta
import logging
from typing import Dict, Any, List

from ai_ticket_platform.core.clients.redis import initialize_redis_client
from ai_ticket_platform.core.settings.app_settings import initialize_settings
from ai_ticket_platform.database.main import initialize_db_engine
from ai_ticket_platform.services.queue_manager.service_adapters import (
	save_tickets,
	cluster_ticket,
	generate_content
)
from rq import Queue, Retry, get_current_job
from rq.job import Job
from ai_ticket_platform.database.CRUD.intent import get_intents_processing_status
from ai_ticket_platform.services.queue_manager.async_helper import _run_async


logger = logging.getLogger(__name__)


redis_client_connector = initialize_redis_client()
sync_redis_connection = redis_client_connector.get_sync_connection()
queue = Queue("default", connection=sync_redis_connection)

def process_ticket_stage1(ticket_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	"""Stage 1: Filter and cluster a BATCH of tickets.
	"""
	logger.info(f"[STAGE1] Processing batch of {len(ticket_batch)} tickets")

	results = []

	try:
		# Step 1: Filter all tickets in the batch (creates them in DB)
		logger.info(f"[STAGE1] Filtering {len(ticket_batch)} tickets")
		filtered_tickets = []
		for ticket_data in ticket_batch:
			try:
				filtered = save_tickets(ticket_data)
				filtered_tickets.append(filtered)
			except ValueError as e:
				# Validation error - skip this ticket but continue with others
				ticket_id = ticket_data.get("id", "unknown")
				logger.error(f"[STAGE1] Validation error for ticket {ticket_id}: {str(e)}")
				results.append({"ticket_id": ticket_id, "error": str(e)})

		if not filtered_tickets:
			logger.warning(f"[STAGE1] No valid tickets to cluster in this batch")
			return results

		logger.info(f"[STAGE1] Successfully filtered {len(filtered_tickets)} tickets")

		# Step 2: Cluster all valid tickets as a batch
		logger.info(f"[STAGE1] Clustering batch of {len(filtered_tickets)} tickets")
		clustered_tickets = cluster_ticket(filtered_tickets)

		# Step 3: Collect successful results
		for clustered in clustered_tickets:
			ticket_id = clustered.get("id")
			cluster = clustered.get("cluster")
			logger.info(f"[STAGE1] Ticket {ticket_id} -> cluster: {cluster}")
			results.append({"ticket_id": ticket_id, "data": clustered})

		logger.info(f"[STAGE1] Batch complete: {len(results)} tickets processed")
		return results

	except Exception as e:
		logger.error(f"[STAGE1] Unexpected error processing batch: {str(e)}", exc_info=True)
		# Return partial results with error indicator
		results.append({"error": f"Batch processing failed: {str(e)}", "partial_results": True})
		return results

def process_ticket_stage2(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
	"""Stage 2: Generate content"""
	ticket_id = ticket_data.get("id")
	cluster = ticket_data.get("cluster")
	logger.info(f"[STAGE2] Processing ticket {ticket_id} from cluster {cluster}")

	try:
		logger.info(f"[STAGE2] Calling generate_content for {ticket_id}")
		result = generate_content(ticket_data)
		logger.info(f"[STAGE2] Completed {ticket_id}")
		return {"ticket_id": ticket_id, "result": result}
	except Exception:
		logger.error(f"[STAGE2] Error for {ticket_id}, will retry")
		raise  # Will be automatically requequed


def batch_finalizer(stage1_job_ids: List[str]) -> Dict[str, Any]:
	"""Batch finalizer that collects results from Stage 1 batch jobs.
	"""
	logger.info(f"[FINALIZER] Starting - checking {len(stage1_job_ids)} stage1 batch jobs")

	# Fetch all jobs once
	jobs = [Job.fetch(job_id, connection=sync_redis_connection) for job_id in stage1_job_ids]

	# Separate finished/failed jobs from pending ones
	pending_jobs = [j for j in jobs if not j.is_finished and not j.is_failed]
	finished_jobs = [j for j in jobs if j.is_finished and not j.is_failed]  # Only truly finished jobs

	if pending_jobs:
		# Not all jobs are done, re-enqueue self to run in 30 seconds
		current_job = get_current_job()
		if current_job:  # Ensure we have a job context to re-enqueue
			# Re-enqueue as a new job (don't reuse job_id or RQ will silently ignore it)
			new_job = queue.enqueue_in(timedelta(seconds=30), batch_finalizer, stage1_job_ids)
			logger.info(f"[FINALIZER] Re-enqueued finalizer as new job {new_job.id}, {len(finished_jobs)}/{len(stage1_job_ids)} batch jobs complete. {len(pending_jobs)} pending.")
			return {
				"message": f"Re-enqueued finalizer, {len(finished_jobs)}/{len(stage1_job_ids)} batch jobs complete.",
				"status": "pending",
				"finished_count": len(finished_jobs),
				"total_count": len(stage1_job_ids),
				"next_check_job_id": new_job.id
			}
		else:
			logger.error("[FINALIZER] Could not get current job context to re-enqueue. This should not happen in an RQ worker.")
			# If for some reason we can't re-enqueue, consider it a failure for this iteration
			return {"message": "Error: Could not re-enqueue finalizer.", "status": "failed"}

	# All jobs are finished (or failed, but we only collect results from finished ones)
	logger.info(f"[FINALIZER] Phase 1 complete: {len(finished_jobs)}/{len(stage1_job_ids)} batch jobs processed")

	# Flatten batch results, each job.result is a list of ticket results
	all_ticket_results = []
	for job in finished_jobs:
		if job.result is not None:
			if isinstance(job.result, list):
				# Batch job returned list of ticket results
				all_ticket_results.extend(job.result)
			else:
				# Fallback: single result (shouldn't happen with new batch logic)
				logger.warning(f"[FINALIZER] Job {job.id} returned non-list result, treating as single item")
				all_ticket_results.append(job.result)

	logger.info(f"[FINALIZER] Collected {len(all_ticket_results)} total ticket results from {len(finished_jobs)} batch jobs")

	# Group by unique clusters
	logger.info("[FINALIZER] Phase 2: Grouping results by unique clusters")
	clusters_map = {}
	errors_count = 0

	for result in all_ticket_results:
		if "error" in result:
			# Skip tickets that failed validation
			errors_count += 1
			continue

		if "data" in result:
			cluster = result["data"].get("cluster")
			if cluster:
				if cluster not in clusters_map:
					clusters_map[cluster] = result["data"]
					logger.info(f"[FINALIZER] New cluster found: {cluster}")

	logger.info(f"[FINALIZER] Phase 2 complete: {len(clusters_map)} unique clusters identified, {errors_count} errors")

	# Phase 2.5: Check which intents need article generation (is_processed=False)
	logger.info("[FINALIZER] Phase 2.5: Checking which intents need article generation")
	intent_ids = [ticket_data.get("intent_id") for ticket_data in clusters_map.values() if ticket_data.get("intent_id")]

	# Check processing status using CRUD operations

	AsyncSessionLocal = initialize_db_engine()

	async def get_status():
		async with AsyncSessionLocal() as db:
			return await get_intents_processing_status(db, intent_ids)

	intent_status = _run_async(get_status())

	# Filter clusters_map to only include intents that need processing (is_processed=False)
	clusters_needing_articles = {
		cluster: ticket_data
		for cluster, ticket_data in clusters_map.items()
		if not intent_status.get(ticket_data.get("intent_id"), False)  # False = not processed yet
	}

	already_processed_count = len(clusters_map) - len(clusters_needing_articles)
	logger.info(
		f"[FINALIZER] Phase 2.5 complete: {len(clusters_needing_articles)} intents need articles, "
		f"{already_processed_count} already have approved articles"
	)

	# Enqueue stage2 ONCE per unique cluster that needs article
	logger.info("[FINALIZER] Phase 3: Enqueueing stage2 jobs (one per cluster needing article)")
	stage2_jobs = []
	for cluster, ticket_data in clusters_needing_articles.items():
		job = queue.enqueue(process_ticket_stage2,
						   ticket_data,
						   retry=Retry(max=3, interval=[10, 30, 60]),
						   job_timeout="5m")
		stage2_jobs.append(job.id)
		logger.info(f"[FINALIZER] Enqueued stage2 job {job.id} for cluster {cluster} (intent_id: {ticket_data.get('intent_id')})")

	logger.info(f"[FINALIZER] Complete: {len(stage2_jobs)} stage2 jobs enqueued")

	return {
		"stage1_batch_jobs_processed": len(finished_jobs),
		"total_tickets_processed": len(all_ticket_results),
		"errors_count": errors_count,
		"unique_clusters": len(clusters_map),
		"clusters": list(clusters_map.keys()),
		"intents_already_processed": already_processed_count,
		"intents_needing_articles": len(clusters_needing_articles),
		"stage2_enqueued": len(stage2_jobs),
		"status": "completed"
	}

from datetime import timedelta
import time
import logging
from typing import Dict, Any, List


from ai_ticket_platform.core.clients.redis import initialize_redis_client
from ai_ticket_platform.services.queue_manager.mock_services import (
	filter_ticket,
	cluster_ticket,
	generate_content,
)
from rq import Queue, Retry, get_current_job
from redis import Redis
from rq.job import Job

logger = logging.getLogger(__name__)


redis_client_connector = initialize_redis_client()
sync_redis_connection = redis_client_connector.get_sync_connection()
queue = Queue("default", connection=sync_redis_connection)


def process_ticket_stage1(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
	"""Stage 1: Filter and cluster"""
	ticket_id = ticket_data.get("id")
	logger.info(f"[STAGE1] Processing ticket {ticket_id}")

	try:
		logger.info(f"[STAGE1] Calling filter_ticket for {ticket_id}")
		filtered = filter_ticket(ticket_data)

		logger.info(f"[STAGE1] Calling cluster_ticket for {ticket_id}")
		clustered = cluster_ticket(filtered)

		logger.info(
			f"[STAGE1] Completed {ticket_id} -> cluster: {clustered.get('cluster')}"
		)
		return {"ticket_id": ticket_id, "data": clustered}
	except ValueError as e:
		logger.error(f"[STAGE1] Validation error for {ticket_id}: {str(e)}")
		return {"ticket_id": ticket_id, "error": str(e)}
	except Exception:
		logger.error(f"[STAGE1] Unexpected error for {ticket_id}, will retry")
		raise  # Will be automatically requequed


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
	logger.info(f"[FINALIZER] Starting - checking {len(stage1_job_ids)} stage1 jobs")

	# Fetch all jobs once
	jobs = [
		Job.fetch(job_id, connection=sync_redis_connection) for job_id in stage1_job_ids
	]

	# Separate finished/failed jobs from pending ones
	pending_jobs = [j for j in jobs if not j.is_finished and not j.is_failed]
	finished_jobs = [
		j for j in jobs if j.is_finished and not j.is_failed
	]  # Only truly finished jobs

	if pending_jobs:
		# Not all jobs are done, re-enqueue self to run in 30 seconds
		current_job = get_current_job()
		if current_job:  # Ensure we have a job context to re-enqueue
			# Re-enqueue with the same job_id to ensure RQ treats this as a continuation
			queue.enqueue_in(
				timedelta(seconds=30),
				batch_finalizer,
				stage1_job_ids,
				job_id=current_job.id,
			)
			logger.info(
				f"[FINALIZER] Re-enqueued finalizer job {current_job.id}, {len(finished_jobs)}/{len(stage1_job_ids)} jobs complete. {len(pending_jobs)} pending."
			)
			return {
				"message": f"Re-enqueued finalizer, {len(finished_jobs)}/{len(stage1_job_ids)} jobs complete.",
				"status": "pending",
				"finished_count": len(finished_jobs),
				"total_count": len(stage1_job_ids),
			}
		else:
			logger.error(
				"[FINALIZER] Could not get current job context to re-enqueue. This should not happen in an RQ worker."
			)
			# If for some reason we can't re-enqueue, consider it a failure for this iteration
			return {
				"message": "Error: Could not re-enqueue finalizer.",
				"status": "failed",
			}

	# All jobs are finished (or failed, but we only collect results from finished ones)
	logger.info(
		f"[FINALIZER] Phase 1 complete: {len(finished_jobs)}/{len(stage1_job_ids)} jobs processed"
	)

	all_results = [
		j.result for j in finished_jobs if j.result is not None
	]  # Collect results from finished jobs

	# Group by unique clusters
	logger.info("[FINALIZER] Phase 2: Grouping results by unique clusters")
	clusters_map = {}
	for result in all_results:
		if "data" in result and "error" not in result:
			cluster = result["data"].get("cluster")
			if cluster:
				if cluster not in clusters_map:
					clusters_map[cluster] = result["data"]
					logger.info(f"[FINALIZER] New cluster found: {cluster}")

	logger.info(
		f"[FINALIZER] Phase 2 complete: {len(clusters_map)} unique clusters identified"
	)

	# Enqueue stage2 ONCE per unique cluster
	logger.info("[FINALIZER] Phase 3: Enqueueing stage2 jobs (one per cluster)")
	stage2_jobs = []
	for cluster, ticket_data in clusters_map.items():
		job = queue.enqueue(
			process_ticket_stage2,
			ticket_data,
			retry=Retry(max=3, interval=[10, 30, 60]),
			job_timeout="5m",
		)
		stage2_jobs.append(job.id)
		logger.info(f"[FINALIZER] Enqueued stage2 job {job.id} for cluster {cluster}")

	logger.info(f"[FINALIZER] Complete: {len(stage2_jobs)} stage2 jobs enqueued")

	return {
		"stage1_processed": len(finished_jobs),
		"unique_clusters": len(clusters_map),
		"clusters": list(clusters_map.keys()),
		"stage2_enqueued": len(stage2_jobs),
		"status": "completed",
	}

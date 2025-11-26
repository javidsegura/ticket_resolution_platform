
# WRITE HERE JOBS + FUNCTIONS USED IN JOBS (PRINT TO STDOUT WHEN YOU ARE MAKING PROGRESS)

import time
import logging
from typing import Dict, Any, List


from ai_ticket_platform.core.clients.redis import initialize_redis_client
from ai_ticket_platform.services.queue_manager.mock_services import filter_ticket, cluster_ticket, generate_content
from rq import Queue
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
        
        logger.info(f"[STAGE1] Completed {ticket_id} -> cluster: {clustered.get('cluster')}")
        return {"ticket_id": ticket_id, "data": clustered}
    except ValueError as e:
        logger.error(f"[STAGE1] Validation error for {ticket_id}: {str(e)}")
        return {"ticket_id": ticket_id, "error": str(e)}
    except Exception:
        logger.error(f"[STAGE1] Unexpected error for {ticket_id}, will retry")
        raise # Will be automatically requequed 


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
        raise # Will be automatically requequed 


# tasks.py
def batch_finalizer(stage1_job_ids: List[str]) -> Dict[str, Any]:
    """Wait for stage1, then trigger stage2 ONCE PER UNIQUE CLUSTER"""
    logger.info(f"[FINALIZER] Starting - waiting for {len(stage1_job_ids)} stage1 jobs")
    all_results = []
    
    # Wait for all stage1 jobs
    logger.info("[FINALIZER] Phase 1: Waiting for stage1 jobs to complete")
    for job_id in stage1_job_ids:
        try:
            job = Job.fetch(job_id, connection=sync_redis_connection)
            
            # Wait up to 5 minutes per job
            timeout = 300
            start = time.time()
            
            while not job.is_finished and not job.is_failed:
                if time.time() - start > timeout:
                    logger.warning(f"[FINALIZER] Timeout waiting for job {job_id}")
                    break
                time.sleep(1)
            
            if job.is_finished and job.result:
                all_results.append(job.result)
                
        except Exception as e:
            logger.warning(f"[FINALIZER] Error fetching job {job_id}: {str(e)}")
            continue
    
    logger.info(f"[FINALIZER] Phase 1 complete: {len(all_results)}/{len(stage1_job_ids)} jobs processed")
    
    # Group by unique clusters
    logger.info("[FINALIZER] Phase 2: Grouping results by unique clusters")
    clusters_map = {}
    for result in all_results:
        if "data" in result and "error" not in result:
            cluster = result["data"].get("cluster")
            if cluster:
                # Store first ticket data for this cluster
                if cluster not in clusters_map:
                    clusters_map[cluster] = result["data"]
                    logger.info(f"[FINALIZER] New cluster found: {cluster}")
    
    logger.info(f"[FINALIZER] Phase 2 complete: {len(clusters_map)} unique clusters identified")
    
    # Enqueue stage2 ONCE per unique cluster
    logger.info("[FINALIZER] Phase 3: Enqueueing stage2 jobs (one per cluster)")
    stage2_jobs = []
    for cluster, ticket_data in clusters_map.items():
        job = queue.enqueue(process_ticket_stage2, ticket_data)
        stage2_jobs.append(job.id)
        logger.info(f"[FINALIZER] Enqueued stage2 job {job.id} for cluster {cluster}")
    
    logger.info(f"[FINALIZER] Complete: {len(stage2_jobs)} stage2 jobs enqueued")
    
    return {
        "stage1_processed": len(all_results),
        "unique_clusters": len(clusters_map),
        "clusters": list(clusters_map.keys()),
        "stage2_enqueued": len(stage2_jobs)
    }

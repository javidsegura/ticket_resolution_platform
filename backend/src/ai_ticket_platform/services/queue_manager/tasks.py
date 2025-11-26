
# WRITE HERE JOBS + FUNCTIONS USED IN JOBS (PRINT TO STDOUT WHEN YOU ARE MAKING PROGRESS)

import time
from typing import Dict, Any, List


from rq import Queue
from rq.job import Job


redis_client_connector = initialize_redis_client()
sync_redis_connection = redis_client_connector.get_sync_connection()
queue = Queue("default", connection=sync_redis_connection)
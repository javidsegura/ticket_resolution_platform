from ai_ticket_platform.core.clients.redis import initialize_redis_client
from rq import Queue


def get_sync_redis_connection():
	redis_client_connector = initialize_redis_client()
	return redis_client_connector.get_sync_connection()


def get_queue() -> Queue:
	# This would ideally get a connection from a pool managed in the lifespan
	sync_redis_connection = get_sync_redis_connection()
	return Queue("default", connection=sync_redis_connection)

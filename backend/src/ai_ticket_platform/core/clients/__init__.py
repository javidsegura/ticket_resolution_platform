from .aws import initialize_aws_s3_client, initialize_aws_secrets_manager_client, s3_client, secrets_manager_client
from .redis import redis_client, initialize_redis_client
from .llm import LLMClient, initialize_llm_client, llm_client
from .azure_search import (
	initialize_azure_search,
	get_azure_search,
	azure_search_store,
	initialize_azure_search_indexer,
	get_azure_search_indexer,
	azure_search_indexer,
)

# Cache manager and azure_search are assigned dynamically in main.py after initialization
cache_manager = None
azure_search = None

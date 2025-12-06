from .aws import (
	initialize_aws_s3_client,
	initialize_aws_secrets_manager_client,
	s3_client,
	secrets_manager_client,
)
from .redis import redis_client, initialize_redis_client
from .llm import LLMClient, initialize_llm_client, get_llm_client, llm_client
from .chroma_client import (
	ChromaVectorStore,
	initialize_chroma_vectorstore,
	get_chroma_vectorstore,
	chroma_vectorstore,
)

# Cache manager and chroma_vectorstore are assigned dynamically in main.py after initialization
cache_manager = None
chroma_vectorstore = None

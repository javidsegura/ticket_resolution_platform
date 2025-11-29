"""Cache key naming conventions and constants."""


class CacheKeys:
	"""Centralized cache key definitions for Redis."""

	# Article cache keys (Published articles with blob_path references)
	@staticmethod
	def article(article_id: str) -> str:
		"""
		Generate the cache key for a published article.
		
		Parameters:
			article_id (str): Article unique identifier used to build the key.
		
		Returns:
			Cache key string in the format "article:{article_id}".
		"""
		return f"article:{article_id}"

	# Clustering cache keys (LLM clustering results)
	@staticmethod
	def clustering_batch(input_hash: str) -> str:
		"""
		Generate the Redis cache key for clustering batch results.
		
		Parameters:
			input_hash (str): Hash identifying the clustering input batch.
		
		Returns:
			cache_key (str): Cache key string in the format "clustering:batch:{input_hash}".
		"""
		return f"clustering:batch:{input_hash}"
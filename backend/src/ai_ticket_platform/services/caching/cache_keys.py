"""Cache key naming conventions and constants."""


class CacheKeys:
	"""Centralized cache key definitions for Redis."""

	# Article cache keys (Published articles with blob_path references)
	@staticmethod
	def article(article_id: str) -> str:
		"""Generate cache key for published article."""
		return f"article:{article_id}"

	# Clustering cache keys (LLM clustering results)
	@staticmethod
	def clustering_batch(input_hash: str) -> str:
		"""Generate cache key for clustering batch results."""
		return f"clustering:batch:{input_hash}"

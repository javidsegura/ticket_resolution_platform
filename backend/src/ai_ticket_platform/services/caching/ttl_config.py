"""TTL (Time-To-Live) configuration for cache items."""


class CacheTTL:
	"""TTL constants for different cache items."""

	# Published articles: 1 year (immutable, permanent articles from blob_path)
	ARTICLE_TTL: int = 31_536_000

	# Clustering results: 30 days (stable input → stable output, deduplication)
	CLUSTERING_TTL: int = 2_592_000

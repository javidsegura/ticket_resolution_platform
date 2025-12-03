"""Unit tests for cache keys."""

import pytest

from ai_ticket_platform.services.caching.cache_keys import CacheKeys


class TestCacheKeys:
	"""Test CacheKeys static methods."""

	def test_article_key(self):
		"""Test article cache key generation."""
		result = CacheKeys.article("123")

		assert result == "article:123"

	def test_article_key_with_string_id(self):
		"""Test article cache key with string ID."""
		result = CacheKeys.article("article-abc-def")

		assert result == "article:article-abc-def"

	def test_clustering_batch_key(self):
		"""Test clustering batch cache key generation."""
		result = CacheKeys.clustering_batch("abc123hash")

		assert result == "clustering:batch:abc123hash"

	def test_clustering_batch_key_with_hash(self):
		"""Test clustering batch cache key with SHA256 hash."""
		sha256_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
		result = CacheKeys.clustering_batch(sha256_hash)

		assert result == f"clustering:batch:{sha256_hash}"

"""Unit tests for CSV uploader service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestClusterTicketsWithCache:
	"""Test cluster_tickets_with_cache function."""

	@pytest.mark.asyncio
	async def test_cluster_tickets_with_cache_empty_list(self):
		"""Test that empty ticket list returns zero results."""
		from ai_ticket_platform.services.csv_uploader.csv_uploader import (
			cluster_tickets_with_cache,
		)

		mock_db = MagicMock()

		result = await cluster_tickets_with_cache(mock_db, [])

		assert result["total_tickets"] == 0
		assert result["clusters_created"] == 0
		assert result["clusters"] == []
		assert result["cached"] is False

	@pytest.mark.asyncio
	async def test_cluster_tickets_with_cache_success(self):
		"""Test successful clustering with tickets."""
		from ai_ticket_platform.services.csv_uploader.csv_uploader import (
			cluster_tickets_with_cache,
		)

		mock_db = MagicMock()
		tickets_data = [
			{"subject": "Login issue", "body": "Can't login"},
			{"subject": "Password reset", "body": "Reset password"},
		]

		mock_clustering_result = {
			"total_tickets": 2,
			"clusters_created": 1,
			"clusters": [{"cluster_id": 1, "tickets": tickets_data}],
			"cached": False,
		}

		with patch(
			"ai_ticket_platform.services.csv_uploader.csv_uploader.cluster_tickets",
			new=AsyncMock(return_value=mock_clustering_result),
		):
			result = await cluster_tickets_with_cache(mock_db, tickets_data)

			assert result["total_tickets"] == 2
			assert result["clusters_created"] == 1
			assert len(result["clusters"]) == 1

	@pytest.mark.asyncio
	async def test_cluster_tickets_with_cache_error(self):
		"""Test that clustering errors are handled and re-raised as RuntimeError."""
		from ai_ticket_platform.services.csv_uploader.csv_uploader import (
			cluster_tickets_with_cache,
		)

		mock_db = MagicMock()
		tickets_data = [{"subject": "Test", "body": "Test body"}]

		with patch(
			"ai_ticket_platform.services.csv_uploader.csv_uploader.cluster_tickets",
			new=AsyncMock(side_effect=Exception("Clustering failed")),
		):
			with pytest.raises(RuntimeError) as exc_info:
				await cluster_tickets_with_cache(mock_db, tickets_data)

			assert "Failed to cluster tickets" in str(exc_info.value)
			assert "Clustering failed" in str(exc_info.value)

"""Unit tests for clustering service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from ai_ticket_platform.services.clustering.cluster_service import (
    cluster_and_categorize_tickets,
    _compute_clustering_hash,
    _extract_ticket_texts
)


class TestClusteringHash:
    """Test hash computation for clustering deduplication."""

    def test_compute_hash_same_tickets_same_hash(self):
        """Test that same tickets always produce same hash."""
        tickets = ["Login Bug", "Password Reset", "Payment Issue"]
        hash1 = _compute_clustering_hash(tickets)
        hash2 = _compute_clustering_hash(tickets)
        assert hash1 == hash2

    def test_compute_hash_different_order_same_hash(self):
        """Test that ticket order doesn't affect hash (sorted)."""
        tickets1 = ["Login Bug", "Password Reset", "Payment Issue"]
        tickets2 = ["Password Reset", "Login Bug", "Payment Issue"]
        hash1 = _compute_clustering_hash(tickets1)
        hash2 = _compute_clustering_hash(tickets2)
        assert hash1 == hash2

    def test_compute_hash_different_tickets_different_hash(self):
        """Test that different tickets produce different hashes."""
        tickets1 = ["Login Bug", "Password Reset"]
        tickets2 = ["Login Bug", "Password Reset", "Payment Issue"]
        hash1 = _compute_clustering_hash(tickets1)
        hash2 = _compute_clustering_hash(tickets2)
        assert hash1 != hash2

    def test_compute_hash_returns_valid_sha256(self):
        """Test that returned hash is valid SHA256."""
        tickets = ["Test", "Tickets"]
        hash_result = _compute_clustering_hash(tickets)
        assert len(hash_result) == 64  # SHA256 hex is 64 chars
        assert all(c in "0123456789abcdef" for c in hash_result)


class TestExtractTicketTexts:
    """Test ticket text extraction from dictionaries."""

    def test_extract_ticket_texts_from_subject_field(self):
        """Test extracting from standard 'subject' field."""
        tickets = [
            {"subject": "Login Bug", "body": "Cannot login"},
            {"subject": "Password Reset", "body": "Need reset"}
        ]
        texts = _extract_ticket_texts(tickets)
        assert len(texts) == 2
        assert "Login Bug" in texts
        assert "Password Reset" in texts

    def test_extract_ticket_texts_from_title_field(self):
        """Test extracting from legacy 'title' field."""
        tickets = [
            {"title": "Login Bug", "content": "Cannot login"},
            {"title": "Password Reset", "content": "Need reset"}
        ]
        texts = _extract_ticket_texts(tickets)
        assert len(texts) == 2
        assert "Login Bug" in texts
        assert "Password Reset" in texts

    def test_extract_ticket_texts_from_ticket_subject_field(self):
        """Test extracting from 'Ticket Subject' field."""
        tickets = [
            {"Ticket Subject": "Login Bug"},
            {"Ticket Subject": "Password Reset"}
        ]
        texts = _extract_ticket_texts(tickets)
        assert len(texts) == 2
        assert "Login Bug" in texts
        assert "Password Reset" in texts

    def test_extract_skips_empty_subjects(self):
        """Test that empty subject fields are skipped."""
        tickets = [
            {"subject": "Login Bug"},
            {"subject": ""},
            {"subject": "  "},
            {"subject": "Password Reset"}
        ]
        texts = _extract_ticket_texts(tickets)
        assert len(texts) == 2
        assert "Login Bug" in texts
        assert "Password Reset" in texts

    def test_extract_strips_whitespace(self):
        """Test that whitespace is stripped from subjects."""
        tickets = [
            {"subject": "  Login Bug  "},
            {"subject": "\nPassword Reset\n"}
        ]
        texts = _extract_ticket_texts(tickets)
        assert texts[0] == "Login Bug"
        assert texts[1] == "Password Reset"

    def test_extract_from_mixed_field_names(self):
        """Test extraction from tickets with different field names."""
        tickets = [
            {"subject": "Bug 1"},
            {"title": "Bug 2"},
            {"Ticket Subject": "Bug 3"}
        ]
        texts = _extract_ticket_texts(tickets)
        assert len(texts) == 3
        assert "Bug 1" in texts
        assert "Bug 2" in texts
        assert "Bug 3" in texts


@pytest.mark.asyncio
class TestClusteringWorkflow:
    """Test the main clustering workflow."""

    async def test_cluster_empty_tickets_list(self):
        """Test clustering with empty ticket list."""
        result = await cluster_and_categorize_tickets([], MagicMock())
        assert result["total_tickets"] == 0
        assert result["clusters_created"] == 0
        assert result["clusters"] == []

    async def test_cluster_with_cache_hit(self):
        """Test clustering with cache hit."""
        tickets = [{"subject": "Login Bug"}, {"subject": "Password Reset"}]
        mock_llm_client = MagicMock()

        mock_cache_result = {
            "total_tickets": 2,
            "clusters_created": 1,
            "clusters": [{"topic_name": "Auth Issues"}]
        }

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = mock_cache_result

        with patch("ai_ticket_platform.services.clustering.cluster_service.clients.cache_manager", mock_cache_manager):
            result = await cluster_and_categorize_tickets(tickets, mock_llm_client)
            assert result == mock_cache_result
            mock_cache_manager.get.assert_called_once()

    async def test_cluster_with_cache_miss_calls_llm(self):
        """Test clustering with cache miss calls LLM."""
        tickets = [{"subject": "Login Bug"}, {"subject": "Password Reset"}]
        mock_llm_client = MagicMock()

        mock_llm_result = {
            "total_tickets": 2,
            "clusters_created": 1,
            "clusters": [{"topic_name": "Auth Issues", "ticket_indices": [0, 1]}]
        }

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch("ai_ticket_platform.services.clustering.cluster_service.clients.cache_manager", mock_cache_manager):
            with patch("ai_ticket_platform.services.clustering.cluster_service.llm_clusterer.cluster_tickets") as mock_cluster:
                mock_cluster.return_value = mock_llm_result
                result = await cluster_and_categorize_tickets(tickets, mock_llm_client)
                assert result["clusters_created"] == 1
                mock_cluster.assert_called_once()

    async def test_cluster_caches_result_after_llm_call(self):
        """Test that clustering result is cached after LLM call."""
        tickets = [{"subject": "Login Bug"}]
        mock_llm_client = MagicMock()

        mock_llm_result = {
            "total_tickets": 1,
            "clusters_created": 1,
            "clusters": [{"topic_name": "Auth Issue", "ticket_indices": [0]}]
        }

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch("ai_ticket_platform.services.clustering.cluster_service.clients.cache_manager", mock_cache_manager):
            with patch("ai_ticket_platform.services.clustering.cluster_service.llm_clusterer.cluster_tickets") as mock_cluster:
                mock_cluster.return_value = mock_llm_result
                result = await cluster_and_categorize_tickets(tickets, mock_llm_client)
                mock_cache_manager.set.assert_called_once()

    async def test_cluster_without_llm_client(self):
        """Test clustering with no LLM client returns empty result."""
        tickets = [{"subject": "Login Bug"}]
        result = await cluster_and_categorize_tickets(tickets, None)
        assert result["total_tickets"] == 1
        assert result["clusters_created"] == 0
        assert result["clusters"] == []

    async def test_cluster_without_cache_manager(self):
        """Test clustering without cache manager still works."""
        tickets = [{"subject": "Login Bug"}, {"subject": "Password Reset"}]
        mock_llm_client = MagicMock()

        mock_llm_result = {
            "total_tickets": 2,
            "clusters_created": 1,
            "clusters": [{"topic_name": "Auth", "ticket_indices": [0, 1]}]
        }

        with patch("ai_ticket_platform.services.clustering.cluster_service.clients.cache_manager", None):
            with patch("ai_ticket_platform.services.clustering.cluster_service.llm_clusterer.cluster_tickets") as mock_cluster:
                mock_cluster.return_value = mock_llm_result
                result = await cluster_and_categorize_tickets(tickets, mock_llm_client)
                assert result["total_tickets"] == 2
                assert result["clusters_created"] == 1

    async def test_cluster_llm_failure_raises_error(self):
        """Test that LLM failures are propagated."""
        tickets = [{"subject": "Login Bug"}]
        mock_llm_client = MagicMock()

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch("ai_ticket_platform.services.clustering.cluster_service.clients.cache_manager", mock_cache_manager):
            with patch("ai_ticket_platform.services.clustering.cluster_service.llm_clusterer.cluster_tickets") as mock_cluster:
                mock_cluster.side_effect = Exception("LLM API error")
                with pytest.raises(RuntimeError, match="Failed to cluster tickets"):
                    await cluster_and_categorize_tickets(tickets, mock_llm_client)

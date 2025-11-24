"""Unit tests for LLM clusterer."""

import pytest
from unittest.mock import MagicMock, patch
from ai_ticket_platform.services.clustering.llm_clusterer import cluster_tickets


class TestLLMClusterer:
    """Test LLM-based ticket clustering."""

    def test_cluster_tickets_calls_llm_with_correct_params(self):
        """Test that cluster_tickets calls LLM with correct parameters."""
        ticket_texts = ["Login Bug", "Password Reset"]
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "clusters": [
                {
                    "topic_name": "Auth Issues",
                    "product": "Auth",
                    "category": "Credentials",
                    "subcategory": "Password",
                    "ticket_indices": [0, 1],
                    "summary": "Password issues"
                }
            ]
        }

        with patch("ai_ticket_platform.services.clustering.llm_clusterer.prompt_builder") as mock_pb:
            mock_pb.build_clustering_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {"type": "object"}

            result = cluster_tickets(mock_llm_client, ticket_texts)

            mock_llm_client.call_llm_structured.assert_called_once()
            call_kwargs = mock_llm_client.call_llm_structured.call_args[1]
            assert "prompt" in call_kwargs
            assert "output_schema" in call_kwargs
            assert "task_config" in call_kwargs
            assert call_kwargs["temperature"] == 0.3

    def test_cluster_tickets_validates_ticket_assignment(self):
        """Test that all tickets are assigned to clusters."""
        ticket_texts = ["Bug1", "Bug2", "Bug3"]
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "clusters": [
                {
                    "topic_name": "All Bugs",
                    "product": "App",
                    "category": "Bugs",
                    "subcategory": "Issues",
                    "ticket_indices": [0, 1, 2],
                    "summary": "All bugs"
                }
            ]
        }

        with patch("ai_ticket_platform.services.clustering.llm_clusterer.prompt_builder") as mock_pb:
            mock_pb.build_clustering_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}

            result = cluster_tickets(mock_llm_client, ticket_texts)
            assert result["clusters"][0]["ticket_indices"] == [0, 1, 2]

    def test_cluster_tickets_detects_unassigned_tickets(self):
        """Test that unassigned tickets are detected."""
        ticket_texts = ["Bug1", "Bug2", "Bug3"]
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "clusters": [
                {
                    "topic_name": "Some Bugs",
                    "product": "App",
                    "category": "Bugs",
                    "subcategory": "Issues",
                    "ticket_indices": [0, 1],  # Missing ticket 2
                    "summary": "Some bugs"
                }
            ]
        }

        with patch("ai_ticket_platform.services.clustering.llm_clusterer.prompt_builder") as mock_pb:
            mock_pb.build_clustering_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}

            with pytest.raises(ValueError, match="Ticket assignment mismatch"):
                cluster_tickets(mock_llm_client, ticket_texts)

    def test_cluster_tickets_detects_invalid_indices(self):
        """Test that invalid ticket indices are detected."""
        ticket_texts = ["Bug1", "Bug2"]
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "clusters": [
                {
                    "topic_name": "Bugs",
                    "product": "App",
                    "category": "Bugs",
                    "subcategory": "Issues",
                    "ticket_indices": [0, 1, 5],  # Index 5 doesn't exist
                    "summary": "Bugs"
                }
            ]
        }

        with patch("ai_ticket_platform.services.clustering.llm_clusterer.prompt_builder") as mock_pb:
            mock_pb.build_clustering_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}

            with pytest.raises(ValueError, match="Ticket assignment mismatch"):
                cluster_tickets(mock_llm_client, ticket_texts)

    def test_cluster_tickets_returns_llm_result(self):
        """Test that function returns LLM result."""
        ticket_texts = ["Bug1"]
        mock_llm_client = MagicMock()
        expected_result = {
            "clusters": [
                {
                    "topic_name": "Bug",
                    "product": "App",
                    "category": "Issues",
                    "subcategory": "Error",
                    "ticket_indices": [0],
                    "summary": "A bug"
                }
            ]
        }
        mock_llm_client.call_llm_structured.return_value = expected_result

        with patch("ai_ticket_platform.services.clustering.llm_clusterer.prompt_builder") as mock_pb:
            mock_pb.build_clustering_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}

            result = cluster_tickets(mock_llm_client, ticket_texts)
            assert result == expected_result

    def test_cluster_tickets_with_multiple_clusters(self):
        """Test clustering with multiple clusters."""
        ticket_texts = ["Login Bug", "Password Reset", "Payment Issue", "Checkout Timeout"]
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "clusters": [
                {
                    "topic_name": "Auth",
                    "product": "Auth",
                    "category": "Credentials",
                    "subcategory": "Password",
                    "ticket_indices": [0, 1],
                    "summary": "Auth issues"
                },
                {
                    "topic_name": "Payments",
                    "product": "Payments",
                    "category": "Checkout",
                    "subcategory": "Processing",
                    "ticket_indices": [2, 3],
                    "summary": "Payment issues"
                }
            ]
        }

        with patch("ai_ticket_platform.services.clustering.llm_clusterer.prompt_builder") as mock_pb:
            mock_pb.build_clustering_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}

            result = cluster_tickets(mock_llm_client, ticket_texts)
            assert len(result["clusters"]) == 2
            assert result["clusters"][0]["ticket_indices"] == [0, 1]
            assert result["clusters"][1]["ticket_indices"] == [2, 3]

    def test_cluster_tickets_sets_correct_temperature(self):
        """Test that temperature is set to 0.3 for deterministic clustering."""
        ticket_texts = ["Bug1"]
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "clusters": [
                {
                    "topic_name": "Bug",
                    "product": "App",
                    "category": "Issues",
                    "subcategory": "Error",
                    "ticket_indices": [0],
                    "summary": "A bug"
                }
            ]
        }

        with patch("ai_ticket_platform.services.clustering.llm_clusterer.prompt_builder") as mock_pb:
            mock_pb.build_clustering_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}

            cluster_tickets(mock_llm_client, ticket_texts)

            call_kwargs = mock_llm_client.call_llm_structured.call_args[1]
            assert call_kwargs["temperature"] == 0.3

    def test_cluster_tickets_sets_system_prompt(self):
        """Test that system prompt is correctly set."""
        ticket_texts = ["Bug1"]
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "clusters": [
                {
                    "topic_name": "Bug",
                    "product": "App",
                    "category": "Issues",
                    "subcategory": "Error",
                    "ticket_indices": [0],
                    "summary": "A bug"
                }
            ]
        }

        with patch("ai_ticket_platform.services.clustering.llm_clusterer.prompt_builder") as mock_pb:
            mock_pb.build_clustering_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}

            cluster_tickets(mock_llm_client, ticket_texts)

            call_kwargs = mock_llm_client.call_llm_structured.call_args[1]
            task_config = call_kwargs["task_config"]
            assert "clustering expert" in task_config["system_prompt"].lower()

"""Unit tests for CSV uploader service (clustering and database saving)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.services.csv_uploader.csv_uploader import (
    cluster_tickets_with_cache,
    save_tickets_to_db
)


@pytest.mark.asyncio
class TestClusterTicketsWithCache:
    """Test clustering with cache integration."""

    async def test_cluster_empty_tickets_returns_zero_results(self):
        """Test clustering empty list returns zero results."""
        result = await cluster_tickets_with_cache([])

        assert result["total_tickets"] == 0
        assert result["clusters_created"] == 0
        assert result["clusters"] == []

    async def test_cluster_tickets_calls_cluster_service(self):
        """Test that cluster_and_categorize_tickets is called."""
        tickets = [{"subject": "Bug 1"}, {"subject": "Bug 2"}]
        mock_llm_client = MagicMock()

        expected_result = {
            "total_tickets": 2,
            "clusters_created": 1,
            "clusters": []
        }

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.cluster_and_categorize_tickets") as mock_cluster:
            mock_cluster.return_value = expected_result

            result = await cluster_tickets_with_cache(tickets)

            mock_cluster.assert_called_once()
            assert result == expected_result

    async def test_cluster_tickets_passes_correct_llm_client(self):
        """Test that injected LLM client is used."""
        tickets = [{"subject": "Bug"}]

        expected_result = {
            "total_tickets": 1,
            "clusters_created": 0,
            "clusters": []
        }

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.cluster_and_categorize_tickets") as mock_cluster:
            mock_cluster.return_value = expected_result

            result = await cluster_tickets_with_cache(tickets)

            # Verify llm_client was passed
            call_args = mock_cluster.call_args
            assert len(call_args[0]) == 2  # tickets, llm_client

    async def test_cluster_tickets_propagates_errors(self):
        """Test that clustering errors are propagated."""
        tickets = [{"subject": "Bug"}]

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.cluster_and_categorize_tickets") as mock_cluster:
            mock_cluster.side_effect = Exception("Clustering failed")

            with pytest.raises(RuntimeError, match="Failed to cluster tickets"):
                await cluster_tickets_with_cache(tickets)

    async def test_cluster_multiple_tickets(self):
        """Test clustering multiple tickets."""
        tickets = [
            {"subject": "Bug 1"},
            {"subject": "Bug 2"},
            {"subject": "Bug 3"}
        ]

        expected_result = {
            "total_tickets": 3,
            "clusters_created": 2,
            "clusters": [
                {"topic": "Auth Issues", "count": 2},
                {"topic": "Performance", "count": 1}
            ]
        }

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.cluster_and_categorize_tickets") as mock_cluster:
            mock_cluster.return_value = expected_result

            result = await cluster_tickets_with_cache(tickets)

            assert result["total_tickets"] == 3
            assert result["clusters_created"] == 2
            assert len(result["clusters"]) == 2


class TestSaveTicketsToDb:
    """Test saving tickets to database."""

    @pytest.mark.asyncio
    async def test_save_tickets_empty_list_raises_error(self):
        """Test that saving empty list raises ValueError."""
        mock_db = MagicMock(spec=AsyncSession)

        with pytest.raises(ValueError, match="No tickets data to save"):
            await save_tickets_to_db(mock_db, [])

    @pytest.mark.asyncio
    async def test_save_tickets_calls_create_tickets(self):
        """Test that create_tickets is called with correct data."""
        mock_db = MagicMock(spec=AsyncSession)
        tickets = [
            {"subject": "Bug 1", "body": "Description 1"},
            {"subject": "Bug 2", "body": "Description 2"}
        ]

        mock_created = [MagicMock(id=1), MagicMock(id=2)]

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.create_tickets") as mock_create:
            mock_create.return_value = mock_created

            result = await save_tickets_to_db(mock_db, tickets)

            mock_create.assert_called_once()
            assert result == mock_created

    @pytest.mark.asyncio
    async def test_save_tickets_passes_db_session(self):
        """Test that database session is passed correctly."""
        mock_db = MagicMock(spec=AsyncSession)
        tickets = [{"subject": "Bug", "body": "Description"}]
        mock_created = [MagicMock(id=1)]

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.create_tickets") as mock_create:
            mock_create.return_value = mock_created

            await save_tickets_to_db(mock_db, tickets)

            # Check that create_tickets was called with db and tickets_data
            call_args = mock_create.call_args
            # Arguments can be positional or keyword
            if call_args.kwargs:
                assert call_args.kwargs["db"] == mock_db
                assert call_args.kwargs["tickets_data"] == tickets
            else:
                # Positional arguments
                assert call_args.args[0] == mock_db
                assert call_args.args[1] == tickets

    @pytest.mark.asyncio
    async def test_save_tickets_handles_database_error(self):
        """Test that database errors are propagated."""
        mock_db = MagicMock(spec=AsyncSession)
        tickets = [{"subject": "Bug", "body": "Description"}]

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.create_tickets") as mock_create:
            mock_create.side_effect = Exception("Database connection failed")

            with pytest.raises(RuntimeError, match="Failed to save tickets"):
                await save_tickets_to_db(mock_db, tickets)

    @pytest.mark.asyncio
    async def test_save_single_ticket(self):
        """Test saving a single ticket."""
        mock_db = MagicMock(spec=AsyncSession)
        tickets = [{"subject": "Bug", "body": "Description"}]
        mock_created = [MagicMock(id=1)]

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.create_tickets") as mock_create:
            mock_create.return_value = mock_created

            result = await save_tickets_to_db(mock_db, tickets)

            assert len(result) == 1
            assert result[0].id == 1

    @pytest.mark.asyncio
    async def test_save_multiple_tickets(self):
        """Test saving multiple tickets."""
        mock_db = MagicMock(spec=AsyncSession)
        tickets = [
            {"subject": "Bug 1", "body": "Desc 1"},
            {"subject": "Bug 2", "body": "Desc 2"},
            {"subject": "Bug 3", "body": "Desc 3"}
        ]
        mock_created = [
            MagicMock(id=1),
            MagicMock(id=2),
            MagicMock(id=3)
        ]

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.create_tickets") as mock_create:
            mock_create.return_value = mock_created

            result = await save_tickets_to_db(mock_db, tickets)

            assert len(result) == 3
            assert result[0].id == 1
            assert result[1].id == 2
            assert result[2].id == 3

    @pytest.mark.asyncio
    async def test_save_tickets_returns_ticket_objects(self):
        """Test that returned objects are Ticket objects with IDs."""
        mock_db = MagicMock(spec=AsyncSession)
        tickets = [{"subject": "Bug", "body": "Description"}]

        mock_ticket = MagicMock()
        mock_ticket.id = 123
        mock_created = [mock_ticket]

        with patch("ai_ticket_platform.services.csv_uploader.csv_uploader.create_tickets") as mock_create:
            mock_create.return_value = mock_created

            result = await save_tickets_to_db(mock_db, tickets)

            assert len(result) == 1
            assert result[0].id == 123

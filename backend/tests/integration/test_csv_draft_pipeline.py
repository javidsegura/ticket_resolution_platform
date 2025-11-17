"""
Integration tests for CSV → Draft pipeline

Verify data flows correctly from upload endpoint through clustering to draft generation
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy import select

from ai_ticket_platform.database.generated_models import (
    Ticket,
    TicketStatus,
    Draft,
    DraftStatus,
)


@pytest.mark.asyncio
class TestCSVDraftPipeline:
    """Tests for CSV upload and draft generation pipeline"""

    async def test_csv_upload_creates_ticket(self, async_client, db_session):
        """CSV upload creates ticket with UPLOADED status"""
        csv_content = b"title,content\nTest Issue,This is a test issue"

        # Mock the clustering service to avoid LLM API calls
        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 1,
                'clusters_created': 1,
                'clusters': [{'topic_name': 'Issues', 'product_category': 'Support'}]
            }

            response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("test.csv", csv_content)}
            )

        assert response.status_code == 200
        data = response.json()
        assert "ticket_ids" in data
        assert data["status"] == "uploaded_and_clustered"
        assert len(data["ticket_ids"]) == 1

        # Verify ticket in database
        result = await db_session.execute(
            select(Ticket).where(Ticket.ticket_id == data["ticket_ids"][0])
        )
        ticket = result.scalar_one_or_none()
        assert ticket is not None
        assert ticket.status == TicketStatus.UPLOADED

    async def test_clustering_receives_ticket(self, async_client, db_session, create_test_ticket):
        """Clustering endpoint receives uploaded ticket"""
        ticket = await create_test_ticket(db_session, status=TicketStatus.UPLOADED)

        # Mock the clustering service to return realistic cluster structure
        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 1,
                'clusters_created': 1,
                'clusters': [
                    {
                        'topic_name': 'Technical Issues',
                        'product_category': 'Engineering',
                        'tickets_count': 1
                    }
                ]
            }

            response = await async_client.post(f"/api/tickets/{ticket.ticket_id}/cluster")

        assert response.status_code == 200
        data = response.json()
        assert "clusters" in data
        assert "primary_cluster" in data
        assert data["primary_cluster"] == "Technical Issues"
        assert len(data["clusters"]) == 1
        assert data["clusters"][0]["topic_name"] == "Technical Issues"

    async def test_draft_generated_from_ticket(self, async_client, db_session, create_test_ticket):
        """Draft is generated from ticket"""
        ticket = await create_test_ticket(db_session, title="Test Issue", content="Issue description")

        response = await async_client.post(f"/api/drafts/generate?ticket_id={ticket.ticket_id}")

        assert response.status_code == 200
        data = response.json()
        assert "draft_id" in data
        assert data["status"] == "pending"
        assert data["ticket_id"] == ticket.ticket_id

        # Verify draft in database
        result = await db_session.execute(
            select(Draft).where(Draft.draft_id == data["draft_id"])
        )
        draft = result.scalar_one_or_none()
        assert draft is not None
        assert draft.status == DraftStatus.PENDING
        assert draft.ticket_id == ticket.ticket_id

    async def test_complete_pipeline_csv_to_draft(self, async_client, db_session):
        """Complete pipeline: CSV upload → Cluster → Draft generation"""
        # Mock clustering service to avoid LLM API calls
        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 1,
                'clusters_created': 1,
                'clusters': [{'topic_name': 'Issues', 'product_category': 'Support'}]
            }

            # Step 1: Upload CSV
            csv_content = b"title,content\nTest Issue,Issue description"
            upload_response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("test.csv", csv_content)}
            )
            assert upload_response.status_code == 200
            ticket_id = upload_response.json()["ticket_ids"][0]

            # Step 2: Cluster ticket (already done in upload, but test endpoint separately)
            cluster_response = await async_client.post(f"/api/tickets/{ticket_id}/cluster")
            assert cluster_response.status_code == 200
            assert "clusters" in cluster_response.json()

        # Step 3: Generate draft
        draft_response = await async_client.post(f"/api/drafts/generate?ticket_id={ticket_id}")
        assert draft_response.status_code == 200
        draft_id = draft_response.json()["draft_id"]

        # Verify all resources in database
        ticket_result = await db_session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        ticket = ticket_result.scalar_one_or_none()
        assert ticket is not None

        draft_result = await db_session.execute(
            select(Draft).where(Draft.draft_id == draft_id)
        )
        draft = draft_result.scalar_one_or_none()
        assert draft is not None
        assert draft.ticket_id == ticket_id

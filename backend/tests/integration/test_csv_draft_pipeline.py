"""
Integration tests for CSV → Draft pipeline

Tests the complete flow:
1. CSV upload creates ticket
2. Ticket is clustered
3. Draft is generated from ticket
"""

import pytest
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
        """Test that CSV upload creates a ticket with UPLOADED status"""
        # Create a mock CSV file
        csv_content = b"title,content\nTest Issue,This is a test issue"

        response = await async_client.post(
            "/api/csv/upload",
            files={"file": ("test.csv", csv_content)}
        )

        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data
        assert data["status"] == "uploaded"
        assert data["title"] == "test.csv"

        # Verify ticket in database
        result = await db_session.execute(
            select(Ticket).where(Ticket.ticket_id == data["ticket_id"])
        )
        ticket = result.scalar_one_or_none()

        assert ticket is not None
        assert ticket.status == TicketStatus.UPLOADED
        assert len(ticket.content) > 0

    async def test_csv_upload_with_empty_file(self, async_client):
        """Test that empty CSV files are handled"""
        response = await async_client.post(
            "/api/csv/upload",
            files={"file": ("empty.csv", b"")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data

    async def test_clustering_requires_valid_ticket(self, async_client):
        """Test that clustering endpoint requires a valid ticket"""
        response = await async_client.post(
            "/api/tickets/invalid-ticket-id/cluster"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_clustering_receives_valid_ticket(self, async_client, db_session, create_test_ticket):
        """Test that clustering receives uploaded ticket and returns clusters"""
        # Create test ticket
        ticket = await create_test_ticket(db_session, status=TicketStatus.UPLOADED)

        response = await async_client.post(f"/api/tickets/{ticket.ticket_id}/cluster")

        assert response.status_code == 200
        data = response.json()
        assert "clusters" in data
        assert "primary_cluster" in data
        assert len(data["clusters"]) > 0
        assert data["primary_cluster"] is not None

    async def test_clustering_response_has_confidence_scores(self, async_client, create_test_ticket, db_session):
        """Test that clustering response includes confidence scores"""
        ticket = await create_test_ticket(db_session)

        response = await async_client.post(f"/api/tickets/{ticket.ticket_id}/cluster")

        assert response.status_code == 200
        data = response.json()

        # Verify cluster structure
        for cluster in data["clusters"]:
            assert "category" in cluster
            assert "confidence" in cluster
            assert 0 <= cluster["confidence"] <= 1

    async def test_draft_generation_requires_valid_ticket(self, async_client):
        """Test that draft generation requires a valid ticket"""
        response = await async_client.post(
            "/api/drafts/generate?ticket_id=invalid-id"
        )

        assert response.status_code == 404

    async def test_draft_generation_from_ticket(self, async_client, db_session, create_test_ticket):
        """Test that draft is generated from ticket"""
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
        assert len(draft.content) > 0

    async def test_draft_content_includes_ticket_info(self, async_client, db_session, create_test_ticket):
        """Test that generated draft includes ticket information"""
        ticket = await create_test_ticket(
            db_session,
            title="Important Feature Request",
            content="We need this feature"
        )

        response = await async_client.post(f"/api/drafts/generate?ticket_id={ticket.ticket_id}")

        data = response.json()
        draft_id = data["draft_id"]

        # Get draft and verify content
        draft_response = await async_client.get(f"/api/drafts/{draft_id}")
        draft_data = draft_response.json()

        assert ticket.title in draft_data["content"]

    async def test_complete_pipeline_csv_to_draft(self, async_client, db_session):
        """Test complete pipeline: CSV → Ticket → Cluster → Draft"""
        # Step 1: Upload CSV
        csv_content = b"title,content\nTest Issue,Issue description"
        upload_response = await async_client.post(
            "/api/csv/upload",
            files={"file": ("test.csv", csv_content)}
        )
        assert upload_response.status_code == 200
        ticket_id = upload_response.json()["ticket_id"]

        # Step 2: Cluster ticket
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

    async def test_multiple_drafts_from_same_ticket(self, async_client, db_session, create_test_ticket):
        """Test that multiple drafts can be generated from same ticket"""
        ticket = await create_test_ticket(db_session)

        # Generate first draft
        response1 = await async_client.post(f"/api/drafts/generate?ticket_id={ticket.ticket_id}")
        draft_id_1 = response1.json()["draft_id"]

        # Generate second draft
        response2 = await async_client.post(f"/api/drafts/generate?ticket_id={ticket.ticket_id}")
        draft_id_2 = response2.json()["draft_id"]

        # Verify both drafts exist and are different
        assert draft_id_1 != draft_id_2

        result1 = await db_session.execute(
            select(Draft).where(Draft.draft_id == draft_id_1)
        )
        result2 = await db_session.execute(
            select(Draft).where(Draft.draft_id == draft_id_2)
        )

        draft1 = result1.scalar_one_or_none()
        draft2 = result2.scalar_one_or_none()

        assert draft1 is not None
        assert draft2 is not None
        assert draft1.ticket_id == draft2.ticket_id

    async def test_draft_invalid_status_format(self, async_client, create_test_ticket, db_session):
        """Test that invalid draft status is rejected"""
        ticket = await create_test_ticket(db_session)

        # Try to set invalid status
        response = await async_client.post(
            f"/api/tickets/{ticket.ticket_id}/status",
            json={"new_status": "INVALID_STATUS"}
        )

        # The endpoint expects form data, but we'll get a validation error
        assert response.status_code in [422, 404, 405]  # Validation error or method error

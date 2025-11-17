"""
Integration tests for Publishing flow

Validate markdown microsite generator rebuilds and exposes published articles
"""

import pytest
from sqlalchemy import select

from ai_ticket_platform.database.generated_models import (
    Draft,
    DraftStatus,
    PublishedArticle,
)


@pytest.mark.asyncio
class TestPublishFlow:
    """Tests for article publishing flow"""

    async def test_publish_approved_draft(self, async_client, db_session, create_test_draft):
        """Publishing approved draft creates published article"""
        draft = await create_test_draft(db_session, status=DraftStatus.APPROVED)

        response = await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        assert response.status_code == 200
        data = response.json()
        assert "article_id" in data
        assert data["draft_id"] == draft.draft_id
        assert "microsite_url" in data
        assert data["status"] == "published"

    async def test_publish_updates_draft_status(self, async_client, db_session, create_test_draft):
        """Publishing updates draft status to PUBLISHED"""
        draft = await create_test_draft(db_session, status=DraftStatus.APPROVED)

        await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        # Refresh draft from database
        result = await db_session.execute(
            select(Draft).where(Draft.draft_id == draft.draft_id)
        )
        updated_draft = result.scalar_one_or_none()
        assert updated_draft.status == DraftStatus.PUBLISHED

    async def test_microsite_url_generated(self, async_client, db_session, create_test_draft):
        """Microsite URL is generated when publishing"""
        draft = await create_test_draft(db_session, status=DraftStatus.APPROVED)

        response = await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        assert response.status_code == 200
        data = response.json()
        url = data["microsite_url"]
        assert url.startswith("https://microsite.example.com/articles/")

    async def test_get_published_article(self, async_client, db_session, create_test_published_article):
        """Published article can be retrieved and exposes microsite"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(f"/api/articles/{article.article_id}/microsite")

        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "markdown" in data
        assert data["url"] == article.microsite_url
        assert data["markdown"] == article.markdown_content

    async def test_cannot_publish_unapproved_draft(self, async_client, db_session, create_test_draft):
        """Cannot publish draft that is not approved"""
        draft = await create_test_draft(db_session, status=DraftStatus.PENDING)

        response = await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        assert response.status_code == 400
        assert "must be in 'APPROVED' status" in response.json()["detail"]

    async def test_cannot_publish_needs_edit_draft(self, async_client, db_session, create_test_draft):
        """Cannot publish draft that needs editing"""
        draft = await create_test_draft(db_session, status=DraftStatus.NEEDS_EDIT)

        response = await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        assert response.status_code == 400

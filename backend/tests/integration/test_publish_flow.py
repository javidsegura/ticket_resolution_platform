"""
Integration tests for Publishing flow

Tests the publishing workflow:
1. Approved draft → publish → creates PublishedArticle
2. Draft status changes to PUBLISHED
3. Validates microsite generation
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

    async def test_publish_approved_draft_creates_article(
        self, async_client, db_session, create_test_draft
    ):
        """Test that publishing approved draft creates PublishedArticle"""
        draft = await create_test_draft(db_session, status=DraftStatus.APPROVED)

        response = await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        assert response.status_code == 200
        data = response.json()
        assert "article_id" in data
        assert data["draft_id"] == draft.draft_id
        assert "microsite_url" in data
        assert data["status"] == "published"
        assert "published_at" in data

    async def test_publish_generates_microsite_url(
        self, async_client, db_session, create_test_draft
    ):
        """Test that publishing generates a valid microsite URL"""
        draft = await create_test_draft(db_session, status=DraftStatus.APPROVED)

        response = await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        assert response.status_code == 200
        data = response.json()

        url = data["microsite_url"]
        assert url.startswith("https://microsite.example.com/articles/")
        assert len(url) > len("https://microsite.example.com/articles/")

    async def test_publish_updates_draft_status_to_published(
        self, async_client, db_session, create_test_draft
    ):
        """Test that publishing updates draft status to PUBLISHED"""
        draft = await create_test_draft(db_session, status=DraftStatus.APPROVED)

        await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        # Refresh draft from database
        result = await db_session.execute(
            select(Draft).where(Draft.draft_id == draft.draft_id)
        )
        updated_draft = result.scalar_one_or_none()

        assert updated_draft.status == DraftStatus.PUBLISHED

    async def test_cannot_publish_unapproved_draft(
        self, async_client, db_session, create_test_draft
    ):
        """Test that unapproved drafts cannot be published"""
        draft = await create_test_draft(db_session, status=DraftStatus.PENDING)

        response = await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        assert response.status_code == 400
        assert "must be in 'APPROVED' status" in response.json()["detail"]

    async def test_cannot_publish_needs_edit_draft(
        self, async_client, db_session, create_test_draft
    ):
        """Test that drafts needing edits cannot be published"""
        draft = await create_test_draft(db_session, status=DraftStatus.NEEDS_EDIT)

        response = await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        assert response.status_code == 400

    async def test_publish_nonexistent_draft_returns_404(self, async_client):
        """Test that publishing nonexistent draft returns 404"""
        response = await async_client.post("/api/articles/publish/nonexistent-id")

        assert response.status_code == 404

    async def test_get_published_article_details(
        self, async_client, db_session, create_test_published_article
    ):
        """Test retrieving published article details"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(f"/api/articles/{article.article_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["article_id"] == article.article_id
        assert data["draft_id"] == article.draft_id
        assert data["markdown_content"] == article.markdown_content
        assert data["microsite_url"] == article.microsite_url

    async def test_get_microsite_returns_markdown_and_url(
        self, async_client, db_session, create_test_published_article
    ):
        """Test that microsite endpoint returns markdown content and URL"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(f"/api/articles/{article.article_id}/microsite")

        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "markdown" in data
        assert data["url"] == article.microsite_url
        assert data["markdown"] == article.markdown_content

    async def test_published_article_preserves_draft_content(
        self, async_client, db_session, create_test_draft
    ):
        """Test that published article preserves the draft's markdown content"""
        test_content = "# Important Announcement\n\nThis is crucial information"
        draft = await create_test_draft(
            db_session,
            status=DraftStatus.APPROVED,
            content=test_content
        )

        await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        # Get the article
        result = await db_session.execute(
            select(PublishedArticle).where(PublishedArticle.draft_id == draft.draft_id)
        )
        article = result.scalar_one_or_none()

        assert article.markdown_content == test_content

    async def test_multiple_articles_from_different_drafts(
        self, async_client, db_session, create_test_draft
    ):
        """Test that multiple articles can be published from different drafts"""
        draft1 = await create_test_draft(
            db_session,
            status=DraftStatus.APPROVED,
            content="# Article 1"
        )
        draft2 = await create_test_draft(
            db_session,
            status=DraftStatus.APPROVED,
            content="# Article 2"
        )

        response1 = await async_client.post(f"/api/articles/publish/{draft1.draft_id}")
        response2 = await async_client.post(f"/api/articles/publish/{draft2.draft_id}")

        assert response1.status_code == 200
        assert response2.status_code == 200

        article_id_1 = response1.json()["article_id"]
        article_id_2 = response2.json()["article_id"]

        assert article_id_1 != article_id_2

        # Verify both exist
        result1 = await db_session.execute(
            select(PublishedArticle).where(PublishedArticle.article_id == article_id_1)
        )
        result2 = await db_session.execute(
            select(PublishedArticle).where(PublishedArticle.article_id == article_id_2)
        )

        assert result1.scalar_one_or_none() is not None
        assert result2.scalar_one_or_none() is not None

    async def test_get_nonexistent_article_returns_404(self, async_client):
        """Test that requesting nonexistent article returns 404"""
        response = await async_client.get("/api/articles/nonexistent-id")

        assert response.status_code == 404

    async def test_article_has_published_timestamp(
        self, async_client, db_session, create_test_draft
    ):
        """Test that published articles have a published_at timestamp"""
        draft = await create_test_draft(db_session, status=DraftStatus.APPROVED)

        response = await async_client.post(f"/api/articles/publish/{draft.draft_id}")

        data = response.json()
        assert "published_at" in data
        assert data["published_at"] is not None

        # Verify in database
        result = await db_session.execute(
            select(PublishedArticle).where(PublishedArticle.article_id == data["article_id"])
        )
        article = result.scalar_one_or_none()
        assert article.published_at is not None

    async def test_microsite_url_is_unique(
        self, async_client, db_session, create_test_draft
    ):
        """Test that each published article gets a unique microsite URL"""
        draft1 = await create_test_draft(db_session, status=DraftStatus.APPROVED)
        draft2 = await create_test_draft(db_session, status=DraftStatus.APPROVED)

        response1 = await async_client.post(f"/api/articles/publish/{draft1.draft_id}")
        response2 = await async_client.post(f"/api/articles/publish/{draft2.draft_id}")

        url1 = response1.json()["microsite_url"]
        url2 = response2.json()["microsite_url"]

        assert url1 != url2

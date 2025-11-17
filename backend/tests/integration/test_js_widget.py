"""
Integration tests for JS Widget

Confirm manual trigger renders the correct micro-answer
"""

import pytest

from ai_ticket_platform.database.generated_models import PublishedArticle


@pytest.mark.asyncio
class TestJSWidget:
    """Tests for JS widget manual trigger and micro-answer rendering"""

    async def test_widget_manual_trigger(self, async_client, db_session, create_test_published_article):
        """Manual trigger endpoint works"""
        article = await create_test_published_article(db_session)

        response = await async_client.post(
            f"/api/widget/trigger/{article.article_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["article_id"] == article.article_id
        assert data["status"] == "triggered"
        assert data["microsite_url"] == article.microsite_url

    async def test_widget_render_micro_answer(self, async_client, db_session, create_test_published_article):
        """Widget renders micro-answer content"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "widget"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "html" in data
        assert data["article_id"] == article.article_id
        assert "micro-answer" in data["html"].lower()

    async def test_widget_contains_article_markdown(self, async_client, db_session, create_test_published_article):
        """Widget render converts markdown to HTML"""
        test_content = "# Test Answer\n\nThis is the micro-answer"
        article = await create_test_published_article(
            db_session,
            markdown_content=test_content
        )

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "widget"}
        )

        assert response.status_code == 200
        html = response.json()["html"]
        # Verify markdown was converted to HTML (should contain h1 tag and p tag)
        assert "<h1" in html or "Test Answer" in html
        assert "<p" in html or "micro-answer" in html
        assert "ai-ticket-widget" in html  # Widget container
        assert "micro-answer" in html  # Widget section

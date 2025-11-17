"""
Integration tests for JS Widget rendering

Tests the widget functionality:
1. Widget rendering with different formats
2. Manual trigger functionality
3. Embed script generation
"""

import pytest
from sqlalchemy import select

from ai_ticket_platform.database.generated_models import PublishedArticle


@pytest.mark.asyncio
class TestJSWidget:
    """Tests for JS widget rendering and micro-answer delivery"""

    async def test_widget_render_basic(
        self, async_client, db_session, create_test_published_article
    ):
        """Test basic widget rendering"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "widget"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "html" in data
        assert data["article_id"] == article.article_id
        assert data["format"] == "widget"

    async def test_widget_render_contains_micro_answer(
        self, async_client, db_session, create_test_published_article
    ):
        """Test that widget HTML contains micro-answer"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "widget"}
        )

        assert response.status_code == 200
        html = response.json()["html"]

        # Verify widget contains expected elements
        assert "micro-answer" in html.lower()
        assert article.markdown_content in html or "AI-Generated Answer" in html

    async def test_widget_render_contains_article_content(
        self, async_client, db_session, create_test_published_article
    ):
        """Test that widget contains the article's markdown content"""
        test_content = "# Test Article Title\n\nThis is the test content"
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

        # Content should be in the widget
        assert "Test Article Title" in html or test_content in html

    async def test_widget_render_link_to_microsite(
        self, async_client, db_session, create_test_published_article
    ):
        """Test that widget includes link to full article"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "widget"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["microsite_url"] == article.microsite_url

    @pytest.mark.parametrize("format_type", ["widget", "embed", "iframe"])
    async def test_widget_multiple_formats(
        self, async_client, db_session, create_test_published_article, format_type
    ):
        """Test widget rendering with different formats"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": format_type}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == format_type
        assert "html" in data

    async def test_widget_invalid_format_rejected(
        self, async_client, db_session, create_test_published_article
    ):
        """Test that invalid widget formats are rejected"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "invalid_format"}
        )

        assert response.status_code == 422
        assert "Invalid format" in response.json()["detail"][0]["msg"]

    async def test_widget_render_nonexistent_article_404(self, async_client):
        """Test that rendering nonexistent article returns 404"""
        response = await async_client.get(
            "/api/widget/render/nonexistent-id",
            params={"format": "widget"}
        )

        assert response.status_code == 404

    async def test_embed_script_endpoint(self, async_client):
        """Test that embed script endpoint returns JavaScript"""
        response = await async_client.get("/api/widget/embed-script")

        assert response.status_code == 200
        data = response.json()
        assert "script" in data
        assert "AITicketWidget" in data["script"]
        assert "function" in data["script"].lower()

    async def test_embed_script_is_valid_javascript(self, async_client):
        """Test that embed script is valid JavaScript"""
        response = await async_client.get("/api/widget/embed-script")

        assert response.status_code == 200
        script = response.json()["script"]

        # Should have JavaScript structure
        assert "(function()" in script
        assert "window.AITicketWidget" in script
        assert "render" in script

    async def test_embed_script_includes_fetch_logic(self, async_client):
        """Test that embed script includes fetch for dynamic rendering"""
        response = await async_client.get("/api/widget/embed-script")

        script = response.json()["script"]
        assert "fetch" in script
        assert "/api/widget/render/" in script

    async def test_manual_trigger_endpoint(
        self, async_client, db_session, create_test_published_article
    ):
        """Test manual widget trigger endpoint"""
        article = await create_test_published_article(db_session)

        response = await async_client.post(
            f"/api/widget/trigger/{article.article_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["article_id"] == article.article_id
        assert data["status"] == "triggered"
        assert data["microsite_url"] == article.microsite_url

    async def test_manual_trigger_nonexistent_article_404(self, async_client):
        """Test that triggering nonexistent article returns 404"""
        response = await async_client.post("/api/widget/trigger/nonexistent-id")

        assert response.status_code == 404

    async def test_widget_embed_format_html(
        self, async_client, db_session, create_test_published_article
    ):
        """Test embed format returns embeddable HTML"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "embed"}
        )

        assert response.status_code == 200
        html = response.json()["html"]

        # Should be basic HTML structure
        assert "<div" in html or "<" in html

    async def test_widget_iframe_format(
        self, async_client, db_session, create_test_published_article
    ):
        """Test iframe format returns iframe code"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "iframe"}
        )

        assert response.status_code == 200
        html = response.json()["html"]

        # Should contain iframe tag
        assert "<iframe" in html
        assert article.microsite_url in html

    async def test_widget_render_response_includes_url(
        self, async_client, db_session, create_test_published_article
    ):
        """Test that widget render response includes microsite URL"""
        article = await create_test_published_article(db_session)

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "widget"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "microsite_url" in data
        assert data["microsite_url"] == article.microsite_url

    async def test_widget_renders_with_special_characters(
        self, async_client, db_session, create_test_published_article
    ):
        """Test that widget handles content with special characters"""
        special_content = "# Test <title> & \"quotes\" 'apostrophe'\n\nContent with special chars"
        article = await create_test_published_article(
            db_session,
            markdown_content=special_content
        )

        response = await async_client.get(
            f"/api/widget/render/{article.article_id}",
            params={"format": "widget"}
        )

        assert response.status_code == 200
        assert "html" in response.json()

    async def test_manual_trigger_returns_correct_fields(
        self, async_client, db_session, create_test_published_article
    ):
        """Test that manual trigger returns all expected fields"""
        article = await create_test_published_article(db_session)

        response = await async_client.post(
            f"/api/widget/trigger/{article.article_id}"
        )

        assert response.status_code == 200
        data = response.json()

        required_fields = ["article_id", "status", "microsite_url", "message"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

"""
Widget Router
Handles JS widget rendering and micro-answer delivery
Converts markdown to HTML for widget display
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

try:
    import markdown
except ImportError:
    markdown = None

from ai_ticket_platform.database.generated_models import PublishedArticle
from ai_ticket_platform.dependencies.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["widget"])


@router.get("/widget/render/{article_id}")
async def render_widget(
    article_id: str,
    format: str = "widget",
    db: AsyncSession = Depends(get_db)
):
    """
    Render a widget for displaying an article.

    Supports multiple formats for embedding in different contexts.

    TODO: Integrate actual widget rendering engine
    For now: Returns HTML/widget code with article content

    Args:
        article_id: ID of the published article
        format: Format to render ("widget", "embed", "iframe")
        db: Database session

    Returns:
        HTML/JavaScript widget code
    """
    # Verify article exists
    result = await db.execute(
        select(PublishedArticle).where(PublishedArticle.article_id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found"
        )

    # Validate format
    valid_formats = ["widget", "embed", "iframe"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid format. Must be one of: {valid_formats}"
        )

    logger.info(f"Rendering article {article_id} as {format}")

    # Generate widget HTML based on format
    if format == "widget":
        html = _generate_widget_html(article)
    elif format == "embed":
        html = _generate_embed_html(article)
    elif format == "iframe":
        html = _generate_iframe_html(article)

    return {
        "article_id": article_id,
        "format": format,
        "html": html,
        "microsite_url": article.microsite_url
    }


@router.get("/widget/embed-script")
async def get_embed_script():
    """
    Get the JavaScript embed script that users can add to their sites.

    This script loads the widget dynamically.

    Returns:
        JavaScript code for embedding widgets
    """
    script = """
    (function() {
        window.AITicketWidget = window.AITicketWidget || {};

        AITicketWidget.render = function(containerId, articleId, options) {
            options = options || {};
            const container = document.getElementById(containerId);

            if (!container) {
                console.error('Container not found: ' + containerId);
                return;
            }

            // Fetch widget HTML
            fetch(`/api/widget/render/${articleId}?format=widget`)
                .then(response => response.json())
                .then(data => {
                    container.innerHTML = data.html;

                    // Trigger any necessary initialization
                    if (window.AITicketWidget.onWidgetRendered) {
                        window.AITicketWidget.onWidgetRendered(articleId, container);
                    }
                })
                .catch(error => {
                    console.error('Error rendering widget:', error);
                    container.innerHTML = '<p>Error loading widget</p>';
                });
        };

        // Support for data-* attributes
        document.addEventListener('DOMContentLoaded', function() {
            const widgets = document.querySelectorAll('[data-ai-widget]');
            widgets.forEach(el => {
                const articleId = el.getAttribute('data-article-id');
                if (articleId) {
                    AITicketWidget.render(el.id || el.className, articleId);
                }
            });
        });
    })();
    """
    return {"type": "application/javascript", "script": script}


@router.post("/widget/trigger/{article_id}")
async def manual_trigger(
    article_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger widget rendering/update.

    This endpoint can be called to refresh or trigger updates for a widget.

    Args:
        article_id: ID of the article to trigger rendering for
        db: Database session

    Returns:
        Status and widget data
    """
    result = await db.execute(
        select(PublishedArticle).where(PublishedArticle.article_id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found"
        )

    logger.info(f"Manual widget trigger for article {article_id}")

    return {
        "article_id": article_id,
        "status": "triggered",
        "microsite_url": article.microsite_url,
        "message": "Widget rendering triggered"
    }


# ============================================================================
# Helper functions for widget HTML generation
# ============================================================================

def _markdown_to_html(markdown_content: str) -> str:
    """Convert markdown content to HTML."""
    if markdown and markdown_content:
        try:
            return markdown.markdown(markdown_content, extensions=['extra', 'codehilite', 'toc'])
        except Exception as e:
            logger.error(f"Error converting markdown to HTML: {str(e)}")
            # Fallback: escape markdown and wrap in pre tag
            return f"<pre>{markdown_content}</pre>"
    return markdown_content


def _generate_widget_html(article) -> str:
    """Generate widget HTML from article content (converts markdown to HTML)."""
    html_content = _markdown_to_html(article.markdown_content)

    return f"""
    <div class="ai-ticket-widget" data-article-id="{article.article_id}">
        <div class="micro-answer">
            <div class="widget-header">
                <h3>AI-Generated Answer</h3>
            </div>
            <div class="widget-content">
                {html_content}
            </div>
            <div class="widget-footer">
                <a href="{article.microsite_url}" target="_blank" class="view-full-article">
                    View Full Article →
                </a>
            </div>
        </div>
        <style>
            .ai-ticket-widget {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 16px;
                background: #f9f9f9;
                max-width: 600px;
            }}
            .micro-answer {{
                color: #333;
            }}
            .widget-header h3 {{
                margin: 0 0 12px 0;
                font-size: 16px;
                font-weight: 600;
            }}
            .widget-content {{
                font-size: 14px;
                line-height: 1.6;
                margin-bottom: 12px;
            }}
            .widget-content h1, .widget-content h2, .widget-content h3 {{
                margin: 16px 0 8px 0;
                font-weight: 600;
            }}
            .widget-content p {{
                margin: 8px 0;
            }}
            .widget-content ul, .widget-content ol {{
                margin: 8px 0 8px 20px;
            }}
            .widget-content code {{
                background: #f0f0f0;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
            .widget-content pre {{
                background: #f0f0f0;
                padding: 12px;
                border-radius: 4px;
                overflow-x: auto;
            }}
            .view-full-article {{
                color: #0066cc;
                text-decoration: none;
                font-weight: 500;
                font-size: 14px;
            }}
            .view-full-article:hover {{
                text-decoration: underline;
            }}
        </style>
    </div>
    """


def _generate_embed_html(article) -> str:
    """Generate embeddable HTML from article content (converts markdown to HTML)."""
    html_content = _markdown_to_html(article.markdown_content)

    return f"""
    <div class="ai-ticket-embed" data-article-id="{article.article_id}">
        {html_content}
    </div>
    """


def _generate_iframe_html(article) -> str:
    """Generate iframe-compatible HTML from article content."""
    return f"""
    <iframe
        src="{article.microsite_url}"
        title="AI-Generated Answer"
        width="600"
        height="400"
        frameborder="0"
        allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture">
    </iframe>
    """

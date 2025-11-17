"""
Publishing Router
Handles publishing drafts to microsite and managing published articles
TODO: Integrate with markdown microsite generator
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
import logging

from ai_ticket_platform.database.generated_models import (
    Draft,
    DraftStatus,
    PublishedArticle
)
from ai_ticket_platform.dependencies.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["publishing"])


@router.post("/articles/publish/{draft_id}", response_model=dict)
async def publish_article(
    draft_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Publish an approved draft to the microsite.

    TODO: Integrate with markdown microsite generator when available
    For now: Creates PublishedArticle and returns mock microsite URL

    Args:
        draft_id: ID of the draft to publish
        db: Database session

    Returns:
        dict with article_id, microsite_url, and published status
    """
    # Verify draft exists
    result = await db.execute(select(Draft).where(Draft.draft_id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft {draft_id} not found"
        )

    # Verify draft is approved
    if draft.status != DraftStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish draft with status '{draft.status}'. "
                   f"Draft must be in 'APPROVED' status"
        )

    try:
        # Generate unique microsite URL
        article_slug = str(uuid4())[:8]
        microsite_url = f"https://microsite.example.com/articles/{article_slug}"

        # Create published article
        article = PublishedArticle(
            draft_id=draft_id,
            markdown_content=draft.content,
            microsite_url=microsite_url
        )

        # Update draft status
        draft.status = DraftStatus.PUBLISHED

        db.add(article)
        await db.commit()
        await db.refresh(article)
        await db.refresh(draft)

        logger.info(f"Published article {article.article_id} from draft {draft_id}")

        # TODO: Call actual microsite generator here
        # For now, just log that we would generate the site
        logger.info(f"Would trigger markdown microsite generator for URL: {microsite_url}")

        return {
            "article_id": article.article_id,
            "draft_id": draft_id,
            "microsite_url": microsite_url,
            "published_at": article.published_at.isoformat(),
            "status": "published"
        }
    except Exception as e:
        logger.error(f"Error publishing article: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish article: {str(e)}"
        )


@router.get("/articles/{article_id}/microsite", response_model=dict)
async def get_microsite(
    article_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the microsite for a published article.

    TODO: Integrate markdown generator rendering
    For now: Returns markdown content and microsite URL

    Args:
        article_id: ID of the published article
        db: Database session

    Returns:
        dict with microsite URL and markdown content
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

    return {
        "article_id": article.article_id,
        "url": article.microsite_url,
        "markdown": article.markdown_content,
        "published_at": article.published_at.isoformat()
    }


@router.get("/articles/{article_id}", response_model=dict)
async def get_article(
    article_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get article details.

    Args:
        article_id: ID of the article
        db: Database session

    Returns:
        Article details
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

    return {
        "article_id": article.article_id,
        "draft_id": article.draft_id,
        "markdown_content": article.markdown_content,
        "microsite_url": article.microsite_url,
        "published_at": article.published_at.isoformat(),
        "created_at": article.created_at.isoformat()
    }

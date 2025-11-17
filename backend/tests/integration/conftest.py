"""
Integration test fixtures
Provides helper functions and fixtures for integration tests

All fixtures are marked with @pytest_asyncio.fixture to support async test methods.
Fixtures automatically create and persist test data to Docker MySQL database.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy import select

from ai_ticket_platform.database.generated_models import (
    Ticket,
    TicketStatus,
    Draft,
    DraftStatus,
    Approval,
    ApprovalStatus,
    PublishedArticle,
)


# ============================================================================
# Ticket Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def create_test_ticket():
    """Factory fixture to create test tickets"""
    async def _create(db_session, **kwargs):
        ticket = Ticket(
            title=kwargs.get("title", "Test Ticket"),
            content=kwargs.get("content", "Test ticket content"),
            status=kwargs.get("status", TicketStatus.UPLOADED),
        )
        db_session.add(ticket)
        await db_session.commit()
        await db_session.refresh(ticket)
        return ticket

    return _create


@pytest_asyncio.fixture
async def sample_ticket(db_session, create_test_ticket):
    """Provide a sample ticket for tests"""
    return await create_test_ticket(db_session)


# ============================================================================
# Draft Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def create_test_draft():
    """Factory fixture to create test drafts"""
    async def _create(db_session, **kwargs):
        ticket = kwargs.get("ticket")
        if not ticket:
            ticket = Ticket(
                title="Test Ticket for Draft",
                content="Test content",
                status=TicketStatus.UPLOADED
            )
            db_session.add(ticket)
            await db_session.commit()
            await db_session.refresh(ticket)

        draft = Draft(
            ticket_id=ticket.ticket_id,
            content=kwargs.get("content", "# Test Draft\n\nThis is test draft content"),
            status=kwargs.get("status", DraftStatus.PENDING),
        )
        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)
        return draft

    return _create


@pytest_asyncio.fixture
async def sample_draft(db_session, create_test_draft):
    """Provide a sample draft for tests"""
    return await create_test_draft(db_session)


# ============================================================================
# Approval Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def create_test_approval():
    """Factory fixture to create test approvals"""
    async def _create(db_session, **kwargs):
        draft = kwargs.get("draft")
        if not draft:
            ticket = Ticket(
                title="Test Ticket for Approval",
                content="Test content",
                status=TicketStatus.UPLOADED
            )
            db_session.add(ticket)
            await db_session.commit()
            await db_session.refresh(ticket)

            draft = Draft(
                ticket_id=ticket.ticket_id,
                content="# Test Draft",
                status=DraftStatus.AWAITING_APPROVAL
            )
            db_session.add(draft)
            await db_session.commit()
            await db_session.refresh(draft)

        approval = Approval(
            draft_id=draft.draft_id,
            slack_message_ts=kwargs.get("slack_message_ts", "mock.ts.123"),
            status=kwargs.get("status", ApprovalStatus.PENDING),
            reviewer_id=kwargs.get("reviewer_id", None),
        )
        db_session.add(approval)
        await db_session.commit()
        await db_session.refresh(approval)
        return approval

    return _create


@pytest_asyncio.fixture
async def sample_approval(db_session, create_test_approval):
    """Provide a sample approval for tests"""
    return await create_test_approval(db_session)


# ============================================================================
# Published Article Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def create_test_published_article():
    """Factory fixture to create test published articles"""
    async def _create(db_session, **kwargs):
        draft = kwargs.get("draft")
        if not draft:
            ticket = Ticket(
                title="Test Ticket for Article",
                content="Test content",
                status=TicketStatus.UPLOADED
            )
            db_session.add(ticket)
            await db_session.commit()
            await db_session.refresh(ticket)

            draft = Draft(
                ticket_id=ticket.ticket_id,
                content="# Test Article\n\nPublished content",
                status=DraftStatus.APPROVED
            )
            db_session.add(draft)
            await db_session.commit()
            await db_session.refresh(draft)

        article = PublishedArticle(
            draft_id=draft.draft_id,
            markdown_content=kwargs.get("markdown_content", "# Test Article\n\nPublished content"),
            microsite_url=kwargs.get("microsite_url", f"https://microsite.test/articles/{uuid4()}"),
        )
        db_session.add(article)
        await db_session.commit()
        await db_session.refresh(article)
        return article

    return _create


@pytest_asyncio.fixture
async def sample_published_article(db_session, create_test_published_article):
    """Provide a sample published article for tests"""
    return await create_test_published_article(db_session)

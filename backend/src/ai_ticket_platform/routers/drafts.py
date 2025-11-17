"""
Draft Management Router
Handles draft generation, sending for approval, and state transitions
Integrates with Slack for approval workflow
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import logging

from ai_ticket_platform.database.generated_models import (
    Ticket,
    Draft,
    DraftStatus,
    Approval,
    ApprovalStatus
)
from ai_ticket_platform.dependencies.database import get_db
from ai_ticket_platform.dependencies.settings import get_app_settings
from ai_ticket_platform.core.clients.slack import Slack

logger = logging.getLogger(__name__)
router = APIRouter(tags=["drafts"])


class ApprovalResponse(BaseModel):
    """Model for approval responses"""
    action: str  # "approved" or "needs_edit"
    feedback: str = ""


@router.post("/drafts/generate", response_model=dict)
async def generate_draft(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a draft from a ticket.

    TODO: Implement actual AI draft generation (Flowgentic integration)
    For now: Creates a draft with mock content

    Args:
        ticket_id: ID of the ticket to generate draft from
        db: Database session

    Returns:
        dict with draft_id and status
    """
    # Verify ticket exists
    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )

    try:
        # TODO: Call actual AI service when teammates implement
        # For now, generate mock draft content
        mock_content = f"""# {ticket.title}

## Summary
This is a generated draft based on the ticket: {ticket.title}

## Details
{ticket.content[:1000]}...

## Proposed Solution
This is a placeholder for the AI-generated draft content.

---
*Generated from ticket {ticket_id}*
"""

        draft = Draft(
            ticket_id=ticket_id,
            content=mock_content,
            status=DraftStatus.PENDING
        )

        db.add(draft)
        await db.commit()
        await db.refresh(draft)

        logger.info(f"Generated draft {draft.draft_id} from ticket {ticket_id}")

        return {
            "draft_id": draft.draft_id,
            "status": "pending",
            "ticket_id": ticket_id
        }
    except Exception as e:
        logger.error(f"Error generating draft: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate draft: {str(e)}"
        )


@router.post("/drafts/{draft_id}/send-for-approval", response_model=dict)
async def send_draft_for_approval(
    draft_id: str,
    slack_channel: str = "general",
    db: AsyncSession = Depends(get_db),
    settings = Depends(get_app_settings)
):
    """
    Send a draft for approval (creates an approval record and sends to Slack).

    Args:
        draft_id: ID of the draft
        slack_channel: Slack channel to send approval message to
        db: Database session
        settings: Application settings with Slack configuration

    Returns:
        dict with approval_id and message_sent status
    """
    # Verify draft exists
    result = await db.execute(select(Draft).where(Draft.draft_id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft {draft_id} not found"
        )

    try:
        # Check if draft is already approved or needs editing
        if draft.status not in [DraftStatus.PENDING, DraftStatus.NEEDS_EDIT]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot send draft for approval. Current status: {draft.status}"
            )

        # Create approval record
        approval = Approval(
            draft_id=draft_id,
            slack_message_ts="pending",
            status=ApprovalStatus.PENDING
        )

        # Update draft status
        draft.status = DraftStatus.AWAITING_APPROVAL

        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        await db.refresh(draft)

        logger.info(f"Sent draft {draft_id} for approval (approval_id: {approval.approval_id})")

        # Send to Slack
        slack_message_ts = None
        slack_sent = False

        try:
            slack = Slack(slack_bot_token=settings.SLACK_BOT_TOKEN)
            result = slack.send_new_article_proposal(
                slack_channel_id=settings.SLACK_CHANNEL_ID,
                url=f"https://app.example.com/draft/{draft_id}",
                content=draft.content[:500]  # Send first 500 chars of draft
            )

            if result:
                slack_message_ts = result[1]  # second element is message timestamp
                slack_sent = True
                approval.slack_message_ts = slack_message_ts
                await db.commit()
                logger.info(f"Slack message sent for approval {approval.approval_id}")
            else:
                logger.warning(f"Failed to send Slack message for approval {approval.approval_id}")
        except Exception as slack_error:
            logger.error(f"Slack integration error: {str(slack_error)}")
            # Don't fail the approval flow if Slack fails
            slack_sent = False

        return {
            "approval_id": approval.approval_id,
            "draft_id": draft_id,
            "status": "awaiting_approval",
            "message_sent": slack_sent,
            "slack_channel": slack_channel,
            "slack_message_ts": slack_message_ts
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error sending draft for approval: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send draft for approval: {str(e)}"
        )


@router.post("/approvals/{approval_id}/handle-response", response_model=dict)
async def handle_approval_response(
    approval_id: str,
    response: ApprovalResponse,
    db: AsyncSession = Depends(get_db),
    settings = Depends(get_app_settings)
):
    """
    Handle approval response (approved or needs_edit).

    Sends confirmation to Slack when approved.

    Args:
        approval_id: ID of the approval
        response: ApprovalResponse with action and feedback
        db: Database session
        settings: Application settings with Slack configuration

    Returns:
        Updated approval with new status
    """
    # Validate action
    valid_actions = ["approved", "needs_edit"]
    if response.action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid action. Must be one of: {valid_actions}"
        )

    # Verify approval exists
    result = await db.execute(select(Approval).where(Approval.approval_id == approval_id))
    approval = result.scalar_one_or_none()

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    try:
        # Get associated draft
        draft_result = await db.execute(select(Draft).where(Draft.draft_id == approval.draft_id))
        draft = draft_result.scalar_one_or_none()

        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Draft {approval.draft_id} not found"
            )

        # Handle the response
        if response.action == "approved":
            approval.status = ApprovalStatus.APPROVED
            draft.status = DraftStatus.APPROVED
        elif response.action == "needs_edit":
            approval.status = ApprovalStatus.NEEDS_EDIT
            draft.status = DraftStatus.NEEDS_EDIT

        # Store feedback if provided
        if response.feedback:
            approval.response_payload = {"feedback": response.feedback, "action": response.action}

        await db.commit()
        await db.refresh(approval)
        await db.refresh(draft)

        logger.info(
            f"Approval {approval_id} set to {response.action} "
            f"(Draft {draft.draft_id} status: {draft.status})"
        )

        # Send Slack confirmation if approved
        if response.action == "approved":
            try:
                slack = Slack(slack_bot_token=settings.SLACK_BOT_TOKEN)
                slack.send_confirmation_message(
                    slack_channel_id=settings.SLACK_CHANNEL_ID,
                    url=f"https://app.example.com/article/{draft.draft_id}"
                )
                logger.info(f"Slack confirmation sent for approval {approval_id}")
            except Exception as slack_error:
                logger.error(f"Failed to send Slack confirmation: {str(slack_error)}")
                # Don't fail the approval if Slack fails

        return {
            "approval_id": approval.approval_id,
            "draft_id": approval.draft_id,
            "action": response.action,
            "approval_status": approval.status,
            "draft_status": draft.status,
            "feedback": response.feedback
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error handling approval response: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle approval response: {str(e)}"
        )


@router.get("/drafts/{draft_id}", response_model=dict)
async def get_draft(
    draft_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a draft by ID.

    Args:
        draft_id: ID of the draft
        db: Database session

    Returns:
        Draft details
    """
    result = await db.execute(select(Draft).where(Draft.draft_id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft {draft_id} not found"
        )

    return {
        "draft_id": draft.draft_id,
        "ticket_id": draft.ticket_id,
        "content": draft.content,
        "status": draft.status,
        "created_at": draft.created_at.isoformat(),
        "updated_at": draft.updated_at.isoformat()
    }

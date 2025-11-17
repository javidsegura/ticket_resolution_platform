"""
Integration tests for Slack approval flow

Simulate Slack approval events and confirm state transitions to "Approved" / "Needs edit"
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import select

from ai_ticket_platform.database.generated_models import (
    Draft,
    DraftStatus,
    Approval,
    ApprovalStatus,
)


@pytest.mark.asyncio
class TestApprovalFlow:
    """Tests for Slack approval flow and state transitions"""

    async def test_send_draft_for_approval(self, async_client, db_session, create_test_draft):
        """Draft can be sent for approval"""
        draft = await create_test_draft(db_session, status=DraftStatus.PENDING)

        # Mock Slack client to avoid actual API calls
        with patch('ai_ticket_platform.routers.drafts.Slack') as mock_slack_class:
            mock_slack_instance = MagicMock()
            mock_slack_class.return_value = mock_slack_instance
            mock_slack_instance.send_new_article_proposal.return_value = ('thread_ts', 'msg_ts_123')

            response = await async_client.post(
                f"/api/drafts/{draft.draft_id}/send-for-approval",
                json={"slack_channel": "general"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "approval_id" in data
        assert data["draft_id"] == draft.draft_id
        assert data["status"] == "awaiting_approval"
        assert data["message_sent"] is True
        assert data["slack_message_ts"] == "msg_ts_123"

        # Verify draft status changed to AWAITING_APPROVAL
        result = await db_session.execute(
            select(Draft).where(Draft.draft_id == draft.draft_id)
        )
        updated_draft = result.scalar_one_or_none()
        assert updated_draft.status == DraftStatus.AWAITING_APPROVAL

        # Verify Slack was called with correct parameters
        mock_slack_instance.send_new_article_proposal.assert_called_once()

    async def test_approval_state_transition_to_approved(
        self, async_client, db_session, create_test_approval
    ):
        """Approval state transitions to APPROVED"""
        approval = await create_test_approval(db_session)

        # Mock Slack client for confirmation message
        with patch('ai_ticket_platform.routers.drafts.Slack') as mock_slack_class:
            mock_slack_instance = MagicMock()
            mock_slack_class.return_value = mock_slack_instance
            mock_slack_instance.send_confirmation_message.return_value = None

            response = await async_client.post(
                f"/api/approvals/{approval.approval_id}/handle-response",
                json={"action": "approved", "feedback": "Looks good!"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "approved"
        assert data["approval_status"] == ApprovalStatus.APPROVED.value
        assert data["draft_status"] == DraftStatus.APPROVED.value

        # Verify Slack was called
        mock_slack_instance.send_confirmation_message.assert_called_once()

        # Verify in database
        approval_result = await db_session.execute(
            select(Approval).where(Approval.approval_id == approval.approval_id)
        )
        updated_approval = approval_result.scalar_one_or_none()
        assert updated_approval.status == ApprovalStatus.APPROVED

        draft_result = await db_session.execute(
            select(Draft).where(Draft.draft_id == approval.draft_id)
        )
        updated_draft = draft_result.scalar_one_or_none()
        assert updated_draft.status == DraftStatus.APPROVED

    async def test_approval_state_transition_to_needs_edit(
        self, async_client, db_session, create_test_approval
    ):
        """Approval state transitions to NEEDS_EDIT"""
        approval = await create_test_approval(db_session)

        response = await async_client.post(
            f"/api/approvals/{approval.approval_id}/handle-response",
            json={"action": "needs_edit", "feedback": "Needs revision"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "needs_edit"
        assert data["approval_status"] == ApprovalStatus.NEEDS_EDIT.value
        assert data["draft_status"] == DraftStatus.NEEDS_EDIT.value

        # Verify in database
        approval_result = await db_session.execute(
            select(Approval).where(Approval.approval_id == approval.approval_id)
        )
        updated_approval = approval_result.scalar_one_or_none()
        assert updated_approval.status == ApprovalStatus.NEEDS_EDIT

        draft_result = await db_session.execute(
            select(Draft).where(Draft.draft_id == approval.draft_id)
        )
        updated_draft = draft_result.scalar_one_or_none()
        assert updated_draft.status == DraftStatus.NEEDS_EDIT

    async def test_approval_invalid_action_rejected(self, async_client, create_test_approval, db_session):
        """Invalid approval actions are rejected"""
        approval = await create_test_approval(db_session)

        response = await async_client.post(
            f"/api/approvals/{approval.approval_id}/handle-response",
            json={"action": "invalid_action", "feedback": ""}
        )

        assert response.status_code == 422

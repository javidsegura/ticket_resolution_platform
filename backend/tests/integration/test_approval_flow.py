"""
Integration tests for Slack approval flow

Tests the complete approval workflow:
1. Draft sent for approval → creates Approval record → changes Draft status to AWAITING_APPROVAL
2. Slack button click (or direct API call) → state transitions to APPROVED or NEEDS_EDIT
3. Validates that arguments are passed/rejected correctly
"""

import pytest
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

    async def test_send_draft_for_approval_creates_approval_record(
        self, async_client, db_session, create_test_draft
    ):
        """Test that sending draft for approval creates an Approval record"""
        draft = await create_test_draft(db_session, status=DraftStatus.PENDING)

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

        # Verify in database
        result = await db_session.execute(
            select(Approval).where(Approval.approval_id == data["approval_id"])
        )
        approval = result.scalar_one_or_none()

        assert approval is not None
        assert approval.draft_id == draft.draft_id
        assert approval.status == ApprovalStatus.PENDING

    async def test_send_draft_for_approval_changes_draft_status(
        self, async_client, db_session, create_test_draft
    ):
        """Test that draft status changes to AWAITING_APPROVAL"""
        draft = await create_test_draft(db_session, status=DraftStatus.PENDING)
        original_status = draft.status

        await async_client.post(
            f"/api/drafts/{draft.draft_id}/send-for-approval",
            json={"slack_channel": "general"}
        )

        # Refresh draft from database
        result = await db_session.execute(
            select(Draft).where(Draft.draft_id == draft.draft_id)
        )
        updated_draft = result.scalar_one_or_none()

        assert updated_draft.status == DraftStatus.AWAITING_APPROVAL
        assert updated_draft.status != original_status

    async def test_cannot_send_already_approved_draft_for_approval(
        self, async_client, db_session, create_test_draft
    ):
        """Test that approved drafts cannot be sent for approval"""
        draft = await create_test_draft(db_session, status=DraftStatus.APPROVED)

        response = await async_client.post(
            f"/api/drafts/{draft.draft_id}/send-for-approval",
            json={"slack_channel": "general"}
        )

        assert response.status_code == 400
        assert "Cannot send draft for approval" in response.json()["detail"]

    async def test_send_draft_for_approval_nonexistent_draft(self, async_client):
        """Test that sending nonexistent draft returns 404"""
        response = await async_client.post(
            "/api/drafts/nonexistent-id/send-for-approval",
            json={"slack_channel": "general"}
        )

        assert response.status_code == 404

    @pytest.mark.parametrize("action,expected_approval_status,expected_draft_status", [
        ("approved", ApprovalStatus.APPROVED, DraftStatus.APPROVED),
        ("needs_edit", ApprovalStatus.NEEDS_EDIT, DraftStatus.NEEDS_EDIT),
    ])
    async def test_approval_state_transitions(
        self, async_client, db_session, create_test_approval,
        action, expected_approval_status, expected_draft_status
    ):
        """
        Test that approval actions correctly transition state.
        Validates arguments are passed correctly.
        """
        approval = await create_test_approval(db_session)

        response = await async_client.post(
            f"/api/approvals/{approval.approval_id}/handle-response",
            json={"action": action, "feedback": "Looks good!"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == action
        assert data["approval_status"] == expected_approval_status.value
        assert data["draft_status"] == expected_draft_status.value

        # Verify in database
        approval_result = await db_session.execute(
            select(Approval).where(Approval.approval_id == approval.approval_id)
        )
        updated_approval = approval_result.scalar_one_or_none()
        assert updated_approval.status == expected_approval_status

        draft_result = await db_session.execute(
            select(Draft).where(Draft.draft_id == approval.draft_id)
        )
        updated_draft = draft_result.scalar_one_or_none()
        assert updated_draft.status == expected_draft_status

    async def test_approval_with_feedback(self, async_client, db_session, create_test_approval):
        """Test that approval feedback is stored"""
        approval = await create_test_approval(db_session)
        feedback_text = "Please add more details to the conclusion"

        response = await async_client.post(
            f"/api/approvals/{approval.approval_id}/handle-response",
            json={"action": "needs_edit", "feedback": feedback_text}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["feedback"] == feedback_text

        # Verify feedback in database
        result = await db_session.execute(
            select(Approval).where(Approval.approval_id == approval.approval_id)
        )
        updated_approval = result.scalar_one_or_none()
        assert updated_approval.response_payload is not None

    async def test_approval_invalid_action_rejected(self, async_client, create_test_approval, db_session):
        """Test that invalid approval actions are rejected"""
        approval = await create_test_approval(db_session)

        response = await async_client.post(
            f"/api/approvals/{approval.approval_id}/handle-response",
            json={"action": "invalid_action", "feedback": ""}
        )

        # Should get validation error (422)
        assert response.status_code == 422
        assert "Invalid action" in response.json()["detail"][0]["msg"]

    async def test_approval_nonexistent_approval_not_found(self, async_client):
        """Test that nonexistent approval returns 404"""
        response = await async_client.post(
            "/api/approvals/nonexistent-id/handle-response",
            json={"action": "approved", "feedback": ""}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_approval_empty_feedback_allowed(self, async_client, db_session, create_test_approval):
        """Test that approvals can be made without feedback"""
        approval = await create_test_approval(db_session)

        response = await async_client.post(
            f"/api/approvals/{approval.approval_id}/handle-response",
            json={"action": "approved"}  # No feedback provided
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == ApprovalStatus.APPROVED.value

    async def test_resend_rejected_draft_for_approval(
        self, async_client, db_session, create_test_draft
    ):
        """Test that rejected drafts can be resubmitted for approval"""
        draft = await create_test_draft(db_session, status=DraftStatus.PENDING)

        # First approval attempt
        response1 = await async_client.post(
            f"/api/drafts/{draft.draft_id}/send-for-approval",
            json={"slack_channel": "general"}
        )
        approval_id_1 = response1.json()["approval_id"]

        # Reject the draft
        await async_client.post(
            f"/api/approvals/{approval_id_1}/handle-response",
            json={"action": "needs_edit", "feedback": "Needs work"}
        )

        # Resubmit for approval (should work)
        response2 = await async_client.post(
            f"/api/drafts/{draft.draft_id}/send-for-approval",
            json={"slack_channel": "general"}
        )

        # Since draft is now in NEEDS_EDIT, this should work per our logic
        # The endpoint allows PENDING and NEEDS_EDIT status
        assert response2.status_code == 200
        approval_id_2 = response2.json()["approval_id"]

        # Verify different approval IDs
        assert approval_id_1 != approval_id_2

    async def test_approval_response_includes_all_fields(
        self, async_client, db_session, create_test_approval
    ):
        """Test that approval response includes all required fields"""
        approval = await create_test_approval(db_session)

        response = await async_client.post(
            f"/api/approvals/{approval.approval_id}/handle-response",
            json={"action": "approved", "feedback": "Looks good"}
        )

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "approval_id", "draft_id", "action",
            "approval_status", "draft_status", "feedback"
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    async def test_argument_passing_validation(
        self, async_client, db_session, create_test_approval
    ):
        """
        Test that arguments passed to approval endpoint are correctly validated.
        This directly tests the issue requirement: "test in slack that the passed
        arguments are passed or rejected"
        """
        approval = await create_test_approval(db_session)

        test_cases = [
            {
                "name": "Valid approved action",
                "payload": {"action": "approved", "feedback": "OK"},
                "expected_status": 200,
                "should_pass": True
            },
            {
                "name": "Valid needs_edit action",
                "payload": {"action": "needs_edit", "feedback": "Revise"},
                "expected_status": 200,
                "should_pass": True
            },
            {
                "name": "Invalid action value",
                "payload": {"action": "reject", "feedback": "No"},
                "expected_status": 422,
                "should_pass": False
            },
            {
                "name": "Missing action field",
                "payload": {"feedback": "No action"},
                "expected_status": 422,
                "should_pass": False
            },
        ]

        for test_case in test_cases:
            response = await async_client.post(
                f"/api/approvals/{approval.approval_id}/handle-response",
                json=test_case["payload"]
            )

            assert response.status_code == test_case["expected_status"], \
                f"Test '{test_case['name']}' failed: expected {test_case['expected_status']}, got {response.status_code}"

            if test_case["should_pass"]:
                assert response.status_code == 200
                assert "approval_status" in response.json()
            else:
                assert response.status_code == 422

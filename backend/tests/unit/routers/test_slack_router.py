import pytest
from unittest.mock import MagicMock, patch

from ai_ticket_platform.routers.slack import (
	send_slack_message,
	send_article_proposal,
	send_approval_confirmation,
	receive_slack_proposal_answer,
	cheeck_backend_health_endpoint,
)


@pytest.fixture
def mock_settings():
	"""Mock application settings with Slack credentials"""
	settings = MagicMock()
	settings.SLACK_BOT_TOKEN = "xoxb-test-token"
	settings.SLACK_CHANNEL_ID = "C12345678"
	return settings


@pytest.mark.asyncio
async def test_send_slack_message_success(mock_settings):
	"""Test successful Slack message send"""
	message = "Test message"

	with patch("ai_ticket_platform.routers.slack.Slack") as mock_slack_class:
		mock_slack = MagicMock()
		mock_slack.send_channel_message.return_value = ("C12345678", "1234567890.123456")
		mock_slack_class.return_value = mock_slack

		result = await send_slack_message(mock_settings, message)

		assert result["status"] == "success"
		assert result["channel_id"] == "C12345678"
		assert result["message_id"] == "1234567890.123456"

		# Verify Slack client was initialized with correct token
		mock_slack_class.assert_called_once_with(slack_bot_token="xoxb-test-token")

		# Verify message was sent
		mock_slack.send_channel_message.assert_called_once_with(
			message=message, slack_channel_id="C12345678"
		)


@pytest.mark.asyncio
async def test_send_slack_message_returns_none(mock_settings):
	"""Test Slack message send when API returns None"""
	message = "Test message"

	with patch("ai_ticket_platform.routers.slack.Slack") as mock_slack_class:
		mock_slack = MagicMock()
		mock_slack.send_channel_message.return_value = None
		mock_slack_class.return_value = mock_slack

		result = await send_slack_message(mock_settings, message)

		assert result["status"] == "error"
		assert "Failed to send Slack message" in result["message"]


@pytest.mark.asyncio
async def test_send_slack_message_exception(mock_settings):
	"""Test Slack message send with exception"""
	message = "Test message"

	with patch("ai_ticket_platform.routers.slack.Slack") as mock_slack_class:
		mock_slack = MagicMock()
		mock_slack.send_channel_message.side_effect = Exception("Connection failed")
		mock_slack_class.return_value = mock_slack

		result = await send_slack_message(mock_settings, message)

		assert result["status"] == "error"
		assert "Connection failed" in result["message"]


@pytest.mark.asyncio
async def test_send_article_proposal_success(mock_settings):
	"""Test successful article proposal send"""
	url = "https://example.com/article/123"
	content = "Check out this new article!"

	with patch("ai_ticket_platform.routers.slack.Slack") as mock_slack_class:
		mock_slack = MagicMock()
		mock_slack.send_new_article_proposal.return_value = (
			"C12345678",
			"1234567890.123456",
		)
		mock_slack_class.return_value = mock_slack

		result = await send_article_proposal(mock_settings, url, content)

		assert result["status"] == "success"
		assert result["channel_id"] == "C12345678"
		assert result["message_id"] == "1234567890.123456"

		# Verify proposal was sent with correct params
		mock_slack.send_new_article_proposal.assert_called_once_with(
			slack_channel_id="C12345678", url=url, content=content
		)


@pytest.mark.asyncio
async def test_send_article_proposal_returns_none(mock_settings):
	"""Test article proposal when API returns None"""
	url = "https://example.com/article/123"
	content = "Test content"

	with patch("ai_ticket_platform.routers.slack.Slack") as mock_slack_class:
		mock_slack = MagicMock()
		mock_slack.send_new_article_proposal.return_value = None
		mock_slack_class.return_value = mock_slack

		result = await send_article_proposal(mock_settings, url, content)

		assert result["status"] == "error"
		assert "Failed to send Slack message" in result["message"]


@pytest.mark.asyncio
async def test_send_article_proposal_exception(mock_settings):
	"""Test article proposal with exception"""
	url = "https://example.com/article/123"
	content = "Test content"

	with patch("ai_ticket_platform.routers.slack.Slack") as mock_slack_class:
		mock_slack = MagicMock()
		mock_slack.send_new_article_proposal.side_effect = Exception("Network error")
		mock_slack_class.return_value = mock_slack

		result = await send_article_proposal(mock_settings, url, content)

		assert result["status"] == "error"
		assert "Network error" in result["message"]


@pytest.mark.asyncio
async def test_send_approval_confirmation_success(mock_settings):
	"""Test successful approval confirmation send"""
	url = "https://example.com/article/123"

	with patch("ai_ticket_platform.routers.slack.Slack") as mock_slack_class:
		mock_slack = MagicMock()
		mock_slack.send_confirmation_message.return_value = (
			"C12345678",
			"1234567890.123456",
		)
		mock_slack_class.return_value = mock_slack

		result = await send_approval_confirmation(mock_settings, url)

		assert result["status"] == "success"
		assert result["channel_id"] == "C12345678"
		assert result["message_id"] == "1234567890.123456"

		# Verify confirmation was sent
		mock_slack.send_confirmation_message.assert_called_once_with(
			slack_channel_id="C12345678", url=url
		)


@pytest.mark.asyncio
async def test_send_approval_confirmation_returns_none(mock_settings):
	"""Test approval confirmation when API returns None"""
	url = "https://example.com/article/123"

	with patch("ai_ticket_platform.routers.slack.Slack") as mock_slack_class:
		mock_slack = MagicMock()
		mock_slack.send_confirmation_message.return_value = None
		mock_slack_class.return_value = mock_slack

		result = await send_approval_confirmation(mock_settings, url)

		assert result["status"] == "error"
		assert "Failed to send Slack message" in result["message"]


@pytest.mark.asyncio
async def test_send_approval_confirmation_exception(mock_settings):
	"""Test approval confirmation with exception"""
	url = "https://example.com/article/123"

	with patch("ai_ticket_platform.routers.slack.Slack") as mock_slack_class:
		mock_slack = MagicMock()
		mock_slack.send_confirmation_message.side_effect = Exception("API error")
		mock_slack_class.return_value = mock_slack

		result = await send_approval_confirmation(mock_settings, url)

		assert result["status"] == "error"
		assert "API error" in result["message"]


@pytest.mark.asyncio
async def test_receive_slack_proposal_answer():
	"""Test receive slack proposal answer endpoint"""
	result = await receive_slack_proposal_answer()

	assert result == 0


@pytest.mark.asyncio
async def test_check_backend_health_endpoint():
	"""Test Slack health check endpoint"""
	result = await cheeck_backend_health_endpoint()

	assert result["response"] == "pong"

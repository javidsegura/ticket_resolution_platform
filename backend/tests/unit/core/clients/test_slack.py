"""Unit tests for Slack client."""

from unittest.mock import patch, MagicMock
from ai_ticket_platform.core.clients.slack import Slack


class TestSlackInit:
	"""Test Slack client initialization."""

	def test_slack_init_sets_token_and_headers(self):
		"""Test that Slack client initializes with token and headers."""
		slack = Slack(slack_bot_token="xoxb-test-token")

		assert slack.slack_bot_token == "xoxb-test-token"
		assert slack.headers["Authorization"] == "Bearer xoxb-test-token"
		assert slack.headers["Content-Type"] == "application/json"


class TestSendChannelMessage:
	"""Test send_channel_message method."""

	@patch("ai_ticket_platform.core.clients.slack.requests.post")
	def test_send_channel_message_success(self, mock_post):
		"""Test successful message sending."""
		mock_response = MagicMock()
		mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
		mock_post.return_value = mock_response

		slack = Slack(slack_bot_token="xoxb-test-token")
		result = slack.send_channel_message(
			message="Test message", slack_channel_id="C12345"
		)

		assert result == ("C12345", "1234567890.123456")
		mock_post.assert_called_once_with(
			"https://slack.com/api/chat.postMessage",
			headers={
				"Authorization": "Bearer xoxb-test-token",
				"Content-Type": "application/json",
			},
			json={"channel": "C12345", "text": "Test message"},
		)

	@patch("ai_ticket_platform.core.clients.slack.requests.post")
	def test_send_channel_message_failure(self, mock_post):
		"""Test message sending failure."""
		mock_response = MagicMock()
		mock_response.json.return_value = {"ok": False, "error": "channel_not_found"}
		mock_post.return_value = mock_response

		slack = Slack(slack_bot_token="xoxb-test-token")
		result = slack.send_channel_message(
			message="Test message", slack_channel_id="C12345"
		)

		assert result is None


class TestSendChannelBlockMessage:
	"""Test send_channel_block_message method."""

	@patch("ai_ticket_platform.core.clients.slack.requests.post")
	def test_send_channel_block_message_success(self, mock_post):
		"""Test successful block message sending."""
		mock_response = MagicMock()
		mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
		mock_post.return_value = mock_response

		blocks = [
			{
				"type": "section",
				"text": {"type": "plain_text", "text": "Hello world"},
			}
		]

		slack = Slack(slack_bot_token="xoxb-test-token")
		result = slack.send_channel_block_message(
			blocks=blocks, slack_channel_id="C12345"
		)

		assert result == ("C12345", "1234567890.123456")
		mock_post.assert_called_once_with(
			"https://slack.com/api/chat.postMessage",
			headers={
				"Authorization": "Bearer xoxb-test-token",
				"Content-Type": "application/json",
			},
			json={"channel": "C12345", "blocks": blocks},
		)

	@patch("ai_ticket_platform.core.clients.slack.requests.post")
	def test_send_channel_block_message_failure(self, mock_post):
		"""Test block message sending failure."""
		mock_response = MagicMock()
		mock_response.json.return_value = {"ok": False, "error": "invalid_blocks"}
		mock_post.return_value = mock_response

		blocks = [{"type": "invalid"}]

		slack = Slack(slack_bot_token="xoxb-test-token")
		result = slack.send_channel_block_message(
			blocks=blocks, slack_channel_id="C12345"
		)

		assert result is None


class TestSendConfirmationMessage:
	"""Test send_confirmation_message method."""

	@patch.object(Slack, "send_channel_block_message")
	def test_send_confirmation_message_calls_block_message(
		self, mock_send_block_message
	):
		"""Test that confirmation message calls send_channel_block_message."""
		mock_send_block_message.return_value = ("C12345", "1234567890.123456")

		slack = Slack(slack_bot_token="xoxb-test-token")
		result = slack.send_confirmation_message(
			slack_channel_id="C12345", url="https://example.com/article"
		)

		assert result == ("C12345", "1234567890.123456")
		mock_send_block_message.assert_called_once()

		# Verify the blocks structure
		call_args = mock_send_block_message.call_args
		blocks = call_args.kwargs["blocks"]
		assert len(blocks) == 4
		assert blocks[0]["type"] == "header"
		assert "Success" in blocks[0]["text"]["text"]


class TestSendNewArticleProposal:
	"""Test send_new_article_proposal method."""

	@patch.object(Slack, "send_channel_block_message")
	def test_send_new_article_proposal_calls_block_message(
		self, mock_send_block_message
	):
		"""Test that new article proposal calls send_channel_block_message."""
		mock_send_block_message.return_value = ("C12345", "1234567890.123456")

		slack = Slack(slack_bot_token="xoxb-test-token")
		result = slack.send_new_article_proposal(
			slack_channel_id="C12345",
			url="https://example.com/article",
			content="Article content here",
		)

		assert result == ("C12345", "1234567890.123456")
		mock_send_block_message.assert_called_once()

		# Verify the blocks structure
		call_args = mock_send_block_message.call_args
		blocks = call_args.kwargs["blocks"]
		assert len(blocks) == 4
		assert blocks[0]["type"] == "header"
		assert "Zeffo" in blocks[0]["text"]["text"]
		assert blocks[2]["elements"][0]["elements"][0]["text"] == "Article content here"

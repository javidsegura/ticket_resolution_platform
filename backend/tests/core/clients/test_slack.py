from types import SimpleNamespace

import pytest

from ai_ticket_platform.core.clients import slack as slack_module  # type: ignore[import]
from ai_ticket_platform.core.clients.slack import Slack  # type: ignore[import]


class DummyResponse:
	def __init__(self, payload: dict):
		self._payload = payload

	def json(self):
		return self._payload


def test_send_channel_message_success(monkeypatch: pytest.MonkeyPatch):
	captured = SimpleNamespace(url=None, headers=None, payload=None)

	def fake_post(url, headers, json):
		captured.url = url
		captured.headers = headers
		captured.payload = json
		return DummyResponse({"ok": True, "ts": "123.456"})

	monkeypatch.setattr(slack_module.requests, "post", fake_post)

	client = Slack("token")
	result = client.send_channel_message("hello world", "C123")

	assert captured.url == "https://slack.com/api/chat.postMessage"
	assert captured.headers["Authorization"] == "Bearer token"
	assert captured.payload == {"channel": "C123", "text": "hello world"}
	assert result == ("C123", "123.456")


def test_send_channel_message_failure_returns_none(monkeypatch: pytest.MonkeyPatch):
	def fake_post(url, headers, json):
		return DummyResponse({"ok": False, "error": "channel_not_found"})

	monkeypatch.setattr(slack_module.requests, "post", fake_post)

	client = Slack("token")
	result = client.send_channel_message("hello world", "C123")

	assert result is None


def test_send_confirmation_message_builds_expected_blocks(monkeypatch: pytest.MonkeyPatch):
	client = Slack("token")

	captured = SimpleNamespace(blocks=None, channel=None)

	def fake_send_block(blocks, slack_channel_id):
		captured.blocks = blocks
		captured.channel = slack_channel_id
		return slack_channel_id, "789.101"

	monkeypatch.setattr(client, "send_channel_block_message", fake_send_block)

	result = client.send_confirmation_message("C999", "https://example.com/articles/1")

	assert result == ("C999", "789.101")
	assert captured.channel == "C999"
	assert captured.blocks[0]["type"] == "header"
	assert captured.blocks[-1]["elements"][0]["url"] == "https://example.com/articles/1"


def test_send_new_article_proposal_includes_content(monkeypatch: pytest.MonkeyPatch):
	client = Slack("token")

	captured = SimpleNamespace(blocks=None)

	def fake_send_block(blocks, slack_channel_id):
		captured.blocks = blocks
		return slack_channel_id, "333.444"

	monkeypatch.setattr(client, "send_channel_block_message", fake_send_block)

	result = client.send_new_article_proposal(
		slack_channel_id="C111",
		url="https://example.com/articles/2",
		content="Generated summary",
	)

	assert result == ("C111", "333.444")
	rich_text = captured.blocks[2]["elements"][0]["elements"][0]["text"]
	assert rich_text == "Generated summary"
	button = captured.blocks[3]["accessory"]
	assert button["url"] == "https://example.com/articles/2"


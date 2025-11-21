import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ai_ticket_platform.dependencies.settings import get_app_settings
from ai_ticket_platform.routers import slack as slack_router


@pytest.fixture()
def test_app():
	app = FastAPI()
	app.include_router(slack_router.router, prefix="/api")

	mock_settings = SimpleNamespace(
		SLACK_BOT_TOKEN="token",
		SLACK_CHANNEL_ID="C123",
	)

	async def override_settings():
		return mock_settings

	app.dependency_overrides[get_app_settings] = override_settings
	return app


class _SlackStub:
	def __init__(self, slack_bot_token, responses: dict):
		self.slack_bot_token = slack_bot_token
		self._responses = responses

	def send_channel_message(self, message, slack_channel_id):
		handler = self._responses.get("send_channel_message")
		return handler(message, slack_channel_id)

	def send_new_article_proposal(self, slack_channel_id, url, content):
		handler = self._responses.get("send_new_article_proposal")
		return handler(slack_channel_id, url, content)

	def send_confirmation_message(self, slack_channel_id, url):
		handler = self._responses.get("send_confirmation_message")
		return handler(slack_channel_id, url)


async def _post(app: FastAPI, path: str, params: dict | None = None):
	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as client:
		return await client.post(path, params=params or {})


def test_send_message_success(monkeypatch, test_app: FastAPI):
	def handler(message, slack_channel_id):
		assert message == "hello"
		assert slack_channel_id == "C123"
		return slack_channel_id, "111.222"

	monkeypatch.setattr(
		slack_router,
		"Slack",
		lambda *args, **kwargs: _SlackStub(
			kwargs.get("slack_bot_token"), {"send_channel_message": handler}
		),
	)

	async def _run():
		response = await _post(test_app, "/api/slack/send-message", {"message": "hello"})
		assert response.status_code == 200
		assert response.json() == {
			"status": "success",
			"channel_id": "C123",
			"message_id": "111.222",
		}

	asyncio.run(_run())


def test_send_message_failure(monkeypatch, test_app: FastAPI):
	def handler(message, slack_channel_id):
		return None

	monkeypatch.setattr(
		slack_router,
		"Slack",
		lambda *args, **kwargs: _SlackStub(
			kwargs.get("slack_bot_token"), {"send_channel_message": handler}
		),
	)

	async def _run():
		response = await _post(test_app, "/api/slack/send-message", {"message": "hello"})
		assert response.status_code == 200
		assert response.json()["status"] == "error"

	asyncio.run(_run())


def test_send_message_exception(monkeypatch, test_app: FastAPI):
	def handler(message, slack_channel_id):
		raise ValueError("boom")

	monkeypatch.setattr(
		slack_router,
		"Slack",
		lambda *args, **kwargs: _SlackStub(
			kwargs.get("slack_bot_token"), {"send_channel_message": handler}
		),
	)

	async def _run():
		response = await _post(test_app, "/api/slack/send-message", {"message": "hello"})
		assert response.status_code == 200
		assert response.json() == {"status": "error", "message": "boom"}

	asyncio.run(_run())


def test_send_article_proposal_success(monkeypatch, test_app: FastAPI):
	def handler(slack_channel_id, url, content):
		assert content == "Generated content"
		return slack_channel_id, "abc.def"

	monkeypatch.setattr(
		slack_router,
		"Slack",
		lambda *args, **kwargs: _SlackStub(
			kwargs.get("slack_bot_token"), {"send_new_article_proposal": handler}
		),
	)

	async def _run():
		response = await _post(
			test_app,
			"/api/slack/send-article-proposal",
			{"url": "https://example.com/article", "content": "Generated content"},
		)
		assert response.status_code == 200
		assert response.json()["status"] == "success"

	asyncio.run(_run())


def test_send_approval_confirmation_success(monkeypatch, test_app: FastAPI):
	def handler(slack_channel_id, url):
		assert url == "https://example.com/article"
		return slack_channel_id, "ghi.jkl"

	monkeypatch.setattr(
		slack_router,
		"Slack",
		lambda *args, **kwargs: _SlackStub(
			kwargs.get("slack_bot_token"), {"send_confirmation_message": handler}
		),
	)

	async def _run():
		response = await _post(
			test_app,
			"/api/slack/send-approval-confirmation",
			{"url": "https://example.com/article"},
		)
		assert response.status_code == 200
		assert response.json()["message_id"] == "ghi.jkl"

	asyncio.run(_run())


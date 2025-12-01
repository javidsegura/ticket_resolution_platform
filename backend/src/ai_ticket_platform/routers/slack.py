from typing import Annotated, Dict

from fastapi import APIRouter, Depends, status

from ai_ticket_platform.dependencies import get_app_settings
from ai_ticket_platform.core.clients.slack import Slack
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/slack")


@router.post(path="/send-message", status_code=status.HTTP_200_OK)
async def send_slack_message(
	settings: Annotated[object, Depends(get_app_settings)], message: str
):
	"""Sends a message to a Slack channel"""
	slack = Slack(slack_bot_token=settings.SLACK_BOT_TOKEN)
	try:
		result = slack.send_channel_message(
			message=message, slack_channel_id=settings.SLACK_CHANNEL_ID
		)
		if result is None:
			return {"status": "error", "message": "Failed to send Slack message"}
		channel_id, message_id = result
		return {"status": "success", "channel_id": channel_id, "message_id": message_id}
	except Exception as e:
		logger.error(f"Error sending Slack message: {str(e)}")
		return {"status": "error", "message": str(e)}


@router.post(path="/send-article-proposal", status_code=status.HTTP_200_OK)
async def send_article_proposal(
	settings: Annotated[object, Depends(get_app_settings)], url: str, content: str
):
	"""Sends a message to a Slack channel"""
	slack = Slack(slack_bot_token=settings.SLACK_BOT_TOKEN)
	try:
		result = slack.send_new_article_proposal(
			slack_channel_id=settings.SLACK_CHANNEL_ID, url=url, content=content
		)
		if result is None:
			return {"status": "error", "message": "Failed to send Slack message"}
		channel_id, message_id = result
		return {"status": "success", "channel_id": channel_id, "message_id": message_id}
	except Exception as e:
		logger.error(f"Error sending Slack message: {str(e)}")
		return {"status": "error", "message": str(e)}


@router.post(path="/send-approval-confirmation", status_code=status.HTTP_200_OK)
async def send_approval_confirmation(
	settings: Annotated[object, Depends(get_app_settings)], url: str
):
	"""Sends a message to a Slack channel"""
	slack = Slack(slack_bot_token=settings.SLACK_BOT_TOKEN)
	try:
		result = slack.send_confirmation_message(
			slack_channel_id=settings.SLACK_CHANNEL_ID, url=url
		)
		if result is None:
			return {"status": "error", "message": "Failed to send Slack message"}
		channel_id, message_id = result
		return {"status": "success", "channel_id": channel_id, "message_id": message_id}
	except Exception as e:
		logger.error(f"Error sending Slack message: {str(e)}")
		return {"status": "error", "message": str(e)}


@router.post(path="/receive-answer", status_code=status.HTTP_200_OK)
async def receive_slack_proposal_answer():
	"""Receives slack proposal answer"""
	return 0


@router.get(path="/ping", status_code=status.HTTP_200_OK)
async def cheeck_backend_health_endpoint() -> Dict:
	return {"response": "pong"}

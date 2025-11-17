import requests
import logging

class Slack:
    def __init__(self, slack_bot_token):
        self.slack_bot_token = slack_bot_token
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)


        self.headers = {
            "Authorization": f"Bearer {self.slack_bot_token}",
            "Content-Type": "application/json"
        }

    def send_channel_message(self, message: str, slack_channel_id: str):
        """
        Send a message to a Slack channel.

        Args:
            message: The message to send.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        url = "https://slack.com/api/chat.postMessage"
        payload = {
            "channel": slack_channel_id,
            "text": message
        }
        response = requests.post(url, headers=self.headers, json=payload)
        data = response.json()

        if data.get("ok"):
            self.logger.info(f"Message sent correctly")
            return slack_channel_id, data.get("ts")
        else:
            self.logger.error(f"{data}")

    def send_channel_block_message(self, blocks: list, slack_channel_id: str):
        """
        Send a block message to a Slack channel. 
        To create your message payload, use this resource https://app.slack.com/block-kit-builder/
        - The block message is a JSON-based array of structured blocks, presented as a URL-encoded string.
        Example: 
        - Example: [{"type": "section", "text": {"type": "plain_text", "text": "Hello world"}}]

        Args:
            blocks: The blocks to send.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        url = "https://slack.com/api/chat.postMessage"
        payload = {
            "channel": slack_channel_id,
            "blocks": blocks
        }
        response = requests.post(url, headers=self.headers, json=payload)
        data = response.json()

        if data.get("ok"):
            self.logger.info(f"Block message sent correctly")
            return slack_channel_id, data.get("ts")
        else:
            self.logger.error(f"{data}")
            
            
    def send_confirmation_message(self, slack_channel_id: str, url: str):
        """Send the approval confirmation block message."""

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Success! 🎉",
                    "emoji": True,
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "Your article was approved and stored in the company docs "
                        "successfully."
                    ),
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "See Article Page"},
                        "url": url,
                        "action_id": "open-article",
                    }
                ],
            },
        ]

        return self.send_channel_block_message(blocks=blocks, slack_channel_id=slack_channel_id)

    
    def send_new_article_proposal(self, slack_channel_id: str, url: str, content: str):
        """send a structured message for user to check AI proposal"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Zeffo has a suggestion",
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "text",
                                "text": content
                            }
                        ]
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "This is the article I have created."
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Open Article",
                    },
                    "value": "click_me_123",
                    "url": url,
                    "action_id": "button-action"
                }
            }
        ]

        return self.send_channel_block_message(blocks=blocks, slack_channel_id=slack_channel_id)
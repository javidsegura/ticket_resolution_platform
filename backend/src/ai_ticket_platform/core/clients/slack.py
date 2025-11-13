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
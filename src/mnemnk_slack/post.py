import json
import os
import sys
from typing import Any, Optional, override

from dotenv import load_dotenv
from loguru import logger
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from . import AgentContext, AgentData, BaseAgent, run_agent

logger.remove()
logger.add(sys.stderr, level="WARNING")

load_dotenv()


class SlackPostAgent(BaseAgent):
    """Post messages to a Slack channel."""

    DEFAULT_CONFIG = {
        "channel_name": "",
    }

    def __init__(self, config=None):
        """Initialize the SlackPublisherAgent with configuration."""
        super().__init__(config)
        self.channel_id = None

        self.slack_token = os.environ.get("SLACK_BOT_TOKEN")
        if not self.slack_token:
            logger.error("SLACK_BOT_TOKEN not found in environment variables")
            raise ValueError("SLACK_BOT_TOKEN not found in environment variables")

        self.client = WebClient(token=self.slack_token)

        self._resolve_channel_id()

    def _resolve_channel_id(self):
        """Resolve channel ID from channel name."""
        self.channel_id = None

        # Do nothing if channel name is not set
        if not self.config.get("channel_name"):
            return

        channel_name = self.config["channel_name"]

        try:
            response = self.client.conversations_list(
                types="public_channel,private_channel"
            )

            for channel in response.get("channels", []):
                if channel["name"] == channel_name:
                    self.channel_id = channel["id"]
                    logger.debug(
                        f"Resolved channel name '{channel_name}' to ID: {channel['id']}"
                    )
                    return

            logger.warning(f"Could not find channel with name: {channel_name}")

        except SlackApiError as e:
            logger.error(f"Error fetching channels: {e}")

    @override
    def process_config(self, new_config: Optional[dict[str, Any]]):
        """Handle updates to configuration."""
        # Resolve the ID if the channel name is updated
        if new_config and "channel_name" in new_config:
            self._resolve_channel_id()

    @override
    def process_input(self, ctx: AgentContext, data: AgentData):
        """Process input from Mnemnk and send to Slack."""
        if not self.channel_id:
            logger.error("No channel_id specified, cannot send message")
            return

        try:
            message_text = ""
            blocks = None
            attachments = None
            thread_ts = None

            if isinstance(data.value, str):
                message_text = data.value
            elif isinstance(data.value, dict):
                if "text" in data.value:
                    message_text = data.value["text"]
                if "blocks" in data.value:
                    blocks = data.value["blocks"]
                if "attachments" in data.value:
                    attachments = data.value["attachments"]
                if "thread_ts" in data.value:
                    thread_ts = data.value["thread_ts"]
            elif isinstance(data.value, list):
                # TODO: Send with multiple blocks
                message_text = "\n".join([str(item) for item in data.value])
            else:
                # Convert to JSON and send as text
                message_text = (
                    f"```{json.dumps(data.value, indent=2, ensure_ascii=False)}```"
                )

            params = {
                "channel": self.channel_id,
                "text": message_text,
                "unfurl_links": True,
                "unfurl_media": True,
            }
            if thread_ts:
                params["thread_ts"] = thread_ts
            if blocks:
                params["blocks"] = blocks
            if attachments:
                params["attachments"] = attachments

            response = self.client.chat_postMessage(**params)

            if response["ok"]:
                logger.debug(f"Message sent to channel {self.channel_id}")
            else:
                logger.error(f"Failed to send message: {response}")

        except SlackApiError as e:
            logger.error(f"Error sending message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


def main():
    """Main entry point."""
    run_agent(SlackPostAgent)


if __name__ == "__main__":
    main()

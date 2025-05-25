import logging
import os
import sys
import time
from typing import Any, override

from dotenv import load_dotenv
from loguru import logger
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

from . import AgentContext, AgentData, BaseAgent, run_agent

logger.remove()
logger.add(sys.stderr, level="WARNING")

load_dotenv()


class SlackListenerAgent(BaseAgent):
    """Listen to messages from a Slack channel."""

    DEFAULT_CONFIG = {
        "channel_name": "",
        "include_replies": False,
    }

    def __init__(self, config=None):
        """Initialize the SlackListenerAgent with configuration."""
        super().__init__(config)
        self.slack_token = os.environ.get("SLACK_BOT_TOKEN")
        self.app_token = os.environ.get("SLACK_APP_TOKEN")
        self.channel_id = None

        if not self.slack_token:
            logger.error("SLACK_BOT_TOKEN not found in environment variables")
            raise ValueError("SLACK_BOT_TOKEN not found in environment variables")

        if not self.app_token:
            logger.error("SLACK_APP_TOKEN not found in environment variables")
            raise ValueError("SLACK_APP_TOKEN not found in environment variables")

        self.slack_app = App(
            token=self.slack_token,
            logger=logging.getLogger("mnemnk_slack"),  # to suppress slack_bolt logs
        )

        self._resolve_channel_id()

        self.setup_listeners()

    def _resolve_channel_id(self):
        """Resolve channel ID from channel name."""
        self.channel_id = None

        # If channel name is not set, do nothing
        if not self.config.get("channel_name"):
            return

        channel_name = self.config["channel_name"]

        try:
            # Retrieve the list of channels
            response = self.slack_app.client.conversations_list(
                types="public_channel,private_channel"
            )

            # Find the channel matching the channel name
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

    def setup_listeners(self):
        """Set up event listeners for Slack."""

        @self.slack_app.event("message")
        def handle_message_events(body, logger):
            event = body["event"]

            # If channel ID is specified, ensure the message is from that channel
            if self.channel_id and event.get("channel") != self.channel_id:
                return

            # If it's a reply, follow the include_replies setting
            if event.get("thread_ts") and not self.config["include_replies"]:
                return

            try:
                user_info = self._get_user_info(event.get("user"))
                channel_info = self._get_channel_info(event.get("channel"))

                message_data = {
                    "text": event.get("text", ""),
                    "blocks": event.get("blocks", []),
                    "files": event.get("files", []),
                    "ts": event.get("ts", ""),
                    "thread_ts": event.get("thread_ts", ""),
                    "user_info": user_info,
                    "channel_info": channel_info,
                    "team": event.get("team", ""),
                }

                self.write_out(
                    AgentContext(),
                    "data",
                    AgentData("object", message_data),
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    def _get_user_info(self, user_id):
        """Fetch user information from Slack."""
        user_info = {}
        if user_id:
            user_info["id"] = user_id
            try:
                response = self.slack_app.client.users_info(user=user_id)
                if response["ok"]:
                    user_info = response["user"]
                else:
                    logger.error(f"Error fetching user info: {response['error']}")
            except SlackApiError as e:
                logger.error(f"Error fetching user info: {e}")
        return user_info

    def _get_channel_info(self, channel_id):
        """Fetch channel information from Slack."""
        channel_info = {}
        if channel_id:
            channel_info["id"] = channel_id
            try:
                response = self.slack_app.client.conversations_info(channel=channel_id)
                if response["ok"]:
                    channel_info = response["channel"]
                else:
                    logger.error(f"Error fetching channel info: {response['error']}")
            except SlackApiError as e:
                logger.error(f"Error fetching channel info: {e}")
        return channel_info

    @override
    def process_config(self, new_config: dict[str, Any]):
        """Handle updates to configuration."""
        # If channel name is updated, resolve the ID
        if "channel_name" in new_config:
            self._resolve_channel_id()

    @override
    def process_input(self, ctx: AgentContext, data: AgentData):
        """Process input from Mnemnk."""
        pass

    @override
    def run(self):
        """Start the Slack app in Socket Mode."""
        # Start a thread to monitor Mnemnk command-line input
        import threading

        handler = SocketModeHandler(self.slack_app, self.app_token)

        def monitor_stdin():
            for line in iter(input, ""):
                line = line.strip()
                if line.startswith(".CONFIG "):
                    self._handle_config(line)
                elif line == ".QUIT":
                    logger.debug("Received QUIT command, signaling shutdown")
                    handler.close()
                    time.sleep(1)
                    os._exit(0)
                    return

        stdin_thread = threading.Thread(target=monitor_stdin, daemon=True)
        stdin_thread.start()

        try:
            channel_display = self.config.get("channel_name")
            if channel_display == "":
                channel_display = "ALL"
            logger.debug(f"Starting Slack listener for channel: {channel_display}")

            handler.start()

        except KeyboardInterrupt:
            logger.debug("Keyboard interrupt received, shutting down")

        finally:
            logger.debug("Shutting down handler")
            handler.close()


def main():
    """Main entry point."""
    run_agent(SlackListenerAgent)


if __name__ == "__main__":
    main()

<div align="center">
  <h3 align="center">Mnemnk Slack Agents</h3>

![Badge Language] 
[![Badge License]][License]

</div>

Slack integration agents for the Mnemnk application that connect Slack channels to your Mnemnk workflows.

## Agents

- **Slack Listen**: Monitor messages from specific Slack channels and output them to Mnemnk
- **Slack Post**: Send messages from Mnemnk to Slack channels

## Getting Started

### Prerequisites

- [Mnemnk App](https://github.com/mnemnk/mnemnk-app)
- [uv](https://github.com/astral-sh/uv)

## Installation

1. Clone the repository:
   ```bash
   cd {Mnemnk Directory}/agents/
   git clone https://github.com/mnemnk/mnemnk-slack.git
   ```

2. Build
   ```bash
   cd mnemnk-slack
   uv sync
   ```

3. Create a `.env` file in the project root with your Slack credentials:
   ```
   SLACK_BOT_TOKEN=your-bot-token
   SLACK_APP_TOKEN=your-app-token
   ```

## Setting up Slack App

1. Create a new Slack App at [Slack API Console](https://api.slack.com/apps)

2. Enable Socket Mode:
   - Go to "Socket Mode" in the sidebar
   - Toggle "Enable Socket Mode"
   - Create an App-Level Token with the `connections:write` scope
   - Save this token as `SLACK_APP_TOKEN` in your `.env` file

3. Configure Bot Token Scopes under "OAuth & Permissions":
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `chat:write.public`
   - `groups:read`
   - `users:read` (optional)
   - `files:read` (optional)
   - `files:write` (optional)
   - `groups:history` (optional)
   - `im:history` (optional)
   - `mpim:history` (optional)

4. Enable Event Subscriptions:
   - Go to "Event Subscriptions" and turn it on
   - Subscribe to bot events:
     - `message.channels`
     - `message.groups` (optional)
     - `message.im` (optional)
     - `message.mpim` (optional)

5. Install the app to your workspace

6. Copy the Bot User OAuth Token to your `.env` file as `SLACK_BOT_TOKEN`

## Troubleshooting

- **Missing Tokens**: Ensure both `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are correctly set in your `.env` file
- **Permission Issues**: Check that your Slack app has all the required scopes
- **Channel Not Found**: Verify that the channel ID or name is correct and your bot is a member of the channel
- **Socket Mode Errors**: Make sure Socket Mode is enabled and the app-level token has the `connections:write` scope

<!----------------------------------------------------------------------------->

[License]: https://github.com/mnemnk/mnemnk-slack

<!----------------------------------{ Badges }--------------------------------->

[Badge Language]: https://img.shields.io/github/languages/top/mnemnk/mnemnk-slack
[Badge License]: https://img.shields.io/badge/License-MIT%20or%20Apache%202-green.svg

import requests
import os

class Notifier:
    def __init__(self):
        self.channels = {}
        self.user_tags = {
            "UserName": os.getenv("SLACK_USER_TAG", "")
        }

    def register_slack(self, name, webhook_url):
        self.channels[name] = {
            "type": "slack",
            "url": webhook_url
        }

    def send(self, message, channel_name, level="info", code_block=None):
        if channel_name not in self.channels:
            raise ValueError(f"Channel '{channel_name}' not registered.")

        channel = self.channels[channel_name]

        if channel["type"] == "slack":
            self._send_slack(
                webhook_url=channel["url"],
                message=message,
                level=level,
                code_block=code_block
            )
        else:
            raise NotImplementedError(f"Channel type '{channel['type']}' not supported.")

    def _send_slack(self, webhook_url, message, level, code_block=None):
        # Level config
        config = {
            "info": {
                "emoji": ":incoming_envelope:",
                "color": "#36a64f",
                "tag": "",
            },
            "warning": {
                "emoji": ":warning:",
                "color": "#F0D500",
                "tag": self.user_tags["Ayush"],
            },
            "critical": {
                "emoji": ":rotating_light:",
                "color": "#F32013",
                "tag": self.user_tags["Ayush"],
            }
        }

        if level not in config:
            raise ValueError(f"Unsupported level: {level}")

        level_cfg = config[level]
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{level_cfg['emoji']} *{level}* \n\n{level_cfg['tag']}\n{message}"
                }
            }
        ]

        # Optional code block for critical
        if code_block and level == "critical":
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{code_block}```"
                    }
                }
            )

        payload = {
            "attachments": [
                {
                    "color": level_cfg["color"],
                    "blocks": blocks
                }
            ]
        }

        response = requests.post(webhook_url, json=payload)
        if response.status_code != 200:
            raise Exception(f"Slack notification failed: {response.status_code} - {response.text}")

"""
This plugin searches for Telegram bot tokens
"""
import re

from detect_secrets.plugins.base import RegexBasedDetector


class TelegramBotTokenDetector(RegexBasedDetector):
    """Scans for Telegram bot tokens."""
    @property
    def secret_type(self):
        return 'Telegram Bot Token'

    @property
    def denylist(self):
        return [
            # refs https://core.telegram.org/bots/api#authorizing-your-bot
            re.compile(r'^\d{8,10}:[0-9A-Za-z_-]{35}$'),
        ]

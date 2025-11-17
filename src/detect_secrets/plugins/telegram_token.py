"""
This plugin searches for Telegram bot tokens
"""
import re

import requests
from typing import Optional

from detect_secrets.constants import VerifiedResult
from detect_secrets.plugins.base import RegexBasedDetector
from detect_secrets.util.code_snippet import CodeSnippet


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

    def verify(self, secret: str, context: Optional[CodeSnippet] = None) -> VerifiedResult:
        response = requests.get(
            'https://api.telegram.org/bot{}/getMe'.format(
                secret,
            ),
        )
        return (
            VerifiedResult.VERIFIED_TRUE
            if response.status_code == 200
            else VerifiedResult.VERIFIED_FALSE
        )

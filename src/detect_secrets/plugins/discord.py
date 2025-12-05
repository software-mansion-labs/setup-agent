"""
This plugin searches for Discord Bot Token
"""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class DiscordBotTokenDetector(RegexBasedDetector):
    """Scans for Discord Bot token."""
    @property
    def secret_type(self) -> str:
        return 'Discord Bot Token'

    @property
    def denylist(self) -> List[Pattern]:
        return [
            # Discord Bot Token ([M|N|O]XXXXXXXXXXXXXXXXXXXXXXX[XX].XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXX)
            # Reference: https://discord.com/developers/docs/reference#authentication
            # Also see: https://github.com/Yelp/detect-secrets/issues/627
            re.compile(r'[MNO][a-zA-Z\d_-]{23,25}\.[a-zA-Z\d_-]{6}\.[a-zA-Z\d_-]{27}'),
        ]

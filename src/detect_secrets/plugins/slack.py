"""
This plugin searches for Slack tokens
"""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector

class SlackDetector(RegexBasedDetector):
    """Scans for Slack tokens."""
    @property
    def secret_type(self):
        return 'Slack Token'

    @property
    def denylist(self) -> List[Pattern]:
        return [
            # Slack Token
            re.compile(r'xox(?:a|b|p|o|s|r)-(?:\d+-)+[a-z0-9]+', flags=re.IGNORECASE),
            # Slack Webhooks
            re.compile(
                r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+',
                flags=re.IGNORECASE | re.VERBOSE,
            ),
        ]

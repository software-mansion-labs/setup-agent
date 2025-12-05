import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector

class SquareOAuthDetector(RegexBasedDetector):
    """Scans for Square OAuth Secrets"""
    @property
    def secret_type(self):
        return 'Square OAuth Secret'

    @property
    def denylist(self) -> List[Pattern]:
        return [
            re.compile(r'sq0csp-[0-9A-Za-z\\\-_]{43}'),
        ]

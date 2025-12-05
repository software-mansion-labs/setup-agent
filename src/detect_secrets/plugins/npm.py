"""
This plugin searches for NPM tokens
"""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class NpmDetector(RegexBasedDetector):
    """Scans for NPM tokens."""
    @property
    def secret_type(self) -> str:
        return 'NPM tokens'

    @property
    def denylist(self) -> List[Pattern]:
        return [
            # npmrc authToken
            # ref. https://stackoverflow.com/questions/53099434/using-auth-tokens-in-npmrc
            re.compile(r'\/\/.+\/:_authToken=\s*((npm_.+)|([A-Fa-f0-9-]{36})).*'),
        ]

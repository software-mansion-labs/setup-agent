"""
This plugin searches for GitHub tokens
"""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class GitHubTokenDetector(RegexBasedDetector):
    """Scans for GitHub tokens."""
    @property
    def secret_type(self):
        return 'GitHub Token'

    @property
    def denylist(self) -> List[Pattern]:
        return [
            # ref. https://github.blog/2021-04-05-behind-githubs-new-authentication-token-formats/
            re.compile(r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}'),
        ]

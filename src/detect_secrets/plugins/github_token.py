"""This plugin searches for GitHub tokens."""

import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class GitHubTokenDetector(RegexBasedDetector):
    """Scans for GitHub tokens.

    This detector identifies the modern (post-2021) GitHub authentication
    token formats, which include specific prefixes indicating the token type.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'GitHub Token'.
        """
        return "GitHub Token"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        This focuses on the format introduced in April 2021, characterized by:
        1. A 3-letter prefix indicating type (e.g., 'ghp' for Personal Access Token).
        2. An underscore separator.
        3. A 36-character alphanumeric string.

        Supported prefixes:
        - ghp: Personal Access Tokens
        - gho: OAuth Access Tokens
        - ghu: User-to-Server Tokens
        - ghs: Server-to-Server Tokens
        - ghr: Refresh Tokens

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # ref. https://github.blog/2021-04-05-behind-githubs-new-authentication-token-formats/
            re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}"),
        ]

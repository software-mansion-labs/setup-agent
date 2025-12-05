"""This plugin searches for SendGrid API keys."""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class SendGridDetector(RegexBasedDetector):
    """Scans for SendGrid API keys.

    This detector identifies API keys using the strict `SG.` prefix format
    implemented by SendGrid.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'SendGrid API Key'.
        """
        return 'SendGrid API Key'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        

        The pattern enforces the official SendGrid key architecture:
        1. Prefix: `SG.`
        2. Key ID: 22 characters (Base64-like alphanumeric + `_` `-`).
        3. Separator: `.`
        4. Secret: 43 characters (Base64-like alphanumeric + `_` `-`).

        Reference:
            https://d2w67tjf43xwdp.cloudfront.net/Classroom/Basics/API/what_is_my_api_key.html

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # SendGrid API key
            # ref. https://d2w67tjf43xwdp.cloudfront.net/Classroom/Basics/API/what_is_my_api_key.html
            re.compile(r'SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}'),
        ]
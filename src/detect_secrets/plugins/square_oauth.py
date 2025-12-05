"""This plugin searches for Square OAuth tokens."""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class SquareOAuthDetector(RegexBasedDetector):
    """Scans for Square OAuth Secrets.

    This detector specifically identifies **Production Client Secrets** used in
    Square's OAuth flow.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Square OAuth Secret'.
        """
        return 'Square OAuth Secret'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The pattern enforces the Square secret format:
        1. Prefix: `sq0csp-`
           - `sq0`: Version (Square 0)
           - `c`: Client
           - `s`: Secret
           - `p`: Production
        2. Payload: 43 characters (alphanumeric, dashes, underscores, backslashes).

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            re.compile(r'sq0csp-[0-9A-Za-z\\\-_]{43}'),
        ]
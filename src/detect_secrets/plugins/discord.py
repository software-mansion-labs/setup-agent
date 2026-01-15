"""Scans for Discord Bot tokens."""

import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class DiscordBotTokenDetector(RegexBasedDetector):
    """Scans for Discord Bot tokens.

    Discord tokens act as authorization keys for bot accounts and consist of
    three distinct parts separated by periods.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Discord Bot Token'.
        """
        return "Discord Bot Token"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The pattern enforces the specific structure of a Discord Bot Token:
        1.  Base64 encoded User ID (specifically starting with M, N, or O).
        2.  Base64 encoded Timestamp.
        3.  Base64 encoded HMAC signature.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # Discord Bot Token structure:
            # [Base64 User ID].[Base64 Timestamp].[Base64 HMAC]
            # Reference: https://discord.com/developers/docs/reference#authentication
            # Note: The [MNO] start char is a heuristic based on Base64 encoding of
            # recent User IDs. See: https://github.com/Yelp/detect-secrets/issues/627
            re.compile(r"[MNO][a-zA-Z\d_-]{23,25}\.[a-zA-Z\d_-]{6}\.[a-zA-Z\d_-]{27}"),
        ]

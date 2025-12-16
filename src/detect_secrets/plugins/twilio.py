"""This plugin searches for Twilio API keys."""

import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class TwilioKeyDetector(RegexBasedDetector):
    """Scans for Twilio credentials.

    This detector identifies specific Twilio credential types based on their
    unique 2-character prefixes followed by a 32-character hexadecimal string.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Twilio API Key'.
        """
        return "Twilio API Key"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The patterns look for:
        1.  **Account SID (`AC`):** The primary identifier for a Twilio account.
            While technically an ID (not a secret), it is often treated as sensitive
            in code scanning contexts.
        2.  **API Key SID (`SK`):** The identifier for a specific API Key pair.

        Both are followed by 32 lowercase alphanumeric characters.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # Account SID (ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
            re.compile(r"AC[a-z0-9]{32}"),
            # Auth token (SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
            re.compile(r"SK[a-z0-9]{32}"),
        ]

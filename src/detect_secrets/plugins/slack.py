"""This plugin searches for Slack tokens."""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class SlackDetector(RegexBasedDetector):
    """Scans for Slack tokens.

    This detector identifies both standard Slack API tokens (used for bot and
    user authentication) and Incoming Webhook URLs (used for posting messages).
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Slack Token'.
        """
        return 'Slack Token'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The patterns target:
        1.  **API Tokens:** specific `xox` prefixes followed by a variant character:
            - `xoxb`: Bot User OAuth Access Token
            - `xoxp`: User OAuth Access Token
            - `xoxa`, `xoxo`, `xoxs`, `xoxr`: Legacy/Other token types.
            The structure typically involves hyphen-separated numeric IDs and a final secret.

        2.  **Incoming Webhooks:** URLs formatted as:
            `https://hooks.slack.com/services/T.../B.../...`
            Where `T...` is the Workspace ID, `B...` is the Bot ID, and the final
            segment is the secret.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # Slack Token
            re.compile(r'xox(?:a|b|p|o|s|r)-(?:\d+-)+[a-z0-9]+', flags=re.IGNORECASE),
            # Slack Webhooks
            re.compile(
                r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+',
                flags=re.IGNORECASE | re.VERBOSE,
            ),
        ]
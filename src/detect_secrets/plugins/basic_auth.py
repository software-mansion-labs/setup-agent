"""This plugin searches for Basic Auth credentials."""

import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector

# This list is derived from RFC 3986 Section 2.2.
#
# We don't expect any of these delimiter characters to appear in
# the username/password component of the URL, seeing that this would probably
# result in an unexpected URL parsing (and probably won't even work).
RESERVED_CHARACTERS = ":/?#[]@"
SUB_DELIMITER_CHARACTERS = "!$&'()*+,;="


class BasicAuthDetector(RegexBasedDetector):
    """Scans for Basic Auth formatted URIs.

    This detects credentials embedded directly in URLs following the standard
    scheme: `protocol://username:password@host`.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Basic Auth Credentials'.
        """
        return "Basic Auth Credentials"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The regex dynamically constructs a pattern that ignores RFC 3986 reserved
        characters within the credential section to avoid false positives on complex
        URLs.

        It looks for:
        1. The protocol separator `://`.
        2. A username (chars not in reserved/sub-delimiter sets).
        3. A colon `:`.
        4. A password (chars not in reserved/sub-delimiter sets) -> Captured.
        5. An `@` symbol.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            re.compile(
                r"://[^{}\s]+:([^{}\s]+)@".format(
                    re.escape(RESERVED_CHARACTERS + SUB_DELIMITER_CHARACTERS),
                    re.escape(RESERVED_CHARACTERS + SUB_DELIMITER_CHARACTERS),
                ),
            ),
        ]

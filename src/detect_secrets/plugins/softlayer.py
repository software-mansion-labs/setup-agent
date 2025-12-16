"""This plugin searches for SoftLayer credentials."""

import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class SoftlayerDetector(RegexBasedDetector):
    """Scans for SoftLayer credentials.

    This detector identifies SoftLayer API keys (64-character lowercase
    alphanumeric strings) in both variable assignments and direct SOAP API URLs.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'SoftLayer Credentials'.
        """
        return "SoftLayer Credentials"

    sl = r"(?:softlayer|sl)(?:_|-|)(?:api|)"
    key_or_pass = r"(?:key|pwd|password|pass|token)"
    secret = r"([a-z0-9]{64})"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The patterns look for:
        1.  **Assignments:** Variables with names containing 'softlayer' or 'sl'
            assigned to a 64-character lowercase alphanumeric string.
        2.  **SOAP URLs:** API keys embedded directly in SoftLayer SOAP API endpoints
            (e.g., `api.softlayer.com/soap/v3/KEY`).

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=self.sl,
                secret_keyword_regex=self.key_or_pass,
                secret_regex=self.secret,
            ),
            re.compile(
                r"(?:http|https)://api.softlayer.com/soap/(?:v3|v3.1)/([a-z0-9]{64})",
                flags=re.IGNORECASE,
            ),
        ]

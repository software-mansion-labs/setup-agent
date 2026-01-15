"""
This plugin searches for AWS key IDs
"""

import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class AWSKeyDetector(RegexBasedDetector):
    """Scans for AWS Access Key IDs and Secret Access Keys.

    This checks for both standard Access Key identifiers (starting with AKIA, etc.)
    and variable assignments looking for Secret Access Keys.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'AWS Access Key'.
        """
        return "AWS Access Key"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The patterns look for:
        1. Standard AWS Access Key IDs (20 chars, starting with specific prefixes).
        2. AWS Secret Access Keys (40 chars) assigned to variables containing
           keywords like 'key', 'password', or 'token'.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        secret_keyword = r"(?:key|pwd|pw|password|pass|token)"
        return [
            # Standard AWS Access Key IDs
            re.compile(r"(?:A3T[A-Z0-9]|ABIA|ACCA|AKIA|ASIA)[0-9A-Z]{16}"),
            # AWS Secret Access Keys
            # This examines the variable name to identify AWS secret tokens.
            # The order is important since we want to prefer finding access
            # keys (since they can be verified), rather than the secret tokens.
            re.compile(
                r"aws.{{0,20}}?{secret_keyword}.{{0,20}}?[\'\"]([0-9a-zA-Z/+]{{40}})[\'\"]".format(
                    secret_keyword=secret_keyword,
                ),
                flags=re.IGNORECASE,
            ),
        ]

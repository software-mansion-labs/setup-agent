"""This plugin searches for Mailchimp keys."""

import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class MailchimpDetector(RegexBasedDetector):
    """Scans for Mailchimp Access Keys.

    Mailchimp API keys have a distinct structure involving a 32-character
    hexadecimal string followed by a data center suffix (e.g., `xxxxxxxx-us19`).
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Mailchimp Access Key'.
        """
        return "Mailchimp Access Key"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The pattern looks for:
        1. 32 lowercase hexadecimal characters.
        2. A literal '-us' suffix.
        3. A 1 or 2 digit data center identifier.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            re.compile(r"[0-9a-z]{32}-us[0-9]{1,2}"),
        ]

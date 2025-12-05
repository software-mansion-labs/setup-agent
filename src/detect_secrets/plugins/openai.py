"""This plugin searches for OpenAI tokens."""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class OpenAIDetector(RegexBasedDetector):
    """Scans for OpenAI API tokens.

    This detector identifies standard OpenAI API keys, including both the legacy
    user-based keys and the newer project-based keys.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'OpenAI Token'.
        """
        return 'OpenAI Token'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The regex looks for the characteristic 'sk-' prefix followed by the
        Base64-encoded string 'T3BlbkFJ' (which decodes to 'OpenAI') embedded
        within the key.

        Supported formats:
        1. Legacy User Keys: `sk-` + 20 chars + `T3BlbkFJ` + 20 chars.
        2. Project Keys: `sk-` + project-id + 20 chars + `T3BlbkFJ` + 20 chars.

        Reference:
            https://community.openai.com/t/what-are-the-valid-characters-for-the-apikey/288643

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # refs https://community.openai.com/t/what-are-the-valid-characters-for-the-apikey/288643
            # User api keys (legacy): 'sk-[20 alnum]T3BlbkFJ[20 alnum]'
            # Project-based api keys: 'sk-[project-name]-[20 alnum]T3BlbkFJ[20 alnum]'
            re.compile(r'sk-[A-Za-z0-9-_]*[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}'),
        ]
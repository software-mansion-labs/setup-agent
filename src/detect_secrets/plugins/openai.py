"""This plugin searches for OpenAI tokens."""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class OpenAIDetector(RegexBasedDetector):
    """Scans for OpenAI API tokens.

    This detector identifies standard OpenAI API keys, including legacy user-based keys,
    project-based keys, and newer service account keys.
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

        The regex looks for the characteristic 'sk-' prefix, optional type prefixes
        (like 'svcacct-' or 'proj-'), and the known anchor string 'BlbkFJ' embedded
        within the key.

        Supported formats:
        1. Legacy User Keys: `sk-` + alphanumeric chars + `BlbkFJ` + alphanumeric chars.
        2. Project Keys: `sk-proj-` + variable chars + `BlbkFJ` + variable chars.
        3. Service Account Keys: `sk-svcacct-` + variable chars + `BlbkFJ` + variable chars.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # Regex explanation:
            # 1. sk-                  -> Standard prefix
            # 2. (?:svcacct-|proj-|)  -> Optional prefixes: 'svcacct-', 'proj-', or empty (legacy)
            # 3. [A-Za-z0-9-_]+       -> Pre-anchor part: alphanumeric, dashes, underscores
            # 4. BlbkFJ               -> "Magic" anchor string (common in OpenAI keys)
            # 5. [A-Za-z0-9-_]+       -> Post-anchor part: alphanumeric, dashes, underscores
            re.compile(r'sk-(?:svcacct-|proj-|)[A-Za-z0-9-_]+BlbkFJ[A-Za-z0-9-_]+'),
        ]
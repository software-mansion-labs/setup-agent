import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class ArtifactoryDetector(RegexBasedDetector):
    """Scans for Artifactory credentials.

    This detects specific token prefixes used by Artifactory for API access
    and encrypted passwords.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Artifactory Credentials'.
        """
        return 'Artifactory Credentials'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The patterns look for:
        1. Artifactory API tokens (starting with 'AKC').
        2. Artifactory encrypted passwords (starting with 'AP' followed by
           specific hex/uppercase indicators).

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # Artifactory tokens begin with AKC
            re.compile(r'(?:\s|=|:|"|^)AKC[a-zA-Z0-9]{10,}(?:\s|"|$)'),
            # Artifactory encrypted passwords begin with AP[A-Z]
            re.compile(r'(?:\s|=|:|"|^)AP[\dABCDEF][a-zA-Z0-9]{8,}(?:\s|"|$)'),
        ]
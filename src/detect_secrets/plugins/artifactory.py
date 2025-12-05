import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class ArtifactoryDetector(RegexBasedDetector):
    """Scans for Artifactory credentials."""
    @property
    def secret_type(self) -> str:
        return 'Artifactory Credentials'

    @property
    def denylist(self) -> List[Pattern]:
        return [
            # Artifactory tokens begin with AKC
            re.compile(r'(?:\s|=|:|"|^)AKC[a-zA-Z0-9]{10,}(?:\s|"|$)'),  # API token
            # Artifactory encrypted passwords begin with AP[A-Z]
            re.compile(r'(?:\s|=|:|"|^)AP[\dABCDEF][a-zA-Z0-9]{8,}(?:\s|"|$)'),  # Password
        ]

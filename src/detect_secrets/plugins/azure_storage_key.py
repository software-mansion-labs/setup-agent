"""
This plugin searches for Azure Storage Account access keys.
"""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class AzureStorageKeyDetector(RegexBasedDetector):
    """Scans for Azure Storage Account access keys."""

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Azure Storage Account access key'.
        """
        return 'Azure Storage Account access key'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The patterns look for:
        1. Azure Storage connection strings containing 'AccountKey='.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # Account Key (AccountKey=xxxxxxxxx)
            re.compile(r'AccountKey=[a-zA-Z0-9+\/=]{88}'),
        ]
"""
This plugin searches for Azure Storage Account access keys.
"""
import re

from detect_secrets.plugins.base import RegexBasedDetector


class AzureStorageKeyDetector(RegexBasedDetector):
    """Scans for Azure Storage Account access keys."""
    @property
    def secret_type(self):
        return 'Azure Storage Account access key'

    @property
    def denylist(self):
        return [
            # Account Key (AccountKey=xxxxxxxxx)
            re.compile(r'AccountKey=[a-zA-Z0-9+\/=]{88}'),
        ]

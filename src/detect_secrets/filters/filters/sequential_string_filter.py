import string
from typing import Optional, Tuple

from detect_secrets.plugins.base import BasePlugin
from detect_secrets.filters.base_secret_filter import BaseSecretFilter

class SequentialStringFilter(BaseSecretFilter):
    """Filters out simple sequential strings (e.g., 'abcde', '12345')."""

    SEQUENCES: Tuple[str, ...] = (
        # Base64 letters first
        string.ascii_uppercase + string.ascii_uppercase + string.digits + '+/',
        # Base64 numbers first
        string.digits + string.ascii_uppercase + string.ascii_uppercase + '+/',
        # Alphanumeric sequences
        (string.digits + string.ascii_uppercase) * 2,
        # Capturing any number sequences
        string.digits * 2,
        # Hex sequences
        string.hexdigits.upper() + string.hexdigits.upper(),
        # Other common patterns
        string.ascii_uppercase + '=/',
    )

    def should_exclude(self, secret: str, plugin: Optional[BasePlugin] = None) -> bool:
        uppercase_secret = secret.upper()
        for sequence in self.SEQUENCES:
            if uppercase_secret in sequence:
                return True
        return False

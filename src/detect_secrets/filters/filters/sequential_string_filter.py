import string
from typing import Optional, Tuple

from detect_secrets.plugins.base import BasePlugin
from detect_secrets.filters.base_secret_filter import BaseSecretFilter


class SequentialStringFilter(BaseSecretFilter):
    """Filter for simple sequential strings.

    Sequential strings like 'abcde', '12345' are filtered out using
    the sequences defined in the class.

    Attributes:
        SEQUENCES (tuple): Tuple of strings in which the secret is searched.
    """

    SEQUENCES: Tuple[str, ...] = (
        # Base64 letters first
        string.ascii_uppercase + string.ascii_uppercase + string.digits + "+/",
        # Base64 numbers first
        string.digits + string.ascii_uppercase + string.ascii_uppercase + "+/",
        # Alphanumeric sequences
        (string.digits + string.ascii_uppercase) * 2,
        # Capturing any number sequences
        string.digits * 2,
        # Hex sequences
        string.hexdigits.upper() + string.hexdigits.upper(),
        # Other common patterns
        string.ascii_uppercase + "=/",
    )

    def should_exclude(self, secret: str, plugin: Optional[BasePlugin] = None) -> bool:
        """Method to check if the input secret should be excluded.

        Args:
            secret (str): The secret string to check.
            plugin (Optional[BasePlugin], optional): typically an instance of
                one of the child classes of BasePlugin. Defaults to None.

        Returns:
            bool: `True` if the secret is found in any of the sequences,
                `False` otherwise.
        """

        uppercase_secret = secret.upper()
        for sequence in self.SEQUENCES:
            if uppercase_secret in sequence:
                return True
        return False

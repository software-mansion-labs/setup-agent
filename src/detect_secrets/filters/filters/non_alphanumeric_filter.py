import string
from typing import Optional

from detect_secrets.plugins.base import BasePlugin
from detect_secrets.filters.base_secret_filter import BaseSecretFilter


class NotAlphanumericFilter(BaseSecretFilter):
    """
    Filters out secrets that do not contain at least one letter.
    Useful for filtering out purely numerical strings or strings like '*****'.
    """

    def should_exclude(self, secret: str, plugin: Optional[BasePlugin] = None) -> bool:
        """
        Determines whether to exclude a given secret.

        This method checks if the secret contains any letters. If it does not, the method returns true,
        indicating the secret should be excluded. Otherwise, it returns false.

        Args:
            secret (str): The secret to check.
            plugin (Optional[BasePlugin], optional): A plugin. Defaults to None.

        Returns:
            bool: True if secret does not contain any letters, False otherwise.
        """
        return not bool(set(string.ascii_letters) & set(secret))
import re
from typing import Optional, Pattern

from detect_secrets.filters.base_secret_filter import BaseSecretFilter
from detect_secrets.plugins.base import BasePlugin


class UUIDFilter(BaseSecretFilter):
    """Filters out strings that match standard UUID formats."""

    _REGEX: Pattern = re.compile(
        r"[a-f0-9]{8}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{12}",
        re.IGNORECASE,
    )

    def should_exclude(self, secret: str, plugin: Optional[BasePlugin] = None) -> bool:
        """
        Determine whether the secret should be excluded based on the UUID pattern.

        Args:
            secret (str): The secret string to be checked.
            plugin (Optional[BasePlugin]): The detect-secrets plugin being used.

        Returns:
            bool: True if the secret should be excluded, False otherwise.
        """
        return bool(self._REGEX.search(secret))

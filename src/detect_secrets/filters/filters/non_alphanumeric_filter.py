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
        return not bool(set(string.ascii_letters) & set(secret))
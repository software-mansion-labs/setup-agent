from typing import Optional, Pattern
import re

from detect_secrets.plugins.base import BasePlugin
from detect_secrets.filters.base_secret_filter import BaseSecretFilter

class UUIDFilter(BaseSecretFilter):
    """Filters out strings that match standard UUID formats."""

    _REGEX: Pattern = re.compile(
        r'[a-f0-9]{8}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{12}',
        re.IGNORECASE,
    )

    def should_exclude(self, secret: str, plugin: Optional[BasePlugin] = None) -> bool:
        return bool(self._REGEX.search(secret))
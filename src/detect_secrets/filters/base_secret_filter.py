from abc import ABC, abstractmethod
from typing import Optional

from detect_secrets.plugins.base import BasePlugin


class BaseSecretFilter(ABC):
    """Abstract base class for all heuristic filters."""

    @abstractmethod
    def should_exclude(self, secret: str, plugin: Optional[BasePlugin] = None) -> bool:
        """
        Checks if the secret should be excluded.
        Args:
            secret (str): The secret to check.
            plugin (Optional[BasePlugin], optional): The plugin used. Defaults to None.
        Returns:
            bool: True if the secret should be filtered out (ignored/false positive), False if the secret should be kept.
        """
        pass

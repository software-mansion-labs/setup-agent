from typing import Optional

from detect_secrets.filters.base_secret_filter import BaseSecretFilter
from detect_secrets.plugins.base import BasePlugin


class TemplatedSecretFilter(BaseSecretFilter):
    """
    Filters out templated variables like ${PASSWORD} or <SECRET>.

    Methods:
        should_exclude(secret: str, plugin: Optional[BasePlugin] = None) -> bool
    """

    def should_exclude(self, secret: str, plugin: Optional[BasePlugin] = None) -> bool:
        """Determines if a secret should be excluded based on being a template.

        Args:
            secret (str): The secret string to evaluate.
            plugin (Optional[BasePlugin]): An optional plugin used to help evaluate secrets.
        Returns:
            bool: True if the secret should be excluded (i.e., is a template), False otherwise.
        """
        if len(secret) < 2:
            # A one-character secret is likely a false positive
            return True

        return (
            (secret.startswith("{") and secret.endswith("}"))
            or (secret.startswith("<") and secret.endswith(">"))
            or (secret.startswith("${") and secret.endswith("}"))
        )

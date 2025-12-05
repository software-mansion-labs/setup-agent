from typing import Optional

from detect_secrets.plugins.base import BasePlugin
from detect_secrets.filters.base_secret_filter import BaseSecretFilter

class TemplatedSecretFilter(BaseSecretFilter):
    """Filters out templated variables like ${PASSWORD} or <SECRET>."""

    def should_exclude(self, secret: str, plugin: Optional[BasePlugin] = None) -> bool:
        if len(secret) < 2:
            # A one-character secret is likely a false positive
            return True

        return (
            (secret.startswith('{') and secret.endswith('}'))
            or (secret.startswith('<') and secret.endswith('>'))
            or (secret.startswith('${') and secret.endswith('}'))
        )
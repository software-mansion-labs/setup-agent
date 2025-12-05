from typing import List

from detect_secrets.core import scan
from detect_secrets.plugins.base import PotentialSecretResult
from detect_secrets.settings import get_plugins

class SecretsCollection:
    def scan_text(self, text: str) -> List[PotentialSecretResult]:
        plugins = get_plugins()
        secrets = scan.scan_line(text, plugins=plugins)
        result: List[PotentialSecretResult] = []

        for secret in secrets:
            plugin = [p for p in plugins if p.secret_type == secret.secret_type][0]
            result.append(plugin.prepare_secret_result(secret=secret))

        return result

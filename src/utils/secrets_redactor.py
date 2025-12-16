from detect_secrets import SecretsCollection
from typing import Set


class SecretsRedactor:
    @classmethod
    def scan_text_for_secrets(cls, text: str) -> Set[str]:
        secrets_collection = SecretsCollection()
        potential_secrets = [
            secret["secret_value"]
            for secret in secrets_collection.scan_text(text)
            if secret["is_secret"]
        ]
        valid_potential_secrets = [
            secret for secret in potential_secrets if secret is not None
        ]

        return set(valid_potential_secrets)

    @classmethod
    def mask_secrets_in_text(cls, text: str, mask: str = "[REDACTED]"):
        potential_secrets = cls.scan_text_for_secrets(text)
        for secret in potential_secrets:
            text = text.replace(secret, mask)

        return text

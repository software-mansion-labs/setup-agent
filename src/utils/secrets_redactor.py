from typing import Set

from detect_secrets import SecretsCollection


class SecretsRedactor:
    """Utility class for identifying and masking sensitive information in text.

    Uses the secret detectors to scan strings for secrets (such as API keys,
    passwords, and tokens) and provides functionality to redact them to prevent
    accidental logging or exposure.
    """

    @classmethod
    def scan_text_for_secrets(cls, text: str) -> Set[str]:
        """Scans the provided text for potential secrets.

        Args:
            text (str): The input string to analyze.

        Returns:
            Set[str]: A set of unique string values identified as secrets.
        """
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
    def mask_secrets_in_text(cls, text: str, mask: str = "[REDACTED]") -> str:
        """Replaces all identified secrets in the text with a mask.

        Args:
            text (str): The text containing potential secrets.
            mask (str): The placeholder string to use for redaction.
                Defaults to "[REDACTED]".

        Returns:
            str: The sanitized text with all secrets replaced by the mask.
        """
        potential_secrets = cls.scan_text_for_secrets(text)
        for secret in potential_secrets:
            text = text.replace(secret, mask)

        return text

"""
This plugin searches for AWS key IDs
"""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class AWSKeyDetector(RegexBasedDetector):
    """Scans for AWS keys."""
    @property
    def secret_type(self) -> str:
        return 'AWS Access Key'

    @property
    def denylist(self) -> List[Pattern]:
        secret_keyword = r'(?:key|pwd|pw|password|pass|token)'
        return [
            re.compile(r'(?:A3T[A-Z0-9]|ABIA|ACCA|AKIA|ASIA)[0-9A-Z]{16}'),

            # This examines the variable name to identify AWS secret tokens.
            # The order is important since we want to prefer finding access
            # keys (since they can be verified), rather than the secret tokens.

            re.compile(
                r'aws.{{0,20}}?{secret_keyword}.{{0,20}}?[\'\"]([0-9a-zA-Z/+]{{40}})[\'\"]'.format(
                    secret_keyword=secret_keyword,
                ),
                flags=re.IGNORECASE,
            ),
        ]

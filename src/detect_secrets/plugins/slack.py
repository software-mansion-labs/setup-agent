"""
This plugin searches for Slack tokens
"""
import re
from typing import Any, cast, Dict, Optional

import requests

from detect_secrets.constants import VerifiedResult
from detect_secrets.plugins.base import RegexBasedDetector
from detect_secrets.util.code_snippet import CodeSnippet


class SlackDetector(RegexBasedDetector):
    """Scans for Slack tokens."""
    @property
    def secret_type(self):
        return 'Slack Token'

    @property
    def denylist(self):
        return (
            # Slack Token
            re.compile(r'xox(?:a|b|p|o|s|r)-(?:\d+-)+[a-z0-9]+', flags=re.IGNORECASE),
            # Slack Webhooks
            re.compile(
                r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+',
                flags=re.IGNORECASE | re.VERBOSE,
            ),
        )

    def verify(self, secret: str, context: Optional[CodeSnippet] = None) -> VerifiedResult:
        if secret.startswith('https://hooks.slack.com/services/T'):
            response = requests.post(
                secret,
                json={
                    'text': '',
                },
            )
            valid = response.text in ['missing_text_or_fallback_or_attachments', 'no_text']
        else:
            response = requests.post(
                'https://slack.com/api/auth.test',
                data={
                    'token': secret,
                },
            ).json()
            valid = cast(Dict[str, Any], response)['ok']

        return (
            VerifiedResult.VERIFIED_TRUE
            if valid
            else VerifiedResult.VERIFIED_FALSE
        )

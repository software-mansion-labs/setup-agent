"""
This plugin searches for Mailchimp keys
"""
import re
from base64 import b64encode

import requests

from detect_secrets.constants import VerifiedResult
from detect_secrets.plugins.base import RegexBasedDetector
from typing import Optional
from detect_secrets.util.code_snippet import CodeSnippet

class MailchimpDetector(RegexBasedDetector):
    """Scans for Mailchimp keys."""
    @property
    def secret_type(self):
        return 'Mailchimp Access Key'

    @property
    def denylist(self):
        return (
            re.compile(r'[0-9a-z]{32}-us[0-9]{1,2}'),
        )

    def verify(self, secret: str, context: Optional[CodeSnippet] = None) -> VerifiedResult:
        _, datacenter_number = secret.split('-us')

        response = requests.get(
            'https://us{}.api.mailchimp.com/3.0/'.format(
                datacenter_number,
            ),
            headers={
                'Authorization': b'Basic ' + b64encode(
                    'any_user:{}'.format(secret).encode('utf-8'),
                ),
            },
        )
        return (
            VerifiedResult.VERIFIED_TRUE
            if response.status_code == 200
            else VerifiedResult.VERIFIED_FALSE
        )

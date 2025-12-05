"""
This plugin searches for Mailchimp keys
"""
import re
from typing import List, Pattern
from detect_secrets.plugins.base import RegexBasedDetector

class MailchimpDetector(RegexBasedDetector):
    """Scans for Mailchimp keys."""
    @property
    def secret_type(self) -> str:
        return 'Mailchimp Access Key'

    @property
    def denylist(self) -> List[Pattern]:
        return [
            re.compile(r'[0-9a-z]{32}-us[0-9]{1,2}'),
        ]

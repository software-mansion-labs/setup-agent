"""
This plugin searches for Mailchimp keys
"""
import re
from detect_secrets.plugins.base import RegexBasedDetector

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

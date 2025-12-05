"""
This plugin searches for Twilio API keys
"""
import re

from detect_secrets.plugins.base import RegexBasedDetector


class TwilioKeyDetector(RegexBasedDetector):
    """Scans for Twilio API keys."""
    @property
    def secret_type(self):
        return 'Twilio API Key'

    @property
    def denylist(self):
        return [
            # Account SID (ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
            re.compile(r'AC[a-z0-9]{32}'),

            # Auth token (SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
            re.compile(r'SK[a-z0-9]{32}'),
        ]

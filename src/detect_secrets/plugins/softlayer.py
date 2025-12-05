import re

from detect_secrets.plugins.base import RegexBasedDetector


class SoftlayerDetector(RegexBasedDetector):
    """Scans for Softlayer credentials."""

    @property
    def secret_type(self):
        return 'SoftLayer Credentials'

    sl = r'(?:softlayer|sl)(?:_|-|)(?:api|)'
    key_or_pass = r'(?:key|pwd|password|pass|token)'
    secret = r'([a-z0-9]{64})'

    @property
    def denylist(self):
        return [
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=self.sl,
                secret_keyword_regex=self.key_or_pass,
                secret_regex=self.secret,
            ),

            re.compile(
                r'(?:http|https)://api.softlayer.com/soap/(?:v3|v3.1)/([a-z0-9]{64})',
                flags=re.IGNORECASE,
            ),
        ]

from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class IbmCosHmacDetector(RegexBasedDetector):
    """Scans for IBM Cloud Object Storage HMAC credentials."""
    # requires 3 factors
    #
    #   access_key: access_key_id
    #   secret_key: secret_access_key
    #   host, defaults to 's3.us.cloud-object-storage.appdomain.cloud'
    token_prefix = r'(?:(?:ibm)?[-_]?cos[-_]?(?:hmac)?|)'
    password_keyword = r'(?:secret[-_]?(?:access)?[-_]?key)'
    password = r'([a-f0-9]{48}(?![a-f0-9]))'


    @property
    def secret_type(self):
        return 'IBM COS HMAC Credentials'

    @property
    def denylist(self) -> List[Pattern]:
        return [
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=self.token_prefix,
                secret_keyword_regex=self.password_keyword,
                secret_regex=self.password,
            ),
        ]

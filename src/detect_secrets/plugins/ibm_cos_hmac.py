"""This plugin searches for IBM Cloud Object Storage HMAC credentials."""

from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class IbmCosHmacDetector(RegexBasedDetector):
    """Scans for IBM Cloud Object Storage HMAC credentials.

    This detector looks for the 'secret_access_key' portion of the HMAC credentials,
    which is a 48-character hexadecimal string.
    """

    # requires 3 factors
    #
    #   access_key: access_key_id
    #   secret_key: secret_access_key
    #   host, defaults to 's3.us.cloud-object-storage.appdomain.cloud'
    token_prefix = r"(?:(?:ibm)?[-_]?cos[-_]?(?:hmac)?|)"
    password_keyword = r"(?:secret[-_]?(?:access)?[-_]?key)"
    password = r"([a-f0-9]{48}(?![a-f0-9]))"

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'IBM COS HMAC Credentials'.
        """
        return "IBM COS HMAC Credentials"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The pattern constructs an assignment search that looks for:
        1. Variable names containing 'cos', 'hmac', or 'secret_access_key'.
        2. Assignments to a 48-character hexadecimal string.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=self.token_prefix,
                secret_keyword_regex=self.password_keyword,
                secret_regex=self.password,
            ),
        ]

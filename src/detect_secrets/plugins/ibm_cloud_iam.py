"""
This plugin searches for IBM Cloud IAM Keys.
"""

from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class IbmCloudIamDetector(RegexBasedDetector):
    """Scans for IBM Cloud IAM Keys.

    This detector identifies 44-character API keys that are assigned to variables
    containing keywords related to IBM, Cloud, and IAM.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'IBM Cloud IAM Key'.
        """
        return "IBM Cloud IAM Key"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The pattern constructs a flexible assignment search that looks for:
        1. Variable names containing combinations of 'ibm', 'cloud', 'iam', and 'api'.
        2. Assignments to a 44-character string (alphanumeric, underscores, and dashes).

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        opt_ibm_cloud_iam = (
            r"(?:ibm(?:_|-|)cloud(?:_|-|)iam|cloud(?:_|-|)iam|"
            + r"ibm(?:_|-|)cloud|ibm(?:_|-|)iam|ibm|iam|cloud|)"
        )
        opt_dash_underscore = r"(?:_|-|)"
        opt_api = r"(?:api|)"
        key_or_pass = r"(?:key|pwd|password|pass|token)"
        secret = r"([a-zA-Z0-9_\-]{44}(?![a-zA-Z0-9_\-]))"

        return [
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=opt_ibm_cloud_iam + opt_dash_underscore + opt_api,
                secret_keyword_regex=key_or_pass,
                secret_regex=secret,
            ),
        ]

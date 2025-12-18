import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class CloudantDetector(RegexBasedDetector):
    """Scans for Cloudant credentials.

    This detects both variable assignments (e.g., `cloudant_password = ...`)
    and credentials embedded directly into Cloudant service URLs.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Cloudant Credentials'.
        """
        return "Cloudant Credentials"

    # Regex components for building complex patterns
    # opt means optional
    dot = r"\."
    cl_account = r"[\w\-]+"
    cl = r"(?:cloudant|cl|clou)"
    opt_api = r"(?:api|)"
    cl_key_or_pass = opt_api + r"(?:key|pwd|pw|password|pass|token)"
    cl_pw = r"([0-9a-f]{64})"
    cl_api_key = r"([a-z]{24})"
    colon = r"\:"
    at = r"\@"
    http = r"(?:https?\:\/\/)"
    cloudant_api_url = r"cloudant\.com"

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The patterns look for:
        1. Assignments of Cloudant passwords (64 hex characters).
        2. Assignments of Cloudant API keys (24 lowercase alpha characters).
        3. URLs containing the password in the authority section:
           `https://account:password@account.cloudant.com`.
        4. URLs containing the API key in the authority section:
           `https://account:api_key@account.cloudant.com`.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # 1. Variable assignment for Password
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=self.cl,
                secret_keyword_regex=self.cl_key_or_pass,
                secret_regex=self.cl_pw,
            ),
            # 2. Variable assignment for API Key
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=self.cl,
                secret_keyword_regex=self.cl_key_or_pass,
                secret_regex=self.cl_api_key,
            ),
            # 3. URL embedding Password
            re.compile(
                r"{http}{cl_account}{colon}{cl_pw}{at}{cl_account}{dot}{cloudant_api_url}".format(
                    http=self.http,
                    colon=self.colon,
                    cl_account=self.cl_account,
                    cl_pw=self.cl_pw,
                    at=self.at,
                    dot=self.dot,
                    cloudant_api_url=self.cloudant_api_url,
                ),
                flags=re.IGNORECASE,
            ),
            # 4. URL embedding API Key
            re.compile(
                r"{http}{cl_account}{colon}{cl_api_key}{at}{cl_account}{dot}{cloudant_api_url}".format(
                    http=self.http,
                    colon=self.colon,
                    cl_account=self.cl_account,
                    cl_api_key=self.cl_api_key,
                    at=self.at,
                    dot=self.dot,
                    cloudant_api_url=self.cloudant_api_url,
                ),
                flags=re.IGNORECASE,
            ),
        ]

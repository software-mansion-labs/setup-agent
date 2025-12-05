import re

from detect_secrets.plugins.base import RegexBasedDetector


class CloudantDetector(RegexBasedDetector):
    """Scans for Cloudant credentials."""

    @property
    def secret_type(self):
        return 'Cloudant Credentials'

    # opt means optional
    dot = r'\.'
    cl_account = r'[\w\-]+'
    cl = r'(?:cloudant|cl|clou)'
    opt_api = r'(?:api|)'
    cl_key_or_pass = opt_api + r'(?:key|pwd|pw|password|pass|token)'
    cl_pw = r'([0-9a-f]{64})'
    cl_api_key = r'([a-z]{24})'
    colon = r'\:'
    at = r'\@'
    http = r'(?:https?\:\/\/)'
    cloudant_api_url = r'cloudant\.com'

    @property
    def denylist(self):
        return [
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=self.cl,
                secret_keyword_regex=self.cl_key_or_pass,
                secret_regex=self.cl_pw,
            ),
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=self.cl,
                secret_keyword_regex=self.cl_key_or_pass,
                secret_regex=self.cl_api_key,
            ),
            re.compile(
                r'{http}{cl_account}{colon}{cl_pw}{at}{cl_account}{dot}{cloudant_api_url}'.format(
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
            re.compile(
                r'{http}{cl_account}{colon}{cl_api_key}{at}{cl_account}{dot}{cloudant_api_url}'.format(
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

import re
from typing import List, Optional

import requests

from detect_secrets.constants import VerifiedResult
from detect_secrets.util.code_snippet import CodeSnippet
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

    def verify(
        self,
        secret: str,
        context: Optional[CodeSnippet]=None,
    ) -> VerifiedResult:
        if context is not None:
            usernames = find_username(context)
            if not usernames:
                return VerifiedResult.UNVERIFIED

            for username in usernames:
                return verify_softlayer_key(username, secret)

        return VerifiedResult.VERIFIED_FALSE


def find_username(context: CodeSnippet) -> List[str]:
    username_keyword = (
        r'(?:'
        r'username|id|user|userid|user-id|user-name|'
        r'name|user_id|user_name|uname'
        r')'
    )
    username = r'(\w(?:\w|_|@|\.|-)+)'
    regex = re.compile(
        RegexBasedDetector.build_assignment_regex(
            prefix_regex=SoftlayerDetector.sl,
            secret_keyword_regex=username_keyword,
            secret_regex=username,
        ),
    )

    return [
        match
        for line in context
        for match in regex.findall(line)
    ]


def verify_softlayer_key(username: str, token: str) -> VerifiedResult:
    headers = {'Content-type': 'application/json'}
    try:
        response = requests.get(
            'https://api.softlayer.com/rest/v3/SoftLayer_Account.json',
            auth=(username, token), headers=headers,
        )
    except requests.exceptions.RequestException:
        return VerifiedResult.UNVERIFIED

    if response.status_code == 200:
        return VerifiedResult.VERIFIED_TRUE
    else:
        return VerifiedResult.VERIFIED_FALSE

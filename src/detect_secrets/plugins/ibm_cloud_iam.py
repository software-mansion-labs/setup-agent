from typing import Union, Optional

import requests

from detect_secrets.constants import VerifiedResult
from detect_secrets.plugins.base import RegexBasedDetector
from detect_secrets.util.code_snippet import CodeSnippet



class IbmCloudIamDetector(RegexBasedDetector):
    """Scans for IBM Cloud IAM Key."""

    @property
    def secret_type(self):
        return 'IBM Cloud IAM Key'

    @property
    def denylist(self):
        # opt means optional
        opt_ibm_cloud_iam = r'(?:ibm(?:_|-|)cloud(?:_|-|)iam|cloud(?:_|-|)iam|' + \
            r'ibm(?:_|-|)cloud|ibm(?:_|-|)iam|ibm|iam|cloud|)'
        opt_dash_underscore = r'(?:_|-|)'
        opt_api = r'(?:api|)'
        key_or_pass = r'(?:key|pwd|password|pass|token)'
        secret = r'([a-zA-Z0-9_\-]{44}(?![a-zA-Z0-9_\-]))'

        return [
            RegexBasedDetector.build_assignment_regex(
                prefix_regex=opt_ibm_cloud_iam + opt_dash_underscore + opt_api,
                secret_keyword_regex=key_or_pass,
                secret_regex=secret,
            ),
        ]

    def verify(self, secret: str, context: Optional[CodeSnippet] = None) -> VerifiedResult:
        response = verify_cloud_iam_api_key(secret)

        return VerifiedResult.VERIFIED_TRUE if response.status_code == 200 \
            else VerifiedResult.VERIFIED_FALSE


def verify_cloud_iam_api_key(apikey: Union[str, bytes]) -> requests.Response:  # pragma: no cover
    if type(apikey) is bytes:
        apikey = apikey.decode('UTF-8')

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
    }
    response = requests.post(
        'https://iam.cloud.ibm.com/identity/token',
        headers=headers,
        data={
            'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': apikey,
        },
    )
    return response

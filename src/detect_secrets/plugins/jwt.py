"""This plugin finds JWT tokens."""
import base64
import json
import re
from typing import Generator, List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class JwtTokenDetector(RegexBasedDetector):
    """Scans for JWTs (JSON Web Tokens).

    This detector uses a two-step process:
    1. Identifies potential candidates using a regex (specifically looking for
       the 'eyJ' prefix, which is Base64 for '{"').
    2. Validates candidates by attempting to decode the Base64 structure and
       ensuring the header and payload are valid JSON.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'JSON Web Token'.
        """
        return 'JSON Web Token'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        This looks for strings starting with 'eyJ' (Base64 for '{"'), followed by
        Base64 characters, a dot, and more Base64 characters.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            re.compile(r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*?'),
        ]

    def analyze_string(self, string: str, **kwargs) -> Generator[str, None, None]:
        """Yields valid JWTs found in the string.

        This overrides the parent method to filter regex matches through
        a structural validation check (`is_formally_valid`) to reduce false
        positives.

        Args:
            string (str): The content to analyze.
            **kwargs: Arbitrary keyword arguments.

        Yields:
            str: Verified JWT strings.
        """
        yield from filter(
            self.is_formally_valid,
            super().analyze_string(string),
        )

    @staticmethod
    def is_formally_valid(token: str) -> bool:
        """Checks if a string is a formally valid JWT.
        
        A valid JWT consists of 3 parts separated by dots:
        1. Header (Base64 encoded JSON)
        2. Payload (Base64 encoded JSON)
        3. Signature (Base64 encoded data)

        This method attempts to decode the Base64 (handling missing padding)
        and parse the JSON for the first two parts.

        Args:
            token (str): The potential JWT string.

        Returns:
            bool: True if the token has valid structure and JSON content.
        """
        parts = token.split('.')
        for idx, part_str in enumerate(parts):
            try:
                part = part_str.encode('ascii')
                # https://github.com/magical/jwt-python/blob/2fd976b41111031313107792b40d5cfd1a8baf90/jwt.py#L49
                # https://github.com/jpadilla/pyjwt/blob/3d47b0ea9e5d489f9c90ee6dde9e3d9d69244e3a/jwt/utils.py#L33
                m = len(part) % 4
                if m == 1:
                    raise TypeError('Incorrect padding')
                elif m == 2:
                    part += '=='.encode('utf-8')
                elif m == 3:
                    part += '==='.encode('utf-8')
                b64_decoded = base64.urlsafe_b64decode(part)
                if idx < 2:
                    _ = json.loads(b64_decoded.decode('utf-8'))
            except (TypeError, ValueError, UnicodeDecodeError):
                return False

        return True
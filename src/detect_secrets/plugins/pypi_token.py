"""This plugin searches for PyPI tokens."""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class PypiTokenDetector(RegexBasedDetector):
    """Scans for PyPI (Python Package Index) tokens.

    PyPI uses Macaroon-based tokens for authentication. This detector identifies
    tokens based on their specific prefixes for both the production PyPI registry
    and the TestPyPI registry.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'PyPI Token'.
        """
        return 'PyPI Token'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The patterns target the unique structure of PyPI Macaroons:
        1. Prefix: `pypi-`
        2. Scope/Service Identifier (Base64 encoded):
           - `AgEIcHlwaS5vcmc`: Encodes 'pypi.org' (Production)
           - `AgENdGVzdC5weXBpLm9yZw`: Encodes 'test.pypi.org' (Test)
        3. Payload: 70+ URL-safe base64 characters.

        Reference:
            https://warehouse.pypa.io/development/token-scanning.html

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # refs https://warehouse.pypa.io/development/token-scanning.html
            # pypi.org token
            re.compile(r'pypi-AgEIcHlwaS5vcmc[A-Za-z0-9-_]{70,}'),

            # test.pypi.org token
            re.compile(r'pypi-AgENdGVzdC5weXBpLm9yZw[A-Za-z0-9-_]{70,}'),
        ]
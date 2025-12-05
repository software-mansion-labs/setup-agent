"""
This plugin searches for PyPI tokens
"""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class PypiTokenDetector(RegexBasedDetector):
    """Scans for PyPI tokens."""
    @property
    def secret_type(self) -> str:
        return 'PyPI Token'

    @property
    def denylist(self) -> List[Pattern]:
        return [
            # refs https://warehouse.pypa.io/development/token-scanning.html
            # pypi.org token
            re.compile(r'pypi-AgEIcHlwaS5vcmc[A-Za-z0-9-_]{70,}'),

            # test.pypi.org token
            re.compile(r'pypi-AgENdGVzdC5weXBpLm9yZw[A-Za-z0-9-_]{70,}'),
        ]

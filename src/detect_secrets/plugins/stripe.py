"""This plugin searches for Stripe API keys."""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class StripeDetector(RegexBasedDetector):
    """Scans for Stripe Access Keys.

    This detector focuses on **Live** (Production) keys, specifically:
    1. Standard Secret Keys (`sk_live_`).
    2. Restricted Secret Keys (`rk_live_`).
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Stripe Access Key'.
        """
        return 'Stripe Access Key'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        

        The pattern targets the specific prefixes used for production secrets:
        - `sk_live_`: Grants full API access (Standard).
        - `rk_live_`: Grants granular, scoped API access (Restricted).

        The regex expects exactly 24 alphanumeric characters following the prefix.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # Stripe standard keys begin with sk_live and restricted with rk_live
            re.compile(r'(?:r|s)k_live_[0-9a-zA-Z]{24}'),
        ]
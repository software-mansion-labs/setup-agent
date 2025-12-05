import re
from detect_secrets.plugins.base import RegexBasedDetector


class StripeDetector(RegexBasedDetector):
    """Scans for Stripe keys."""
    @property
    def secret_type(self):
        return 'Stripe Access Key'

    @property
    def denylist(self):
        return (
            # Stripe standard keys begin with sk_live and restricted with rk_live
            re.compile(r'(?:r|s)k_live_[0-9a-zA-Z]{24}'),
        )

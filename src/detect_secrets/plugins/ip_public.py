"""This plugin searches for Public IP addresses."""

import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class IPPublicDetector(RegexBasedDetector):
    """Scans for public IPv4 addresses.

    This detector identifies valid IPv4 addresses while explicitly ignoring
    non-public ranges as defined by IANA and RFC standards (Private, Loopback,
    and Link-Local).

    Excluded ranges:
    - 127.0.0.0/8 (Loopback)
    - 10.0.0.0/8 (Private)
    - 172.16.0.0/12 (Private)
    - 192.168.0.0/16 (Private)
    - 169.254.0.0/16 (Link-Local)

    References:
        - https://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.xhtml
        - https://en.wikipedia.org/wiki/Private_network
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'Public IP (ipv4)'.
        """
        return "Public IP (ipv4)"

    denylist_ipv4_address = r"""
        (?<![\w.])         # Negative lookbehind: Ensures no preceding word character or dot
        (                  # Start of the main capturing group
            (?!            # Negative lookahead: Ensures the following pattern doesn't match
                192\.168\. # Exclude "192.168."
                |127\.     # Exclude "127."
                |10\.      # Exclude "10."
                |169\.254\. # Exclude IPv4 Link Local Address (169.254.0.0/16)
                |172\.(?:1[6-9]|2[0-9]|3[01])   # Exclude "172." with specific ranges
            )
            (?:            # Non-capturing group for octets
                           # Match numbers 0-255 followed by dot, properly handle leading zeros
                (?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.
            ){3}           # Repeat for three octets
                           # Match final octet (0-255), properly handle leading zeros
            (?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])
            (?:            # Optional non-capturing group for port number
                :\d{1,5}   # Match colon followed by 1 to 5 digits
            )?
        )                  # End of the main capturing group
        (?![\w.])          # Negative lookahead: Ensures no following word character or dot
    """

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The regex uses negative lookaheads to exclude private and reserved
        IP ranges (RFC 1918, RFC 3927) from the detection results.

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            re.compile(self.denylist_ipv4_address, flags=re.IGNORECASE | re.VERBOSE),
        ]

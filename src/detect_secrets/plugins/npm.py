"""This plugin searches for NPM tokens."""
import re
from typing import List, Pattern

from detect_secrets.plugins.base import RegexBasedDetector


class NpmDetector(RegexBasedDetector):
    """Scans for NPM tokens.

    This detector specifically targets the format used in `.npmrc` configuration
    files, which involves a registry URL followed by `:_authToken=`.
    """

    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: The string identifier 'NPM tokens'.
        """
        return 'NPM tokens'

    @property
    def denylist(self) -> List[Pattern]:
        """Returns the list of regex patterns to search for.

        The pattern matches the standard `.npmrc` authentication token format:
        `//registry.npmjs.org/:_authToken=TOKEN`

        It supports two token formats:
        1. Modern tokens starting with `npm_`.
        2. Legacy UUID-style tokens (36 characters).

        Reference:
            https://stackoverflow.com/questions/53099434/using-auth-tokens-in-npmrc

        Returns:
            List[Pattern]: A list of compiled regular expression patterns.
        """
        return [
            # npmrc authToken
            # ref. https://stackoverflow.com/questions/53099434/using-auth-tokens-in-npmrc
            re.compile(r'\/\/.+\/:_authToken=\s*((npm_.+)|([A-Fa-f0-9-]{36})).*'),
        ]
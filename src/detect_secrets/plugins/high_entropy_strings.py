import math
import re
import string
from abc import ABCMeta
from contextlib import contextmanager
from typing import Any, cast, Dict, Generator, Set

from detect_secrets.core.potential_secret import PotentialSecret
from detect_secrets.plugins.base import BasePlugin, PotentialSecretResult

class PotentialSecretResultWithEntropy(PotentialSecretResult):
    """Typed dictionary representing a secret result with an added entropy score.

    Attributes:
        entropy (float): The calculated Shannon entropy of the secret string.
    """
    entropy: float

class HighEntropyStringsPlugin(BasePlugin, metaclass=ABCMeta):
    """Base class for plugins that detect secrets based on information density (entropy)."""

    def __init__(self, charset: str, limit: float) -> None:
        """Initializes the HighEntropyStringsPlugin.

        Args:
            charset (str): The string of characters allowed in the secret (e.g., hex digits).
            limit (float): The minimum entropy score required to be considered a secret.

        Raises:
            ValueError: If the limit is not between 0.0 and 8.0.
        """
        if limit < 0 or limit > 8:
            raise ValueError(
                'The limit set for HighEntropyStrings must be between 0.0 and 8.0',
            )

        self.charset = charset
        self.entropy_limit = limit

        # We require quoted strings to reduce noise.
        # NOTE: We need this to be a capturing group, so back-reference can work.
        self.regex = re.compile(r'([\'"])([{}]+)(\1)'.format(re.escape(charset)))

    def analyze_string(self, string: str, **kwargs: Any) -> Generator[str, None, None]:
        """Finds candidate strings that match the charset within quotes.

        Args:
            string (str): The text content to analyze.
            **kwargs: Arbitrary keyword arguments.

        Yields:
            str: The candidate string content (without quotes).
        """
        for result in self.regex.findall(string):
            if isinstance(result, tuple):
                # This occurs on the default regex, but not on the eager regex.
                result = result[1]

            # We perform the shannon entropy check in `analyze_line` instead, so that we have
            # more control over **when** we display the results of this plugin. Specifically,
            # this allows us to show the computed entropy values during adhoc string scans.
            yield result

    def analyze_line(
        self,
        line: str,
        enable_eager_search: bool = False,
        **kwargs
    ) -> Set[PotentialSecret]:
        """Examines a line and filters results based on entropy limits.

        Args:
            line (str): The line of text to analyze.
            enable_eager_search (bool): If True, returns results even if they don't
                meet the entropy limit (useful for debugging why a secret was missed).
                Defaults to False.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Set[PotentialSecret]: A set of verified PotentialSecret objects.
        """
        output = super().analyze_line(
            line=line,
        )
        if output or not enable_eager_search:
            # NOTE: We perform the limit filter at this layer (rather than analyze_string) so
            # that we can surface secrets that do not meet the limit criteria when
            # enable_eager_search=True.
            return {
                secret
                for secret in (output or set())
                if (
                    self.calculate_shannon_entropy(cast(str, secret.secret_value)) >
                    self.entropy_limit
                )
            }

        # This is mainly used for adhoc string scanning. As such, it's just bad UX to require
        # quotes around the expected secret. In these cases, we only try to search it without
        # requiring quotes when we can't find any results *with* quotes.
        #
        # NOTE: Since we currently assume this is only used for adhoc string scanning, we
        # perform the limit filtering outside this function. This allows us to see *why* secrets
        # have failed to be caught with our configured limit.
        with self.non_quoted_string_regex(is_exact_match=False):
            return super().analyze_line(line=line)

    def calculate_shannon_entropy(self, data: str) -> float:
        """Returns the Shannon entropy of a given string.
        
        This calculates the amount of information (randomness) contained in the string.
        Higher values indicate more randomness.
        Borrowed from: http://blog.dkbza.org/2007/05/scanning-data-for-entropy-anomalies.html.

        Args:
            data (str): The string to calculate entropy for.

        Returns:
            float: The calculated entropy score.
        """
        if not data:
            return 0

        entropy = 0.0
        for x in self.charset:
            p_x = float(data.count(x)) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)

        return entropy
    
    def prepare_secret_result_with_entropy(self, secret: PotentialSecret) -> PotentialSecretResultWithEntropy:
        """Prepare data structures including the calculated entropy score.

        Args:
            secret (PotentialSecret): The secret object.

        Returns:
            PotentialSecretResultWithEntropy: The result dictionary containing entropy.
        """
        entropy = round(self.calculate_shannon_entropy(cast(str, secret.secret_value)), 3)
        is_secret = entropy > self.entropy_limit

        return {
            'is_secret': is_secret,
            'secret_value': secret.secret_value,
            'secret_type': secret.secret_type,
            'entropy': entropy,
        }

    def prepare_secret_result(self, secret: PotentialSecret) -> PotentialSecretResult:
        """Prepare standard data structures for formatting results.

        Args:
            secret (PotentialSecret): The secret object.

        Returns:
            PotentialSecretResult: The standard result dictionary.
        """
        secret_result_with_entropy = self.prepare_secret_result_with_entropy(secret)
        return {
            'is_secret': secret_result_with_entropy['is_secret'],
            'secret_value': secret_result_with_entropy['secret_value'],
            'secret_type': secret_result_with_entropy['secret_type'],
        }

    def format_scan_result(self, secret: PotentialSecret) -> str:
        """Formats the result string to include the entropy score.

        Args:
            secret (PotentialSecret): The secret object.

        Returns:
            str: A string in the format 'True/False (entropy_score)'.
        """
        secret_result_with_entropy = self.prepare_secret_result_with_entropy(secret)
        is_secret_part = 'True' if secret_result_with_entropy['is_secret'] else 'False'
        entropy = secret_result_with_entropy['entropy']
        return f'{is_secret_part} ({entropy})'

    def json(self) -> Dict[str, Any]:
        """Returns a JSON-serializable representation including the entropy limit.

        Returns:
            Dict[str, Any]: A dictionary containing class name and entropy limit.
        """
        return {
            **super().json(),
            'limit': self.entropy_limit,
        }

    @contextmanager
    def non_quoted_string_regex(self, is_exact_match: bool = True) -> Generator[None, None, None]:
        """Context manager to temporarily allow scanning without quotes.

        For certain file formats, strings need not necessarily follow the
        normal convention of being denoted by single or double quotes.

        Args:
            is_exact_match (bool): If True, modifies regex to match the exact string
                anchored to start/end. If False, allows finding the secret embedded
                within a line. Defaults to True.

        Yields:
            None: Context manager yield.
        """
        old_regex = self.regex

        regex_alternative = r'([{}]+)'.format(re.escape(self.charset))
        if is_exact_match:
            regex_alternative = r'^' + regex_alternative + r'$'

        self.regex = re.compile(regex_alternative)

        try:
            yield
        finally:
            self.regex = old_regex


class Base64HighEntropyString(HighEntropyStringsPlugin):
    """Scans for random-looking base64 encoded strings."""
    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: 'Base64 High Entropy String'.
        """
        return 'Base64 High Entropy String'

    def __init__(self, limit: float = 4.5) -> None:
        """Initializes the plugin with Base64 charset.

        Args:
            limit (float): The entropy limit. Defaults to 4.5.
        """
        super().__init__(
            charset=(
                string.ascii_letters
                + string.digits
                + '+/'  # Regular base64
                + '\\-_'  # Url-safe base64
                + '='  # Padding
            ),
            limit=limit,
        )


class HexHighEntropyString(HighEntropyStringsPlugin):
    """Scans for random-looking hex encoded strings."""
    
    @property
    def secret_type(self) -> str:
        """Returns the secret type identifier.

        Returns:
            str: 'Hex High Entropy String'.
        """
        return 'Hex High Entropy String'

    def __init__(self, limit: float = 3.0) -> None:
        """Initializes the plugin with Hex charset.

        Args:
            limit (float): The entropy limit. Defaults to 3.0.
        """
        super().__init__(
            charset=string.hexdigits,
            limit=limit,
        )

    def calculate_shannon_entropy(self, data: str) -> float:
        """Calculates entropy with a penalty for all-digit strings.

        In our investigations, we have found that when the input is all digits,
        the number of false positives we get greatly exceeds realistic true
        positive scenarios.

        Therefore, this tries to capture this heuristic mathematically.

        We do this by noting that the maximum shannon entropy for this charset
        is ~3.32 (e.g. "0123456789", with every digit different), and we want
        to lower that below the standard limit, 3. However, at the same time,
        we also want to accommodate the fact that longer strings have a higher
        chance of being a true positive, which means "01234567890123456789"
        should be closer to the maximum entropy than the shorter version.

        It works by:
        1. Calculating standard entropy.
        2. If the string is all digits, reducing the entropy score.
        3. The reduction is smaller for longer strings (longer strings of digits
           are more likely to be real secrets).

        Args:
            data (str): The hex string to analyze.

        Returns:
            float: The adjusted entropy score.
        """
        entropy = super().calculate_shannon_entropy(data)
        if len(data) == 1:
            return entropy

        try:
            # Check if str is that of a number
            int(data)

            # This multiplier was determined through trial and error, with the
            # intent of keeping it simple, yet achieving our goals.
            entropy -= 1.2 / math.log(len(data), 2)
        except ValueError:
            pass

        return entropy
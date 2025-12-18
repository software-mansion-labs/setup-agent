"""Defines the interfaces for extending plugins.

In most cases, you probably can just use the RegexBasedPlugin. In more advanced cases,
you can also use the LineBasedPlugin, and FileBasedPlugin. If you're extending the BasePlugin,
things may not work as you expect (see the scan logic in SecretsCollection).
"""

import re
from abc import ABCMeta
from abc import abstractmethod
from typing import Any, Dict, Generator, Iterable, Pattern, Set, Optional, TypedDict

from detect_secrets.core.potential_secret import PotentialSecret


class PotentialSecretResult(TypedDict):
    """Typed dictionary representing the structure of a secret result.

    Attributes:
        is_secret (bool): Whether the item is considered a secret.
        secret_value (Optional[str]): The actual string value of the secret, or None.
        secret_type (str): The identifier string for the type of secret.
    """

    is_secret: bool
    secret_value: Optional[str]
    secret_type: str


class BasePlugin(metaclass=ABCMeta):
    """Abstract base class for all plugins."""

    @property
    @abstractmethod
    def secret_type(self) -> str:
        """Unique, user-facing description to identify this type of secret.

        Returns:
            str: The identifier for the secret type.
        """
        raise NotImplementedError

    @abstractmethod
    def analyze_string(self, string: str, **kwargs) -> Generator[str, None, None]:
        """Yields all the raw secret values within a supplied string.

        Args:
            string (str): The text content to analyze.
            **kwargs: Arbitrary keyword arguments.

        Yields:
            str: The raw secret value found in the string.
        """
        raise NotImplementedError

    def analyze_line(self, line: str, **kwargs: Any) -> Set[PotentialSecret]:
        """Examines a line and finds all possible secret values in it.

        Args:
            line (str): The line of text to analyze.
            **kwargs: Arbitrary keyword arguments passed to analyze_string.

        Returns:
            Set[PotentialSecret]: A set of PotentialSecret objects found in the line.
        """
        output = set()
        for match in self.analyze_string(line, **kwargs):
            is_verified: bool = False
            output.add(
                PotentialSecret(
                    secret_type=self.secret_type,
                    secret=match,
                    is_verified=is_verified,
                ),
            )

        return output

    def json(self) -> Dict[str, Any]:
        """Returns a JSON-serializable representation of the plugin.

        Returns:
            Dict[str, Any]: A dictionary containing the class name.
        """
        return {
            "name": self.__class__.__name__,
        }

    def prepare_secret_result(self, secret: PotentialSecret) -> PotentialSecretResult:
        """Prepare any data structures needed for formatting results.

        Args:
            secret (PotentialSecret): The secret object to process.

        Returns:
            PotentialSecretResult: A dictionary containing the formatted secret details.
        """
        if not secret.secret_value and not secret.is_verified:
            return {
                "is_secret": True,
                "secret_value": None,
                "secret_type": secret.secret_type,
            }

        if secret.is_verified:
            return {
                "is_secret": True,
                "secret_value": secret.secret_value,
                "secret_type": secret.secret_type,
            }

        return {
            "is_secret": True,
            "secret_value": None,
            "secret_type": secret.secret_type,
        }

    def format_scan_result(self, secret: PotentialSecret) -> str:
        """Formats the result of a scan for display.

        Args:
            secret (PotentialSecret): The secret object to format.

        Returns:
            str: 'True' if the item is a secret, otherwise 'False'.
        """
        secret_result = self.prepare_secret_result(secret)
        return "True" if secret_result["is_secret"] else "False"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BasePlugin):
            raise NotImplementedError

        return self.json() == other.json()


class RegexBasedDetector(BasePlugin, metaclass=ABCMeta):
    """Parent class for regular-expression based detectors.

    To create a new regex-based detector, subclass this and set `secret_type` with a
    description and `denylist` with a sequence of *compiled* regular expressions.

    Example:
        class FooDetector(RegexBasedDetector):
            secret_type = "foo"
            denylist = (
                re.compile(r'foo'),
            )
    """

    @property
    @abstractmethod
    def denylist(self) -> Iterable[Pattern]:
        """Returns the list of regex patterns to search for.

        Returns:
            Iterable[Pattern]: A sequence of compiled regular expression patterns.
        """
        raise NotImplementedError

    def analyze_string(self, string: str, **kwargs) -> Generator[str, None, None]:
        """Analyzes a string using the defined denylist regex patterns.

        Args:
            string (str): The content to analyze.
            **kwargs: Arbitrary keyword arguments.

        Yields:
            str: Strings matching the denylist patterns.
        """
        for regex in self.denylist:
            for match in regex.findall(string):
                if isinstance(match, tuple):
                    for submatch in filter(bool, match):
                        yield submatch
                else:
                    yield match

    @staticmethod
    def build_assignment_regex(
        prefix_regex: str,
        secret_keyword_regex: str,
        secret_regex: str,
    ) -> Pattern:
        """Generates a regular expression for detecting assignments.

        This method constructs a regex that looks for a secret assignment in the
        following format:

        `<prefix_regex>(-|_|)<secret_keyword_regex> <assignment> <secret_regex>`

        It accounts for:
        * Assignments using `=`, `:`, `:=`, `=>`, or `::`.
        * Optional quotes around key names and values.
        * Optional square brackets.
        * Optional whitespace.

        Args:
            prefix_regex (str): Regex for the prefix of the variable name.
            secret_keyword_regex (str): Regex for the keyword indicating a secret.
            secret_regex (str): Regex for the actual secret value.

        Returns:
            Pattern: A compiled regular expression object ignoring case.
        """
        begin = r"(?:(?<=\W)|(?<=^))"
        opt_quote = r'(?:"|\'|)'
        opt_open_square_bracket = r"(?:\[|)"
        opt_close_square_bracket = r"(?:\]|)"
        opt_dash_underscore = r"(?:_|-|)"
        opt_space = r"(?: *)"
        assignment = r"(?:=|:|:=|=>| +|::)"
        return re.compile(
            r"{begin}{opt_open_square_bracket}{opt_quote}{prefix_regex}{opt_dash_underscore}"
            "{secret_keyword_regex}{opt_quote}{opt_close_square_bracket}{opt_space}"
            "{assignment}{opt_space}{opt_quote}{secret_regex}{opt_quote}".format(
                begin=begin,
                opt_open_square_bracket=opt_open_square_bracket,
                opt_quote=opt_quote,
                prefix_regex=prefix_regex,
                opt_dash_underscore=opt_dash_underscore,
                secret_keyword_regex=secret_keyword_regex,
                opt_close_square_bracket=opt_close_square_bracket,
                opt_space=opt_space,
                assignment=assignment,
                secret_regex=secret_regex,
            ),
            flags=re.IGNORECASE,
        )

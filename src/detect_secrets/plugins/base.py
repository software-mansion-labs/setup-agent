"""
Defines the interfaces for extending plugins.

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
    is_secret: bool
    secret_value: Optional[str]
    secret_type: str

class BasePlugin(metaclass=ABCMeta):
    @property
    @abstractmethod
    def secret_type(self) -> str:
        """
        Unique, user-facing description to identify this type of secret. This should be overloaded
        by declaring a class variable (rather than a `property` function), since we need to know
        a plugin's `secret_type` before initialization.

        NOTE: Choose carefully! If this value is changed, it will require old baselines to be
        updated to use the new secret type.
        """
        raise NotImplementedError

    @abstractmethod
    def analyze_string(self, string: str, **kwargs) -> Generator[str, None, None]:
        """Yields all the raw secret values within a supplied string."""
        raise NotImplementedError

    def analyze_line(
        self,
        line: str,
        **kwargs: Any
    ) -> Set[PotentialSecret]:
        """This examines a line and finds all possible secret values in it."""

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
        return {
            'name': self.__class__.__name__,
        }
    
    def prepare_secret_result(self, secret: PotentialSecret) -> PotentialSecretResult:
        """Prepare any data structures needed for formatting results."""
        if not secret.secret_value and not secret.is_verified:
            return {'is_secret': True, 'secret_value': None, 'secret_type': secret.secret_type}
        
        if secret.is_verified:
            return {'is_secret': True, 'secret_value': secret.secret_value, 'secret_type': secret.secret_type}

        return {
            'is_secret': True,
            'secret_value': None,
            'secret_type': secret.secret_type,
        }

    def format_scan_result(self, secret: PotentialSecret) -> str:
        secret_result = self.prepare_secret_result(secret)
        return 'True' if secret_result['is_secret'] else 'False'

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BasePlugin):
            raise NotImplementedError

        return self.json() == other.json()


class RegexBasedDetector(BasePlugin, metaclass=ABCMeta):
    """Parent class for regular-expression based detectors.

    To create a new regex-based detector, subclass this and set `secret_type` with a
    description and `denylist` with a sequence of *compiled* regular expressions, like:

    class FooDetector(RegexBasedDetector):

        secret_type = "foo"

        denylist = (
            re.compile(r'foo'),
        )
    """
    @property
    @abstractmethod
    def denylist(self) -> Iterable[Pattern]:
        raise NotImplementedError

    def analyze_string(self, string: str, **kwargs) -> Generator[str, None, None]:
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
        """Generate assignment regex
        It reads 3 input parameters, each stands for regex. The return regex would look for
        secret in following format.
        <prefix_regex>(-|_|)<secret_keyword_regex> <assignment> <secret_regex>
        assignment would include =,:,:=,::
        keyname and value supports optional quotes
        """
        begin = r'(?:(?<=\W)|(?<=^))'
        opt_quote = r'(?:"|\'|)'
        opt_open_square_bracket = r'(?:\[|)'
        opt_close_square_bracket = r'(?:\]|)'
        opt_dash_underscore = r'(?:_|-|)'
        opt_space = r'(?: *)'
        assignment = r'(?:=|:|:=|=>| +|::)'
        return re.compile(
            r'{begin}{opt_open_square_bracket}{opt_quote}{prefix_regex}{opt_dash_underscore}'
            '{secret_keyword_regex}{opt_quote}{opt_close_square_bracket}{opt_space}'
            '{assignment}{opt_space}{opt_quote}{secret_regex}{opt_quote}'.format(
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
            ), flags=re.IGNORECASE,
        )

from typing import Any
from typing import Generator
from typing import Iterable
from typing import List

from detect_secrets.settings import get_filters
from detect_secrets.settings import get_settings
from detect_secrets.types import SelfAwareCallable
from detect_secrets.util.code_snippet import CodeSnippet
from detect_secrets.util.code_snippet import get_code_snippet
from detect_secrets.util.inject import call_function_with_arguments
from detect_secrets.core.log import log
from detect_secrets.core.potential_secret import PotentialSecret
from detect_secrets.plugins.base import BasePlugin


def scan_line(line: str, plugins: List[BasePlugin]) -> Generator[PotentialSecret, None, None]:
    """Used for adhoc string scanning."""
    context = get_code_snippet(lines=[line], line_number=1)

    yield from (
        secret
        for plugin in plugins
        for secret in _scan_line(
            plugin=plugin,
            filename='adhoc-string-scan',
            line=line,
            line_number=0,
            enable_eager_search=True,
            context=context,
        )
        if not _is_filtered_out(
            required_filter_parameters=['context'],
            filename=secret.filename,
            secret=secret.secret_value,
            plugin=plugin,
            line=line,
            context=context,
        )
    )

def _scan_line(
    plugin: BasePlugin,
    filename: str,
    line: str,
    line_number: int,
    context: CodeSnippet,
    **kwargs: Any,
) -> Generator[PotentialSecret, None, None]:
    # NOTE: We don't apply filter functions here yet, because we don't have any filters
    # that operate on (filename, line, plugin) without `secret`
    secrets = plugin.analyze_line(
        filename=filename,
        line=line,
        line_number=line_number,
        context=context,
        **kwargs
    )
    if not secrets:
        return

    yield from (
        secret
        for secret in secrets
        if not _is_filtered_out(
            required_filter_parameters=['secret'],
            filename=secret.filename,
            secret=secret.secret_value,
            plugin=plugin,
            line=line,
        )
    )


def _is_filtered_out(required_filter_parameters: Iterable[str], **kwargs: Any) -> bool:
    for filter_fn in get_filters_with_parameter(*required_filter_parameters):
        try:
            if call_function_with_arguments(filter_fn, **kwargs):
                if 'secret' in kwargs:
                    debug_msg = f'Skipping "{0}" due to `{1}`.'.format(
                        kwargs['secret'],
                        filter_fn.path,
                    )
                elif list(kwargs.keys()) == ['filename']:
                    # We want to make sure this is only run if we're skipping files (as compared
                    # to other filters that may include `filename` as a parameter).
                    debug_msg = 'Skipping "{0}" due to `{1}`'.format(
                        kwargs['filename'],
                        filter_fn.path,
                    )
                else:
                    debug_msg = 'Skipping secret due to `{0}`.'.format(filter_fn.path)

                log.info(debug_msg)
                return True
        except TypeError:
            pass

    return False


def get_filters_with_parameter(*parameters: str) -> List[SelfAwareCallable]:
    """
    The issue of our method of dependency injection is that functions will be called multiple
    times. For example, if we have two functions:

    >>> def foo(filename: str): ...
    >>> def bar(filename: str, secret: str): ...

    our invocation of `call_function_with_arguments(filename=filename, secret=secret)`
    will run both of these functions. While expected, this results in multiple invocations of
    the same function, which can be less than ideal (especially if we have a heavy duty filter).

    To address this, we filter our filters with this function. It will return the functions
    that accept a minimum set of parameters, to avoid duplicative work. For instance,

    >>> get_filters_with_parameter('secret')
    [bar]
    """
    minimum_parameters = set(parameters)

    return [
        filter
        for filter in get_filters()
        if minimum_parameters <= filter.injectable_variables
    ]

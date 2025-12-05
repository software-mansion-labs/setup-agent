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


def _is_filtered_out(secret: str, plugin: BasePlugin) -> bool:
    return any(filter.should_exclude(secret=secret, plugin=plugin) for filter in get_filters())

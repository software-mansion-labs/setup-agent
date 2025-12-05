from typing import Any
from typing import Generator
from typing import List

from detect_secrets.settings import get_filters
from detect_secrets.core.potential_secret import PotentialSecret
from detect_secrets.plugins.base import BasePlugin


def scan_line(line: str, plugins: List[BasePlugin]) -> Generator[PotentialSecret, None, None]:
    """Used for adhoc string scanning."""
    yield from (
        secret
        for plugin in plugins
        for secret in _scan_line(
            plugin=plugin,
            line=line,
            enable_eager_search=True,
        )
        if not _is_filtered_out(
            secret=secret.secret_value,
            plugin=plugin,
        )
    )

def _scan_line(
    plugin: BasePlugin,
    line: str,
    **kwargs: Any,
) -> Generator[PotentialSecret, None, None]:
    secrets = plugin.analyze_line(
        line=line,
        **kwargs
    )
    if not secrets:
        return

    yield from (
        secret
        for secret in secrets
        if not _is_filtered_out(
            secret=secret.secret_value,
            plugin=plugin,
        )
    )


def _is_filtered_out(secret: str, plugin: BasePlugin) -> bool:
    return any(filter.should_exclude(secret=secret, plugin=plugin) for filter in get_filters())

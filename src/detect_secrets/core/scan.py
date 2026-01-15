from typing import Any, Generator, List

from detect_secrets.core.potential_secret import PotentialSecret
from detect_secrets.plugins.base import BasePlugin
from detect_secrets.settings import get_filters


def scan_line(
    line: str, plugins: List[BasePlugin]
) -> Generator[PotentialSecret, None, None]:
    """
    Function for adhoc string scanning.

    Args:
        line (str): String to scan.
        plugins (List[BasePlugin]): List of plugins to use for scanning.

    Returns:
        Generator[PotentialSecret, None, None]: Generator of PotentialSecret objects.
    """
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
    """
    Function to scan a line with a given plugin.

    Args:
        plugin (BasePlugin): Plugin to use for scanning.
        line (str): String to scan.
        **kwargs (Any): Additional arguments.

    Returns:
        Generator[PotentialSecret, None, None]: Generator of PotentialSecret objects.
    """
    secrets = plugin.analyze_line(line=line, **kwargs)
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
    """
    Function to check if a secret should be filtered out.

    Args:
        secret (str): Secret to check.
        plugin (BasePlugin): Plugin to use for checking.

    Returns:
        bool: True if the secret should be filtered out, False otherwise.
    """
    return any(
        filter.should_exclude(secret=secret, plugin=plugin) for filter in get_filters()
    )

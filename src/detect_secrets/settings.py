from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from importlib import import_module
from typing import Any
from typing import Dict
from typing import List
from urllib.parse import urlparse
from detect_secrets.plugins.base import BasePlugin

from .exceptions import InvalidFile
from .util.importlib import import_file_as_module

from detect_secrets.plugins import (
    ArtifactoryDetector,
    AWSKeyDetector,
    AzureStorageKeyDetector,
    Base64HighEntropyString,
    BasicAuthDetector,
    CloudantDetector,
    DiscordBotTokenDetector,
    GitHubTokenDetector,
    GitLabTokenDetector,
    HexHighEntropyString,
    IbmCloudIamDetector,
    IbmCosHmacDetector,
    IPPublicDetector,
    JwtTokenDetector,
    KeywordDetector,
    MailchimpDetector,
    NpmDetector,
    OpenAIDetector,
    PrivateKeyDetector,
    PypiTokenDetector,
    SendGridDetector,
    SlackDetector,
    SoftlayerDetector,
    SquareOAuthDetector,
    StripeDetector,
    TelegramBotTokenDetector,
    TwilioKeyDetector,
)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    This is essentially a singleton pattern, that allows for (controlled) global access
    to common variables.
    """
    return Settings()


def configure_settings_from_baseline(baseline: Dict[str, Any], filename: str = '') -> Settings:
    """
    :raises: KeyError
    """
    settings = get_settings()

    if 'plugins_used' in baseline:
        settings.configure_plugins(baseline['plugins_used'])

    if 'filters_used' in baseline:
        settings.configure_filters(baseline['filters_used'])

        if 'detect_secrets.filters.wordlist.should_exclude_secret' in settings.filters:
            config = settings.filters['detect_secrets.filters.wordlist.should_exclude_secret']

            from detect_secrets.filters import wordlist
            wordlist.initialize(
                wordlist_filename=config['file_name'],
                min_length=config['min_length'],
            )

        if 'detect_secrets.filters.gibberish.should_exclude_secret' in settings.filters:
            config = settings.filters['detect_secrets.filters.gibberish.should_exclude_secret']

            from detect_secrets.filters import gibberish
            gibberish.initialize(
                model_path=config.get('model'),
                limit=config['limit'],
            )

    if filename:
        settings.filters['detect_secrets.filters.common.is_baseline_file'] = {
            'filename': filename,
        }

    return settings

class Settings:
    from detect_secrets.filters.heuristic import is_sequential_string

    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        # mapping of class names to initialization variables
        self.plugins: Dict[str, Dict[str, Any]] = {}

        # mapping of python import paths to configuration variables
        self.filters: Dict[str, Dict[str, Any]] = {
            path: {}
            for path in {
                'detect_secrets.filters.heuristic.is_sequential_string',
                'detect_secrets.filters.heuristic.is_potential_uuid',
                'detect_secrets.filters.heuristic.is_likely_id_string',
                'detect_secrets.filters.heuristic.is_templated_secret',
                'detect_secrets.filters.heuristic.is_prefixed_with_dollar_sign',
                'detect_secrets.filters.heuristic.is_indirect_reference',
                'detect_secrets.filters.heuristic.is_lock_file',
                'detect_secrets.filters.heuristic.is_not_alphanumeric_string',
                'detect_secrets.filters.heuristic.is_swagger_file',
            }
        }

    def configure_plugins(self, config: List[Dict[str, Any]]) -> 'Settings':
        """
        :param config: e.g.
            [
                {'name': 'AWSKeyDetector'},
                {'limit': 4.5, 'name': 'Base64HighEntropyString'}
            ]
        """
        for plugin in config:
            plugin = {**plugin}
            name = plugin.pop('name')
            self.plugins[name] = plugin

        get_plugins.cache_clear()
        return self

    def disable_plugins(self, *plugin_names: str) -> 'Settings':
        for name in plugin_names:
            try:
                self.plugins.pop(name)
            except KeyError:
                pass

        get_plugins.cache_clear()
        return self

    def configure_filters(self, config: List[Dict[str, Any]]) -> 'Settings':
        """
        :param config: e.g.
            [
                {'path': 'detect_secrets.filters.heuristic.is_sequential_string'},
                {
                    'path': 'detect_secrets.filters.regex.should_exclude_files',
                    'pattern': '^test.*',
                }
            ]
        """
        self.filters = {}

        # Make a copy, so we don't affect the original.
        filter_configs = deepcopy(config)
        for filter_config in filter_configs:
            path = filter_config['path']
            self.filters[path] = filter_config

        get_filters.cache_clear()
        return self

    def disable_filters(self, *filter_paths: str) -> 'Settings':
        for filter_path in filter_paths:
            self.filters.pop(filter_path, None)

        get_filters.cache_clear()
        return self


@lru_cache(maxsize=1)
def get_plugins() -> List[BasePlugin]:
    return [
        ArtifactoryDetector(),
        AWSKeyDetector(),
        AzureStorageKeyDetector(),
        Base64HighEntropyString(),
        BasicAuthDetector(),
        CloudantDetector(),
        DiscordBotTokenDetector(),
        GitHubTokenDetector(),
        GitLabTokenDetector(),
        HexHighEntropyString(),
        IbmCloudIamDetector(),
        IbmCosHmacDetector(),
        IPPublicDetector(),
        JwtTokenDetector(),
        KeywordDetector(),
        MailchimpDetector(),
        NpmDetector(),
        OpenAIDetector(),
        PrivateKeyDetector(),
        PypiTokenDetector(),
        SendGridDetector(),
        SlackDetector(),
        SoftlayerDetector(),
        SquareOAuthDetector(),
        StripeDetector(),
        TelegramBotTokenDetector(),
        TwilioKeyDetector(),
    ]


@lru_cache(maxsize=1)
def get_filters() -> List:
    from .core.log import log
    from .util.inject import get_injectable_variables

    output = []
    for path, config in get_settings().filters.items():
        parts = urlparse(path)
        if not parts.scheme:
            module_path, function_name = path.rsplit('.', 1)
            try:
                function = getattr(import_module(module_path), function_name)
            except (ModuleNotFoundError, AttributeError):
                log.warning(f'Invalid filter: {path}')
                continue

        elif parts.scheme == 'file':
            file_path, function_name = path[len('file://'):].split('::')

            try:
                function = getattr(import_file_as_module(file_path), function_name)
            except (FileNotFoundError, InvalidFile, AttributeError):
                log.warning(f'Invalid filter: {path}')
                continue

        else:
            log.warning(f'Invalid filter: {path}')
            continue

        # We attach this metadata to the function itself, so that we don't need to
        # compute it everytime. This will allow for dependency injection for filters.
        function.injectable_variables = set(get_injectable_variables(function))
        output.append(function)

        # This is for better logging.
        function.path = path

    return output

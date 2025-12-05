from __future__ import annotations
from functools import lru_cache
from typing import List

from detect_secrets.filters.filters import (
    SequentialStringFilter,
    UUIDFilter,
    TemplatedSecretFilter,
    NotAlphanumericFilter,
    GibberishFilter,
)
from detect_secrets.filters.base_secret_filter import BaseSecretFilter

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
    BasePlugin,
)

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
def get_filters() -> List[BaseSecretFilter]:
    """
    Returns the hardcoded list of active filters.
    """

    filters: List[BaseSecretFilter] = [
        SequentialStringFilter(),
        UUIDFilter(),
        TemplatedSecretFilter(),
        NotAlphanumericFilter(),
        GibberishFilter()
    ]

    return filters
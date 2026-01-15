from functools import lru_cache
from typing import List

from detect_secrets.filters.base_secret_filter import BaseSecretFilter
from detect_secrets.filters.filters import (
    GibberishFilter,
    NotAlphanumericFilter,
    SequentialStringFilter,
    TemplatedSecretFilter,
    UUIDFilter,
)
from detect_secrets.plugins import (
    ArtifactoryDetector,
    AWSKeyDetector,
    AzureStorageKeyDetector,
    Base64HighEntropyString,
    BasePlugin,
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
    filters = [
        SequentialStringFilter(),
        UUIDFilter(),
        TemplatedSecretFilter(),
        NotAlphanumericFilter(),
        GibberishFilter(),
    ]

    return filters

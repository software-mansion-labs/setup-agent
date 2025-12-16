from enum import Enum

class SuggestedModels(str, Enum):
    CLAUDE_SONNET_4_5 = "anthropic:claude-sonnet-4-5"
    CLAUDE_OPUS_3 = "anthropic:claude-3-opus"
    GPT_4o = "openai:gpt-4o"

DEFAULT_MODEL = SuggestedModels.CLAUDE_SONNET_4_5
from functools import lru_cache
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

@lru_cache(maxsize=1)
def get_llm(model: str = "openai:gpt-4o") -> BaseChatModel:
    """Return a shared instance of ChatOpenAI, initialized lazily."""

    return init_chat_model(model=model)

from __future__ import annotations
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional
from utils.singleton_meta import SingletonMeta


class LLMManager(metaclass=SingletonMeta):
    """
    Singleton class for managing a shared LLM instance.
    Lazily initializes the model, and allows re-initialization via CLI or code.
    """

    def __init__(self, model: str = "anthropic:claude-sonnet-4-5") -> None:
        self._model_name = model
        self._llm: Optional[BaseChatModel] = None

    @classmethod
    def init(cls, model: str = "anthropic:claude-sonnet-4-5") -> LLMManager:
        """
        Initialize or reinitialize the singleton with a specific model.
        Returns the shared LLMManager instance.
        """
        instance = cls(model)
        instance._model_name = model
        instance._llm = init_chat_model(model=model)
        return instance

    @classmethod
    def get(cls) -> LLMManager:
        """
        Return the existing LLMManager instance.
        Raises an error if not initialized first.
        """
        if cls._instance is None:
            raise RuntimeError("LLMManager not initialized. Call LLMManager.init() first.")
        return cls._instance

    def get_llm(self) -> BaseChatModel:
        """
        Return the underlying LLM instance, lazily initializing if needed.
        """
        if self._llm is None:
            self._llm = init_chat_model(model=self._model_name)
        return self._llm

    @property
    def model_name(self) -> str:
        """Return the name of the current model."""
        return self._model_name

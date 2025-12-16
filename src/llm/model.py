from __future__ import annotations
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional, TypedDict, cast
from utils.singleton_meta import SingletonMeta
from llm.constants import DEFAULT_MODEL


class LLMParams(TypedDict, total=False):
    model: str
    max_tokens: Optional[int]
    temperature: Optional[float]
    timeout: Optional[float]
    max_retries: Optional[int]


class LLMManager(metaclass=SingletonMeta):
    """
    Singleton class for managing a shared LLM instance.
    Lazily initializes the model, and allows re-initialization via CLI or code.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        self._model_name = model
        self._llm: Optional[BaseChatModel] = None
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._timeout = timeout
        self._max_retries = max_retries

    @classmethod
    def init(
        cls,
        model: str = DEFAULT_MODEL,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> LLMManager:
        """
        Initialize or reinitialize the singleton with specific model parameters.
        Only parameters explicitly provided (not None) will be passed to the factory.
        """
        instance = cls(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
        )

        return instance

    @classmethod
    def get(cls) -> LLMManager:
        """
        Return the existing LLMManager instance.
        Raises an error if not initialized first.
        """
        if cls._instance is None:
            raise RuntimeError(
                "LLMManager not initialized. Call LLMManager.init() first."
            )
        return cls._instance

    def init_llm(self) -> BaseChatModel:
        params: LLMParams = {
            "model": self._model_name,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "timeout": self._timeout,
            "max_retries": self._max_retries,
        }

        active_params = cast(
            LLMParams, {k: v for k, v in params.items() if v is not None}
        )

        self._llm = init_chat_model(**active_params)
        return self._llm

    def get_llm(self) -> BaseChatModel:
        """
        Return the underlying LLM instance, lazily initializing if needed.
        """
        if self._llm is None:
            return init_chat_model(model=self._model_name, max_tokens=self._max_tokens)
        return self._llm

    @property
    def model_name(self) -> str:
        """Return the name of the current model."""
        return self._model_name

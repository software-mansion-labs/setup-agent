from __future__ import annotations
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional, TypedDict, cast
from utils.singleton_meta import SingletonMeta
from llm.constants import DEFAULT_MODEL


class LLMParams(TypedDict, total=False):
    """Defines the configuration parameters available for the LLM.

    Attributes:
        model (str): The name or identifier of the model (e.g., "gpt-4o").
        max_tokens (Optional[int]): The maximum number of tokens to generate.
        temperature (Optional[float]): The sampling temperature.
        timeout (Optional[float]): The request timeout in seconds.
        max_retries (Optional[int]): The maximum number of retries for failed requests.
    """

    model: str
    max_tokens: Optional[int]
    temperature: Optional[float]
    timeout: Optional[float]
    max_retries: Optional[int]


class LLMManager(metaclass=SingletonMeta):
    """Singleton class for managing a shared LLM instance.

    Lazily initializes the model and allows re-initialization via CLI or code
    to switch configurations globally.

    Attributes:
        _model_name (str): The name of the model to be used.
        _llm (Optional[BaseChatModel]): The cached LangChain model instance.
        _max_tokens (Optional[int]): Configured max tokens.
        _temperature (Optional[float]): Configured temperature.
        _timeout (Optional[float]): Configured timeout.
        _max_retries (Optional[int]): Configured max retries.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """Initializes the LLMManager with specific configuration settings.

        Args:
            model (str): The model name. Defaults to DEFAULT_MODEL.
            max_tokens (Optional[int]): The maximum tokens to generate. Defaults to None.
            temperature (Optional[float]): The sampling temperature. Defaults to None.
            timeout (Optional[float]): The request timeout. Defaults to None.
            max_retries (Optional[int]): The maximum retries. Defaults to None.
        """
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
        """Initialize or reinitialize the singleton with specific model parameters.

        Only parameters explicitly provided (not None) will be passed to the factory.

        Args:
            model (str): The model name. Defaults to DEFAULT_MODEL.
            max_tokens (Optional[int]): The maximum tokens to generate. Defaults to None.
            temperature (Optional[float]): The sampling temperature. Defaults to None.
            timeout (Optional[float]): The request timeout. Defaults to None.
            max_retries (Optional[int]): The maximum retries. Defaults to None.

        Returns:
            LLMManager: The initialized singleton instance.
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
        """Return the existing LLMManager instance.

        Returns:
            LLMManager: The current singleton instance.

        Raises:
            RuntimeError: If the manager has not been initialized via `LLMManager.init()` first.
        """
        if cls._instance is None:
            raise RuntimeError(
                "LLMManager not initialized. Call LLMManager.init() first."
            )
        return cls._instance

    def init_llm(self) -> BaseChatModel:
        """Initializes the underlying LangChain BaseChatModel based on stored config.

        This method filters out None values from the configuration to ensure
        default behaviors are preserved by the backend.

        Returns:
            BaseChatModel: The initialized LangChain chat model.
        """
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
        """Return the underlying LLM instance, lazily initializing if needed.

        Returns:
            BaseChatModel: The active LangChain chat model instance.
        """
        if self._llm is None:
            return self.init_llm()
        return self._llm

    @property
    def model_name(self) -> str:
        return self._model_name

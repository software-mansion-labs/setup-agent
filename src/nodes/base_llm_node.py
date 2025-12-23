from pydantic import BaseModel
from llm.structured_llm import StructuredLLM
from typing import Type, TypeVar
from abc import abstractmethod, ABC
from utils.logger import LoggerFactory
from langchain.agents import AgentState
from langgraph.graph import MessagesState
from typing import Union, Generic

T = TypeVar("T", bound=BaseModel)
K = TypeVar("K", bound=Union[AgentState, MessagesState])


class BaseLLMNode(ABC, Generic[K]):
    """
    Abstract base class for all agents.
    Provides shared interface and utility methods.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._llm = StructuredLLM()
        self.logger = LoggerFactory.get_logger(name=name)

    def _invoke_structured_llm(
        self, schema: Type[T], system_message: str, input_text: str
    ) -> T:
        """
        Invoke the LLM with a structured output schema.
        Accepts a Pydantic model class (Type[BaseModel]).
        Returns a parsed Pydantic object (schema).
        """
        return self._llm.invoke(
            schema=schema, system_message=system_message, input_text=input_text
        )

    @abstractmethod
    def invoke(self, state: K) -> K:
        """
        Abstract method that must be implemented by subclasses.
        Executes the node logic using the provided state and returns the updated state.
        """
        pass

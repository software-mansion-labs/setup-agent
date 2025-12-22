from abc import abstractmethod

from nodes.base_llm_node import BaseLLMNode
from typing import TypeVar, Generic
from langchain.agents.middleware import AgentState
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import MessagesState

T = TypeVar("T", bound=AgentState)
K = TypeVar("K", bound=MessagesState)


class BaseCustomAgent(BaseLLMNode, Generic[T, K]):
    """
    Abstract base class for all agents.
    Provides shared interface and utility methods.
    """

    def __init__(
        self,
        name: str,
    ) -> None:
        super().__init__(name=name)

    @abstractmethod
    def _build_agent_workflow(self) -> CompiledStateGraph[T, None, T, T]:
        pass

    @abstractmethod
    def invoke(self, state: K) -> K:
        """
        Abstract method that must be implemented by subclasses.
        Executes the agent logic using the provided GraphState and returns the updated GraphState.
        """
        pass

from abc import abstractmethod

from nodes.base_llm_node import BaseLLMNode
from typing import TypeVar, Generic
from langchain.agents.middleware import AgentState
from langgraph.graph import StateGraph

K = TypeVar("K", bound=AgentState)

class BaseCustomAgent(BaseLLMNode, Generic[K]):
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
    def _build_agent_workflow(self) -> StateGraph:
        pass
        
    @abstractmethod
    def invoke(self, state: K) -> K:
        """
        Abstract method that must be implemented by subclasses.
        Executes the agent logic using the provided GraphState and returns the updated GraphState.
        """
        pass

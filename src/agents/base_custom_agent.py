from abc import abstractmethod

from nodes.base_llm_node import BaseLLMNode
from typing import TypeVar, Generic
from langchain.agents.middleware import AgentState
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import MessagesState

T = TypeVar("T", bound=AgentState)
K = TypeVar("K", bound=MessagesState)


class BaseCustomAgent(BaseLLMNode, Generic[T, K]):
    """Abstract base class for all custom agents in the workflow.

    Provides a shared interface and utility structure for agents that manage
    their own internal LangGraph workflows.

    Attributes:
        name (str): The unique identifier for this agent.

    Type Parameters:
        T: The internal state type used by the agent's subgraph (bound to AgentState).
        K: The external/global state type passed to the agent (bound to MessagesState).
    """

    def __init__(
        self,
        name: str,
    ) -> None:
        """Initializes the BaseCustomAgent.

        Args:
            name: The name of the agent node (e.g., "planner_agent").
        """
        super().__init__(name=name)

    @abstractmethod
    def _build_agent_workflow(self) -> CompiledStateGraph[T, None, T, T]:
        """Constructs and compiles the internal workflow graph for the agent.

        This abstract method must be implemented by subclasses to define the
        nodes, edges, and state transitions specific to the agent's task.

        Returns:
            CompiledStateGraph[T, None, T, T]: The compiled internal graph ready for execution.
        """
        pass

    @abstractmethod
    def invoke(self, state: K) -> K:
        """Executes the agent logic.

        This abstract method serves as the entry point for the agent when called
        by the main graph. It typically initializes the internal state (T) from
        the global state (K), runs the subgraph, and maps the results back.

        Args:
            state (K): The current global graph state.

        Returns:
            K: The updated global graph state after the agent has completed its work.
        """
        pass

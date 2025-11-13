from abc import abstractmethod

from graph_state import GraphState
from uuid import UUID
from typing import Sequence
from langchain.tools import BaseTool
from typing import Optional
from pydantic import BaseModel
from typing import Type, TypeVar
from agents.base_agent import BaseAgent, CustomAgentState

T = TypeVar("T", bound=BaseModel)
K = TypeVar("K", bound=CustomAgentState)

class StructuredAgentState(CustomAgentState):
    shell_id: Optional[UUID]


class BaseStructuredAgent(BaseAgent):
    """
    Abstract base class for all agents with structured output.
    Provides shared interface and utility methods.
    """

    def __init__(
        self,
        name: str,
        prompt: str,
        tools: Sequence[BaseTool] = [],
        parallel_tool_calls: bool = False,
        state_schema: Optional[Type[K]] = StructuredAgentState,
        response_format: Optional[Type[T]] = None,
    ):
        super().__init__(
            name=name,
            prompt=prompt,
            tools=tools,
            parallel_tool_calls=parallel_tool_calls,
            state_schema=state_schema,
            response_format=response_format
        )

    @abstractmethod
    def invoke(self, state: GraphState) -> GraphState:
        """
        Abstract method that must be implemented by subclasses.
        Executes the agent logic using the provided GraphState and returns the updated GraphState.
        """
        pass

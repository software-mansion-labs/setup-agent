from abc import abstractmethod

from graph_state import GraphState
from langchain.agents import create_agent
from uuid import UUID
from typing import Sequence
from langchain.tools import BaseTool
from typing import Optional
from nodes.base_llm_node import BaseLLMNode
from pydantic import BaseModel
from typing import Type, TypeVar
from langchain.agents.middleware import AgentState
from middlewares import ParallelToolCallsMiddleware


class CustomAgentState(AgentState):
    agent_name: str
    shell_id: Optional[UUID]

T = TypeVar("T", bound=BaseModel)
K = TypeVar("K", bound=CustomAgentState)


class BaseAgent(BaseLLMNode):
    """
    Abstract base class for all agents.
    Provides shared interface and utility methods.
    """

    def __init__(
        self,
        name: str,
        prompt: str,
        tools: Sequence[BaseTool] = [],
        parallel_tool_calls: bool = False,
        state_schema: Optional[Type[K]] = CustomAgentState,
        response_format: Optional[Type[T]] = None,
    ):
        super().__init__(name=name)

        self.agent = create_agent(
            model=self._llm.get_raw_llm(),
            tools=tools,
            name=name,
            system_prompt=prompt,
            state_schema=state_schema,
            response_format=response_format,
            middleware=[ParallelToolCallsMiddleware(parallel_tool_calls=parallel_tool_calls)]
        )
        
    @abstractmethod
    def invoke(self, state: GraphState) -> GraphState:
        """
        Abstract method that must be implemented by subclasses.
        Executes the agent logic using the provided GraphState and returns the updated GraphState.
        """
        pass

from abc import abstractmethod

from graph_state import GraphState
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.prebuilt import create_react_agent
from uuid import UUID
from typing import Sequence
from langchain.tools import BaseTool
from typing import Optional
from nodes.base_llm_node import BaseLLMNode
from pydantic import BaseModel
from typing import Type, TypeVar

T = TypeVar("T", bound=BaseModel)

class CustomAgentState(AgentState):
    shell_id: Optional[UUID]
    structured_response: Optional[BaseModel]


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
        response_format: Optional[Type[T]] = None
    ):
        super().__init__(name=name)
        self.agent = create_react_agent(
            model=self._llm.get_raw_llm().bind_tools(
                tools=tools, parallel_tool_calls=parallel_tool_calls
            ),
            tools=tools,
            name=name,
            prompt=prompt,
            state_schema=CustomAgentState,
            response_format=response_format
        )

    @abstractmethod
    def invoke(self, state: GraphState) -> GraphState:
        """
        Abstract method that must be implemented by subclasses.
        Executes the agent logic using the provided GraphState and returns the updated GraphState.
        """
        pass

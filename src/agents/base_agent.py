from abc import abstractmethod

from graph_state import GraphState
from langchain.agents import create_agent
from uuid import UUID
from typing import Any, Sequence
from langchain.tools import BaseTool
from typing import Optional
from langgraph.runtime import Runtime
from nodes.base_llm_node import BaseLLMNode
from pydantic import BaseModel
from typing import Type, TypeVar
from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.agents.middleware import ModelRequest, ModelResponse
from typing import Callable


class CustomAgentState(AgentState):
    agent_name: str
    shell_id: Optional[UUID]

T = TypeVar("T", bound=BaseModel)
K = TypeVar("K", bound=CustomAgentState)


class CustomMiddleware(AgentMiddleware):
    def __init__(self, parallel_tool_calls: bool = False) -> None:
        self.parallel_tool_calls = parallel_tool_calls

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        model_settings = request.model_settings.copy()
        model_settings.update({"parallel_tool_calls": self.parallel_tool_calls})
        
        request.override(model_settings=model_settings)

        return handler(request)

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
            middleware=[CustomMiddleware(parallel_tool_calls=parallel_tool_calls)]
        )
        
    @abstractmethod
    def invoke(self, state: GraphState) -> GraphState:
        """
        Abstract method that must be implemented by subclasses.
        Executes the agent logic using the provided GraphState and returns the updated GraphState.
        """
        pass

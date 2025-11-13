from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware import ModelRequest, ModelResponse
from typing import Callable


class ParallelToolCallsMiddleware(AgentMiddleware):
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

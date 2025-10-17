from pydantic import BaseModel
from src.model import get_llm
from langchain.prompts import ChatPromptTemplate
from typing import Type, TypeVar
from abc import abstractmethod, ABC
from src.graph_state import GraphState

T = TypeVar("T", bound=BaseModel)


class BaseLLMNode(ABC):
    """
    Abstract base class for all agents.
    Provides shared interface and utility methods.
    """

    def __init__(self, name: str):
        self.name = name
        self._llm = get_llm()

    def _invoke_structured_llm(
        self, schema: Type[T], system_message: str, input_text: str
    ) -> T:
        """
        Invoke the LLM with a structured output schema.
        Accepts a Pydantic model class (Type[BaseModel]).
        Returns a parsed Pydantic object (schema).
        """
        structured_llm = self._llm.with_structured_output(schema, method="json_mode")

        system_message = (
            system_message
            + "\n\nIMPORTANT: Always return valid JSON that conforms to the schema."
        )

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("human", "{input}")]
        )

        chain = prompt | structured_llm
        raw_result = chain.invoke({"input": input_text})

        if isinstance(raw_result, dict):
            return schema.model_validate(raw_result)
        elif isinstance(raw_result, BaseModel):
            return schema.model_validate(raw_result.model_dump())
        else:
            raise TypeError(f"Unexpected return type: {type(raw_result)}")

    @abstractmethod
    def invoke(self, state: GraphState) -> GraphState:
        """
        Abstract method that must be implemented by subclasses.
        Executes the node logic using the provided GraphState and returns the updated GraphState.
        """
        pass

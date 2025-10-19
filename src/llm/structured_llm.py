from pydantic import BaseModel
from llm.model import get_llm
from langchain.prompts import ChatPromptTemplate
from typing import Type, TypeVar

T = TypeVar("T", bound=BaseModel)


class StructuredLLM:
    """
    Abstract base class for all agents.
    Provides shared interface and utility methods.
    """

    def __init__(self):
        self._llm = get_llm()

    def invoke(
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

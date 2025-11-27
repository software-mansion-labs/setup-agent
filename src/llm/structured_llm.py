from pydantic import BaseModel
from llm.model import LLMManager
from langchain_core.prompts import ChatPromptTemplate
from typing import Type, TypeVar
from langchain_core.language_models.chat_models import BaseChatModel

T = TypeVar("T", bound=BaseModel)


class StructuredLLM:
    """
    Abstract base class for all agents.
    Provides shared interface and utility methods.
    """

    def __init__(self):
        llm_manager = LLMManager.get()
        self._raw_llm = llm_manager.get_llm()

    def invoke(self, schema: Type[T], system_message: str, input_text: str) -> T:
        """
        Invoke the LLM with a structured output schema.
        Args:
            schema (Type[T]): The Pydantic model class defining the expected output structure.
            system_message (str): The system prompt to guide the LLM's behavior and context.
            input_text (str): The actual input text or query to be processed by the LLM.

        Returns:
            T: An instance of the provided Pydantic model class populated with the LLM's response.
        """
        structured_llm = self._raw_llm.with_structured_output(
            schema, method="json_schema"
        )

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

    @property
    def raw_llm(self) -> BaseChatModel:
        return self._raw_llm

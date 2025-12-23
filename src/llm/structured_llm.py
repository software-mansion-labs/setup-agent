from pydantic import BaseModel
from llm.model import LLMManager
from langchain_core.prompts import ChatPromptTemplate
from typing import Type, TypeVar, List
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AnyMessage

T = TypeVar("T", bound=BaseModel)


class StructuredLLM:
    """Wrapper around BaseChatModel to facilitate structured Pydantic outputs.

    This class retrieves the shared LLM instance from LLMManager and provides
    utility methods to invoke the LLM while enforcing a specific JSON schema
    defined by a Pydantic model.

    Attributes:
        _raw_llm (BaseChatModel): The underlying LangChain chat model instance.
    """

    def __init__(self) -> None:
        """Initializes the StructuredLLM.

        Retrieves the globally configured LLM instance to ensure consistency
        across the application.
        """
        llm_manager = LLMManager.get()
        self._raw_llm = llm_manager.get_llm()

    def invoke(self, schema: Type[T], system_message: str, input_text: str) -> T:
        """Generates a structured response based on a system prompt and user input.

        Args:
            schema (Type[T]): The Pydantic model class defining the expected output structure.
            system_message (str): The system prompt to guide the LLM's behavior.
            input_text (str): The actual input text or query to be processed.

        Returns:
            T: An instance of the provided Pydantic model class populated with the LLM's response.

        Raises:
            TypeError: If the returned object is not an instance of the provided schema.
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
        response = chain.invoke({"input": input_text})

        if isinstance(response, schema):
            return response
        else:
            raise TypeError(f"Unexpected return type: {type(response)}")

    def invoke_with_messages_list(
        self, schema: Type[T], messages: List[AnyMessage]
    ) -> T:
        """
        Invoke the LLM with a structured output schema over a list of messages.
        Args:
            schema (Type[T]): The Pydantic model class defining the expected output structure.
            messages (List[AnyMessage]): The list of messages.

        Returns:
            T: An instance of the provided Pydantic model class populated with the LLM's response.

        Raises:
            TypeError: If the returned object is not an instance of the provided schema.
        """
        structured_llm = self._raw_llm.with_structured_output(
            schema, method="json_schema"
        )

        response = structured_llm.invoke(messages)
        if isinstance(response, schema):
            return response
        else:
            raise TypeError(f"Unexpected return type: {type(response)}")

    @property
    def raw_llm(self) -> BaseChatModel:
        """Access the underlying unstructured LangChain BaseChatModel.

        Returns:
            BaseChatModel: The raw model instance being used.
        """
        return self._raw_llm

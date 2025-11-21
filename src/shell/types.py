from pydantic import BaseModel
from typing import Optional


class InteractionReviewLLMResponse(BaseModel):
    """
    Structured response from the LLM analyzing shell output for interaction needs.

    Attributes:
        needs_action (bool): True if the shell is awaiting user input, False otherwise.
        reason (str): Explanation of why the shell requires or does not require interaction.
    """

    needs_action: bool
    reason: str


class InteractionReview(InteractionReviewLLMResponse):
    """
    Extends InteractionReviewLLMResponse to include the raw shell output.

    Attributes:
        output (str): The shell output that was analyzed by the LLM.
    """

    output: str


class StreamToShellOutput(BaseModel):
    """
    Standardized structure for output returned from executing a shell command.

    Attributes:
        needs_action (bool): True if the shell requires user input; False if command completed.
        reason (Optional[str]): Explanation provided by the LLM if needs_action is True.
        output (str): The final cleaned shell output from the command execution.
    """

    needs_action: bool
    reason: Optional[str] = None
    output: str

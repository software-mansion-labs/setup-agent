from pydantic import BaseModel, Field
from enum import Enum
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

class ProcessState(str, Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    ERROR = "error"

class LongRunningShellInteractionReviewLLMResponse(BaseModel):
    """
    Structured response from the LLM analyzing long-running shell output for interaction needs.

    Attributes:
        needs_action (bool): True if the shell is awaiting user input, False otherwise.
        reason (str): Explanation of why the shell requires or does not require interaction.

    """
    state: ProcessState = ProcessState.INITIALIZING
    reason: str

class InteractionReview(InteractionReviewLLMResponse):
    """
    Extends InteractionReviewLLMResponse to include the raw shell output.

    Attributes:
        output (str): The shell output that was analyzed by the LLM.
    """
    output: str

class SecurityCheckLLMResponse(BaseModel):
    is_safe: bool = Field( 
        description="True if command is a safe write OR accesses only whitelisted files. False otherwise."
    )
    reason: str = Field(
        description="Reasoning for the decision."
    )

class FileExtractionResponse(BaseModel):
    file_path: Optional[str] = Field(
        description="The specific sensitive file path extracted from the command, or None if unclear."
    )
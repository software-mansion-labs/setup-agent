from pydantic import BaseModel, Field
from enum import Enum


class InteractionReviewLLMResponse(BaseModel):
    """Structured response from the LLM analyzing shell output for interaction needs."""

    needs_action: bool = Field(
        description="True if the terminal is currently blocked and waiting for human input (e.g., [Y/n], password, or menu selection). False if it is still processing or finished."
    )
    reason: str = Field(
        description="A clear justification for the interaction status, identifying specific strings like 'Enter password:' or '[y/n]' found in the buffer."
    )


class ProcessState(str, Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    ERROR = "error"


class LongRunningShellInteractionReviewLLMResponse(BaseModel):
    """Structured response from the LLM analyzing long-running shell output for interaction needs."""

    state: ProcessState = Field(
        default=ProcessState.INITIALIZING,
        description="The current lifecycle phase of the background process.",
    )
    reason: str = Field(description="The evidence for the state classification.")


class InteractionReview(InteractionReviewLLMResponse):
    """
    Extends InteractionReviewLLMResponse to include the raw shell output.
    """

    output: str = Field(
        description="The full, redacted text buffer from the shell that was used for this specific analysis session."
    )

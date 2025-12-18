from pydantic import BaseModel
from typing import Optional


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

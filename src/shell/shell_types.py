from pydantic import BaseModel, Field
from typing import Optional


class StreamToShellOutput(BaseModel):
    """
    Standardized structure for output returned from executing a shell command.
    """

    needs_action: bool = Field(
        description="Indicates if the command is currently blocked and waiting for user intervention (e.g., a prompt for a password, a confirmation Y/N, or an interactive menu)."
    )
    reason: Optional[str] = Field(
        default=None,
        description="A short explanation of what the shell is waiting for if needs_action is True.",
    )
    output: str = Field(
        description="The full, cleaned text output captured from the shell from the command execution."
    )

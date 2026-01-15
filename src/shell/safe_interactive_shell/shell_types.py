from pydantic import BaseModel, Field


class CommandReview(BaseModel):
    """
    Represents the safety review of a shell command.
    """

    description: str = Field(
        description="A brief explanation of what the command does and how it affects the system."
    )
    safe: bool = Field(
        description="Indicates whether the command is considered safe to run"
    )
    reason: str = Field(description="Explanation of why the command is safe or unsafe")

from pydantic import BaseModel


class CommandReview(BaseModel):
    """
    Represents the safety review of a shell command.

    Attributes:
        description (str): A brief explanation of what the command does.
        safe (bool): Indicates whether the command is considered safe to run.
        reason (str): Explanation of why the command is safe or unsafe.
    """

    description: str
    safe: bool
    reason: str
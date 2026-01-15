from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SecurityVerdictAction(str, Enum):
    PROCEED = "PROCEED"
    COMPLETED_MANUALLY = "COMPLETED_MANUALLY"
    SKIPPED = "SKIPPED"


class SecurityVerdict(BaseModel):
    """
    Structured result of a command security review.
    """

    action: SecurityVerdictAction = Field(
        description=(
            "The final decision on how to handle the command. "
            "PROCEED: run automatically; "
            "COMPLETED_MANUALLY: user ran it and provided output; "
            "SKIPPED: command was blocked or rejected."
        )
    )
    reason: str = Field(
        description="The justification for the action, such as the specific forbidden pattern triggered or the user's choice in the interactive menu."
    )
    output: Optional[str] = Field(
        default=None,
        description="The shell output captured during manual execution. This should be populated only if the action is COMPLETED_MANUALLY.",
    )

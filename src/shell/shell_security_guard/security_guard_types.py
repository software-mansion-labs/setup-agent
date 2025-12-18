from pydantic import BaseModel
from typing import Optional
from enum import Enum


class SecurityVerdictAction(str, Enum):
    PROCEED = "PROCEED"
    COMPLETED_MANUALLY = "COMPLETED_MANUALLY"
    SKIPPED = "SKIPPED"


class SecurityVerdict(BaseModel):
    action: SecurityVerdictAction
    reason: str
    output: Optional[str] = None

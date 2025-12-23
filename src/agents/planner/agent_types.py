from pydantic import BaseModel, Field
from typing import List
from graph_state import Step


class ReadmeAnalysis(BaseModel):
    plan: List[Step] = Field(
        description=(
            "An ordered list of logical steps required to achieve the user's goal. "
            "Each step must include description, detailed substeps, assigned agents, and "
            "concurrency requirements (separate shell)."
        )
    )

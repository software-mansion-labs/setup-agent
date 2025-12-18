from pydantic import BaseModel, Field


class StepExplanation(BaseModel):
    purpose: str = Field(
        description="An explanation of why this step is necessary for the overall workflow."
    )
    actions: str = Field(
        description="A summary of what the commands will actually do to the system."
    )
    safe: str = Field(
        description="An assessment of the risks involved, clarifying if the step is reversible, safe for the system or if it impacts system-wide configurations."
    )

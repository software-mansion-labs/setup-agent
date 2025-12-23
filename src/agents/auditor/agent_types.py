from pydantic import BaseModel, Field


class AuditorVerdict(BaseModel):
    """Structured response format for the Auditor agent."""

    success: bool = Field(
        description="A boolean flag indicating if the step achieved its intended outcome without critical errors."
    )
    reason: str = Field(
        description="Explanation of the failure or discrepancy found in the step execution. Should be empty if success is true."
    )
    guidance: str = Field(
        description="Actionable instructions or corrections for the Planner agent to resolve the failure. Should be empty if success is true."
    )

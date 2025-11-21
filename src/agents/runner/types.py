from pydantic import BaseModel

class StepExplanation(BaseModel):
    purpose: str
    actions: str
    safe: str
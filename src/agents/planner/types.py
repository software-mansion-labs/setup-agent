from pydantic import BaseModel
from typing import List
from graph_state import Step

class ReadmeAnalysis(BaseModel):
    plan: List[Step]
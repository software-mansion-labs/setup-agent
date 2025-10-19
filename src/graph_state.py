from langgraph.graph import MessagesState
from typing import Optional, List
from pydantic import BaseModel


class GuidelineFile(BaseModel):
    file: str
    content: str


class GraphState(MessagesState):
    next_agent: Optional[str]
    guideline_files: List[GuidelineFile]

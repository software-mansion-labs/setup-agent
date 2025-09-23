from typing import Optional, List
from langgraph.graph import MessagesState


class GraphState(MessagesState):
    guidelines_text: Optional[str]
    requirements: Optional[List[str]]

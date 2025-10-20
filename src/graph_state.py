from langgraph.graph import MessagesState
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from nodes import Node
from typing import Deque

class Substep(BaseModel):
    description: str
    suggested_commands: List[str] = []

class Step(BaseModel):
    description: str
    substeps: List[Substep]
    assigned_agent: Optional[Node] = None
    run_in_separate_shell: bool = False
    shell_id: Optional[UUID] = None

class FinishedStep(BaseModel):
    step: Step
    output: Optional[str] = None
    skipped: bool = False

class FailedStep(BaseModel):
    step: Step
    reason: str
    guidance: str

class GuidelineFile(BaseModel):
    file: str
    content: str


class GraphState(MessagesState):
    plan: Deque[Step]
    finished_steps: List[FinishedStep]
    failed_steps: List[FinishedStep]
    errors: Optional[List[dict]]
    next_node: Optional[Node]
    guideline_files: List[GuidelineFile]
    possible_tasks: List[str]
    chosen_task: str

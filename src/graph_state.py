from langgraph.graph import MessagesState
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from typing import Deque
from enum import Enum
from langgraph.graph import START, END


class Node(str, Enum):
    PLANNER_AGENT = "PLANNER_AGENT"
    INSTALLER_AGENT = "INSTALLER_AGENT"
    RUNNER_AGENT = "RUNNER_AGENT"
    AUDITOR_AGENT = "AUDITOR_AGENT"
    SUCCESS_VERIFIER_AGENT = "SUCCESS_VERIFIER_AGENT"
    GUIDELINES_RETRIEVER_NODE = "GUIDELINES_RETRIEVER_NODE"
    TASK_IDENTIFIER_NODE = "TASK_IDENTIFIER_NODE"
    CONTINUE_PROCESS_NODE = "CONTINUE_PROCESS_NODE"
    START = START
    END = END

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


class WorkflowError(BaseModel):
    description: str
    error: str


class GraphState(MessagesState):
    plan: Optional[Deque[Step]]
    finished_steps: List[FinishedStep]
    failed_steps: List[FailedStep]
    errors: List[WorkflowError]
    next_node: Optional[Node]
    guideline_files: List[GuidelineFile]
    possible_tasks: List[str]
    chosen_task: str

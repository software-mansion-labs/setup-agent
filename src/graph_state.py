from enum import Enum
from typing import Deque, List, Optional
from uuid import UUID

from langgraph.graph import END, START, MessagesState
from pydantic import BaseModel, Field


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
    description: str = Field(
        description="A description of the action to be performed within a step."
    )
    suggested_commands: List[str] = Field(
        default=[],
        description="The specific shell commands required to complete this substep.",
    )


class Step(BaseModel):
    description: str = Field(
        description="A description of the step in the installation or execution process."
    )
    substeps: List[Substep] = Field(
        description="A list substeps required to complete this step."
    )
    assigned_agent: Optional[Node] = Field(
        default=None, description="The specific agent responsible for this step."
    )
    run_in_separate_shell: bool = Field(
        default=False,
        description="Flag indicating if this step starts a long-running process (like a server) that needs its own persistent terminal.",
    )
    shell_id: Optional[UUID] = Field(
        default=None,
        description="The unique identifier for the shell session assigned to this step.",
    )


class FinishedStep(BaseModel):
    step: Step = Field(description="The original step definition that was executed.")
    output: Optional[str] = Field(
        default=None,
        description="The full terminal output captured during the execution of this step.",
    )
    skipped: bool = Field(
        default=False,
        description="Indicates if the user chose to bypass this step manually.",
    )


class FailedStep(BaseModel):
    step: Step = Field(
        description="The original step definition that failed to complete successfully."
    )
    reason: str = Field(description="A description of the error or discrepancy.")
    guidance: str = Field(description="Suggested corrective actions to fix the issue.")


class GuidelineFile(BaseModel):
    file: str = Field(description="The relative path to the documentation file.")
    content: str = Field(description="The full raw text content of the file.")


class WorkflowError(BaseModel):
    description: str = Field(
        description="A summary of where the workflow logic broke down."
    )
    error: str = Field(description="Error message associated with the failure.")


class GraphState(MessagesState):
    plan: Optional[Deque[Step]]
    finished_steps: List[FinishedStep]
    failed_steps: List[FailedStep]
    errors: List[WorkflowError]
    next_node: Optional[Node]
    possible_guideline_files: List[GuidelineFile]
    selected_guideline_files: List[GuidelineFile]
    possible_tasks: List[str]
    chosen_task: str
    finished_tasks: List[str]

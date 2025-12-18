from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from langgraph.graph import END
from langchain.agents import AgentState
from enum import Enum
from graph_state import WorkflowError


class ShutdownDecision(BaseModel):
    """Intelligent shutdown decision with reasoning"""

    decision: Literal["end", "continue"] = Field(
        description="'end' if conversation should end, 'continue' otherwise"
    )
    reason: str = Field(description="Brief explanation for the decision")


class VerificationOutcome(str, Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"


class VerifierState(AgentState):
    outcome: Optional[VerificationOutcome]
    should_continue: bool
    errors: List[WorkflowError]
    question_count: int
    current_error_description: str
    user_stopped_questioning: bool


class VerifierAgentNode(str, Enum):
    CHECK_OUTCOME = "check_outcome"
    COLLECT_ERROR = "collect_error"
    ASK_CLARIFICATION = "ask_clarification"
    SHOULD_CONTINUE = "should_continue"
    END = END

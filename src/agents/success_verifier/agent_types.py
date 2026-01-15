from enum import Enum
from typing import List, Literal, Optional

from langchain.agents import AgentState
from langgraph.graph import END
from pydantic import BaseModel, Field

from agents.success_verifier.constants import VerificationOutcome
from graph_state import WorkflowError


class ShutdownDecision(BaseModel):
    """Intelligent shutdown decision with reasoning"""

    decision: Literal["end", "continue"] = Field(
        description="'end' if conversation should end, 'continue' otherwise"
    )
    reason: str = Field(description="Brief explanation for the decision")


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

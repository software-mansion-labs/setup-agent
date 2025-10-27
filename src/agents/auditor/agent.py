from typing import List

from graph_state import GraphState, FinishedStep, FailedStep, Node
from langchain_core.messages import HumanMessage
from tools.run_command_tool import run_command_tool
from tools import get_websearch_tool
from agents.base_structured_agent import BaseStructuredAgent
from pydantic import BaseModel
from agents.auditor.prompts import AuditorPrompts


class AuditorVerdict(BaseModel):
    """Structured response format for the Auditor agent."""
    success: bool
    reason: str
    guidance: str


class Auditor(BaseStructuredAgent):
    """Agent responsible for verifying the success of the last executed step.

    The Auditor examines the output of the last finished step and determines
    whether it succeeded or failed. It can use system tools or web search
    to validate results and provide actionable guidance.

    Attributes:
        tools: List of tools available to the auditor (run_command, websearch).
        response_format: Pydantic model defining the structured response.
    """

    def __init__(self):
        """Initialize the Auditor agent with appropriate tools and prompt."""
        websearch_tool = get_websearch_tool()
        tools = [websearch_tool, run_command_tool]
        super().__init__(
            name=Node.AUDITOR_AGENT.value,
            prompt=AuditorPrompts.AUDITOR_DESCRIPTION,
            tools=tools,
            response_format=AuditorVerdict,
        )

    def invoke(self, state: GraphState) -> GraphState:
        """Verify the success of the last finished step in the workflow.

        Args:
            state (GraphState): Current workflow state containing finished and failed steps.

        Returns:
            GraphState: Updated workflow state with potential failed steps and next node.
        """
        finished_steps: List[FinishedStep] = state.get("finished_steps", [])
        failed_steps: List[FailedStep] = state.get("failed_steps", [])

        if not finished_steps:
            self.logger.warning("[Auditor] No finished steps to verify.")
            state["next_node"] = Node.PLANNER_AGENT
            return state

        last_finished_step = finished_steps[-1]
        self.logger.info(
            f"[Auditor] Verifying last step: {last_finished_step.step.description}"
        )

        if last_finished_step.skipped:
            self.logger.info("[Auditor] Last step was skipped, moving to planner.")
            state["next_node"] = Node.PLANNER_AGENT
            return state

        return self._verify_last_step(
            last_finished_step, finished_steps[:-1], failed_steps, state
        )

    def _verify_last_step(
        self,
        last_step: FinishedStep,
        previous_steps: List[FinishedStep],
        failed_steps: List[FailedStep],
        state: GraphState,
    ) -> GraphState:
        """Internal helper to verify the last finished step using LLM and tools.

        Args:
            last_step (FinishedStep): Step to verify.
            previous_steps (List[FinishedStep]): Steps executed before this one.
            failed_steps (List[FailedStep]): Existing list of failed steps.
            state (GraphState): Current workflow state.

        Returns:
            GraphState: Updated workflow state with potential failed step added.
        """
        previous_text = (
            ", ".join([step.step.description for step in previous_steps])
            if previous_steps
            else "none"
        )
        step_output = last_step.output[-64_000:] if last_step.output is not None else "No output recorded."

        prompt = self._build_verification_prompt(
            last_step.step.description, previous_text, step_output
        )

        try:
            response: AuditorVerdict = self.agent.invoke(
                {"messages": [HumanMessage(content=prompt)]}
            )["structured_response"]

            if not response.success:
                self.logger.error(
                    f"[Auditor] Step failed: {last_step.step.description}. Reason: {response.reason}, Guidance: {response.guidance}"
                )
                failed_steps.append(
                    FailedStep(
                        step=last_step.step,
                        reason=response.reason,
                        guidance=response.guidance,
                    )
                )

        except Exception as e:
            self.logger.error(f"[Auditor] Exception during verification: {e}")
            failed_steps.append(
                FailedStep(
                    step=last_step.step, reason="Auditor exception", guidance=str(e)
                )
            )

        state["failed_steps"] = failed_steps
        state["next_node"] = Node.PLANNER_AGENT
        return state

    def _build_verification_prompt(
        self, step_description: str, previous_steps_text: str, step_output: str
    ) -> str:
        """Construct the prompt to send to the LLM for verification.

        Args:
            step_description (str): Description of the last step.
            previous_steps_text (str): Descriptions of previously executed steps.
            step_output (str): Output from the last step.

        Returns:
            str: Formatted prompt for the LLM.
        """

        return AuditorPrompts.VERIFICATION.value.format(
            step_description=step_description,
            previous_steps_text=previous_steps_text,
            step_output=step_output,
        )

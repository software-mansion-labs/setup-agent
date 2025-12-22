from agents.base_custom_agent import BaseCustomAgent
from graph_state import GraphState, WorkflowError, Node
from langchain_core.messages import HumanMessage, SystemMessage
from questionary import text, select, Choice
from langgraph.graph.state import StateGraph, CompiledStateGraph
from agents.success_verifier.types import (
    ShutdownDecision,
    VerifierAgentNode,
    VerifierState,
)
from agents.success_verifier.prompts import SuccessVerifierPrompts
from agents.success_verifier.constants import (
    ErrorCategory,
    VerificationOutcome,
    ClarificationChoice,
    VerifierUserPrompts,
)


class SuccessVerifier(BaseCustomAgent[VerifierState, GraphState]):
    """Agent responsible for verifying the success of an executed workflow.

    This agent interacts with the user to confirm if the task was completed
    successfully. If errors occur, it engages in a troubleshooting loop to
    gather details and clarification before returning control to the planner.
    """

    def __init__(self, max_questions: int = 5) -> None:
        """Initializes the SuccessVerifier agent.

        Args:
            max_questions: The maximum number of clarifying questions the agent
                is allowed to ask the user regarding an error. Defaults to 5.
        """
        super().__init__(
            name=Node.SUCCESS_VERIFIER_AGENT.value,
        )
        self.subgraph = self._build_agent_workflow()
        self.max_questions = max_questions

    def _build_agent_workflow(
        self,
    ) -> CompiledStateGraph[VerifierState, None, VerifierState, VerifierState]:
        """Constructs and compiles the internal state graph for the verification process.

        Defines the nodes (outcome check, error collection, clarification loop)
        and the conditional edges that dictate the flow based on user input.

        Returns:
            CompiledStateGraph: The compiled LangGraph workflow ready for invocation.
        """
        workflow = StateGraph(VerifierState)

        workflow.add_node(
            VerifierAgentNode.CHECK_OUTCOME.value, self._check_outcome_node
        )
        workflow.add_node(
            VerifierAgentNode.COLLECT_ERROR.value, self._collect_error_node
        )
        workflow.add_node(
            VerifierAgentNode.ASK_CLARIFICATION.value, self._ask_clarification_node
        )
        workflow.add_node(
            VerifierAgentNode.SHOULD_CONTINUE.value, self._check_continuation_node
        )
        workflow.set_entry_point(VerifierAgentNode.CHECK_OUTCOME.value)

        workflow.add_conditional_edges(
            VerifierAgentNode.CHECK_OUTCOME.value,
            self._route_after_outcome,
            {
                VerifierAgentNode.END.value: VerifierAgentNode.END.value,
                VerifierAgentNode.COLLECT_ERROR.value: VerifierAgentNode.COLLECT_ERROR.value,
            },
        )

        workflow.add_edge(
            VerifierAgentNode.COLLECT_ERROR.value,
            VerifierAgentNode.ASK_CLARIFICATION.value,
        )

        workflow.add_conditional_edges(
            VerifierAgentNode.ASK_CLARIFICATION.value,
            self._route_after_clarification,
            {
                VerifierAgentNode.ASK_CLARIFICATION.value: VerifierAgentNode.ASK_CLARIFICATION.value,
                VerifierAgentNode.SHOULD_CONTINUE.value: VerifierAgentNode.SHOULD_CONTINUE.value,
            },
        )

        workflow.add_conditional_edges(
            VerifierAgentNode.SHOULD_CONTINUE.value,
            self._route_final,
            {
                VerifierAgentNode.END.value: VerifierAgentNode.END.value,
                VerifierAgentNode.COLLECT_ERROR.value: VerifierAgentNode.COLLECT_ERROR.value,
            },
        )

        return workflow.compile()

    def _check_outcome_node(self, state: VerifierState) -> VerifierState:
        """Prompts the user to confirm the success of the installation/execution.

        Displays a selection menu to the user to categorize the outcome as
        Success, Partial Success, or Failure.

        Args:
            state: The current verifier state.

        Returns:
            VerifierState: The updated verifier state.
        """
        self.logger.info("Checking installation outcome...")

        outcome = select(
            message=VerifierUserPrompts.CHECK_OUTCOME.value,
            choices=[
                Choice(
                    title=VerificationOutcome.SUCCESS.value,
                    value=VerificationOutcome.SUCCESS,
                ),
                Choice(
                    title=VerificationOutcome.PARTIAL_SUCCESS.value,
                    value=VerificationOutcome.PARTIAL_SUCCESS,
                ),
                Choice(
                    title=VerificationOutcome.FAILURE.value,
                    value=VerificationOutcome.FAILURE,
                ),
            ],
            default=VerificationOutcome.SUCCESS,
        ).unsafe_ask()

        state["outcome"] = outcome
        return state

    def _collect_error_node(self, state: VerifierState) -> VerifierState:
        """Collects initial error details from the user via interactive prompts.

        Asks the user to categorize the error and provide a specific description or error log.

        Args:
            state: The current verifier state.

        Returns:
            VerifierState: The updated verifier state.
        """
        self.logger.info("Collecting error details...")

        outcome = state.get("outcome") or VerificationOutcome.FAILURE

        error_category = select(
            message=VerifierUserPrompts.ERROR_NATURE.value,
            choices=[
                ErrorCategory.TERMINAL.value,
                ErrorCategory.MISSING_FILE.value,
                ErrorCategory.HANG.value,
                ErrorCategory.LOGIC.value,
                ErrorCategory.OTHER.value,
            ],
        ).unsafe_ask()

        problem_description = text(
            message=VerifierUserPrompts.ERROR_DETAILS.value,
        ).unsafe_ask()

        if not problem_description:
            problem_description = "User provided no details."

        full_description = f"[{outcome.upper()}] Category: {error_category}. Details: {problem_description}"
        state["current_error_description"] = full_description

        return state

    def _ask_clarification_node(self, state: VerifierState) -> VerifierState:
        """Generates a clarifying question using LLM and captures user input.

        Uses the current error description to prompt the LLM for a relevant
        troubleshooting question. Allows the user to answer, skip, or stop
        the questioning process.

        Args:
            state: The current verifier state.

        Returns:
            VerifierState: The updated verifier state.
        """
        question_count = state.get("question_count", 0)

        full_description = state.get(
            "current_error_description", "Unknown error reported by user."
        )

        system_prompt = SuccessVerifierPrompts.COLLECT_USER_ERRORS.value.format(
            problem_description=full_description
        )

        try:
            messages = [HumanMessage(content=system_prompt)] + state["messages"]
            result = self._llm.raw_llm.invoke(messages)
            agent_question = result.content

            if not agent_question:
                self.logger.info("No more questions generated.")
                state["should_continue"] = False
                state["question_count"] = question_count + 1
                return state

            print(
                f"\n[{self.name}] Clarifying question ({question_count + 1}/{self.max_questions}):"
            )
            print(f'   "{agent_question}"\n')

            user_choice = select(
                message=VerifierUserPrompts.PROCEED_ACTION.value,
                choices=[
                    ClarificationChoice.ANSWER.value,
                    ClarificationChoice.SKIP.value,
                    ClarificationChoice.STOP.value,
                ],
            ).unsafe_ask()

            state["question_count"] = question_count + 1

            if user_choice == ClarificationChoice.STOP.value:
                state["should_continue"] = False
                state["user_stopped_questioning"] = True
                return state

            if user_choice == ClarificationChoice.SKIP.value:
                return state

            user_reply = text(
                message=VerifierUserPrompts.USER_ANSWER.value
            ).unsafe_ask()

            if user_reply:
                messages_list = state.get("messages", [])
                messages_list.append(
                    HumanMessage(content=f"Q: {agent_question}\nA: {user_reply}")
                )
                state["messages"] = messages_list

                current_desc = state.get("current_error_description", "")
                state["current_error_description"] = (
                    f"{current_desc}\n\nClarification Q&A:\nQ: {agent_question}\nA: {user_reply}"
                )

        except Exception as e:
            self.logger.error(f"Error during clarification: {e}")
            state["should_continue"] = False
            state["question_count"] = question_count + 1

        return state

    def _check_continuation_node(self, state: VerifierState) -> VerifierState:
        """Determines if the troubleshooting conversation should continue.

        Uses an LLM call to decide if enough information has been gathered
        or if the user has explicitly requested to stop.

        Args:
            state: The current state containing recent messages.

        Returns:
            VerifierState: The updated verifier state.
        """
        if state["user_stopped_questioning"]:
            self.logger.info(
                "User explicitly stopped questioning - ending verification"
            )
            state["should_continue"] = False
            return state

        if len(state.get("messages", [])) < 2:
            state["should_continue"] = True
            return state

        recent_messages = state["messages"][-6:]

        try:
            decision: ShutdownDecision = self._llm.invoke_with_messages_list(
                ShutdownDecision,
                recent_messages
                + [
                    HumanMessage(
                        content=SuccessVerifierPrompts.SHOULD_END_CONVERSATION.value
                    )
                ],
            )

            self.logger.info(
                f"Shutdown decision: {decision.decision} -- {decision.reason}"
            )
            state["should_continue"] = decision.decision == "continue"
        except Exception as e:
            self.logger.error(f"Error in continuation check: {e}")
            state["should_continue"] = False

        return state

    def _route_after_outcome(self, state: VerifierState) -> str:
        """Determines the next node based on the user's reported outcome.

        Args:
            state: The current verifier state.

        Returns:
            str: The name of the next node.
        """
        if state["outcome"] == VerificationOutcome.SUCCESS:
            return VerifierAgentNode.END.value
        return VerifierAgentNode.COLLECT_ERROR.value

    def _route_after_clarification(self, state: VerifierState) -> str:
        """Routes execution after a clarification question is processed.

        Args:
            state: The current verifier state.

        Returns:
            str: The name of the next node.
        """
        if not state.get("should_continue", True):
            return VerifierAgentNode.SHOULD_CONTINUE.value

        if state.get("question_count", 0) >= self.max_questions:
            self.logger.info(f"Reached max questions ({self.max_questions})")
            return VerifierAgentNode.SHOULD_CONTINUE.value

        return VerifierAgentNode.ASK_CLARIFICATION.value

    def _route_final(self, state: VerifierState) -> str:
        """Final routing logic after the continuation check.

        Args:
            state: The current verifier state.

        Returns:
            str: The name of the next node.
        """
        if not state["should_continue"] or state["user_stopped_questioning"]:
            return VerifierAgentNode.END.value
        return VerifierAgentNode.COLLECT_ERROR.value

    def _create_execution_context(self, state: GraphState) -> str:
        """Creates a text summary of the executed workflow for the LLM context.

        Compiles the chosen task and a list of successfully completed steps
        and substeps into a formatted string.

        Args:
            state: The main GraphState containing execution history.

        Returns:
            str: A formatted context string describing the current environment state.
        """
        task = state["chosen_task"]

        context_lines = ["### WORKFLOW CONTEXT", f"**Target Task:** {task}", ""]

        finished_steps = state.get("finished_steps", [])
        if finished_steps:
            context_lines.append("**SUCCESSFULLY COMPLETED STEPS:**")
            for i, fs in enumerate(finished_steps, 1):
                step_desc = fs.step.description
                status = "Skipped" if fs.skipped else "Executed"
                context_lines.append(f"{i}. [{status}] {step_desc}")

                if fs.step.substeps:
                    for sub in fs.step.substeps:
                        context_lines.append(f"    - Substep: {sub.description}")
                        if sub.suggested_commands:
                            cmds_str = ", ".join(
                                [f"`{cmd}`" for cmd in sub.suggested_commands]
                            )
                            context_lines.append(f"      Commands: {cmds_str}")
        else:
            context_lines.append("No steps have been completed yet.")

        context_lines.append(
            "\nUse this context to understand the current state of the environment and interact with user to verify if everything works as expected."
        )
        return "\n".join(context_lines)

    def invoke(self, state: GraphState) -> GraphState:
        """Executes the verification workflow.

        This is the main entry point called by the parent graph. It initializes
        the subgraph state, runs the verification workflow, and maps any collected
        errors back to the main application state.

        Args:
            state: The main GraphState of the application.

        Returns:
            GraphState: The updated application state.
        """
        self.logger.info("Starting success verification workflow...")
        context_messages = [
            SystemMessage(content=self._create_execution_context(state))
        ] + state["messages"]

        result_state: VerifierState = self.subgraph.invoke(
            VerifierState(
                messages=context_messages,
                outcome=None,
                should_continue=True,
                errors=[],
                question_count=0,
                current_error_description="",
                user_stopped_questioning=False,
            )
        )  # type: ignore

        error_description = result_state.get("current_error_description", "")
        if error_description:
            state["errors"] = [
                WorkflowError(
                    description="User reported issue after verification process",
                    error=error_description,
                )
            ]
            state["next_node"] = Node.PLANNER_AGENT

        self.logger.info(
            f"Verification finished. Outcome: {result_state.get('outcome')}"
        )
        return state

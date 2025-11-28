from agents.base_custom_agent import BaseCustomAgent
from graph_state import GraphState, WorkflowError, Node
from langchain_core.messages import HumanMessage, SystemMessage
from agents.planner.prompts import PlannerPrompts
from questionary import text, select, Choice
from langgraph.graph import StateGraph
from agents.success_verifier.types import ShutdownDecision, VerifierAgentNode, VerifierState, VerificationOutcome
from agents.success_verifier.prompts import SuccessVerifierPrompts


class SuccessVerifier(BaseCustomAgent):
    def __init__(self):
        super().__init__(
            name=Node.SUCCESS_VERIFIER_AGENT.value,
        )
        self.subgraph = self._build_agent_workflow().compile()
        self.max_questions = 5

    def _build_agent_workflow(self) -> StateGraph:
        workflow = StateGraph(VerifierState)
        
        workflow.add_node(VerifierAgentNode.CHECK_OUTCOME.value, self._check_outcome_node)
        workflow.add_node(VerifierAgentNode.COLLECT_ERROR.value, self._collect_error_node)
        workflow.add_node(VerifierAgentNode.ASK_CLARIFICATION.value, self._ask_clarification_node)
        workflow.add_node(VerifierAgentNode.SHOULD_CONTINUE.value, self._check_continuation_node)
        workflow.set_entry_point(VerifierAgentNode.CHECK_OUTCOME.value)
        
        workflow.add_conditional_edges(
            VerifierAgentNode.CHECK_OUTCOME.value,
            self._route_after_outcome,
            {
                VerifierAgentNode.END.value: VerifierAgentNode.END.value,
                VerifierAgentNode.COLLECT_ERROR.value: VerifierAgentNode.COLLECT_ERROR.value
            }
        )
        
        workflow.add_edge(VerifierAgentNode.COLLECT_ERROR.value, VerifierAgentNode.ASK_CLARIFICATION.value)
        
        workflow.add_conditional_edges(
            VerifierAgentNode.ASK_CLARIFICATION.value,
            self._route_after_clarification,
            {
                VerifierAgentNode.ASK_CLARIFICATION.value: VerifierAgentNode.ASK_CLARIFICATION.value,
                VerifierAgentNode.SHOULD_CONTINUE.value: VerifierAgentNode.SHOULD_CONTINUE.value,
            }
        )
        
        workflow.add_conditional_edges(
            VerifierAgentNode.SHOULD_CONTINUE.value,
            self._route_final,
            {
                VerifierAgentNode.END.value: VerifierAgentNode.END.value,
                VerifierAgentNode.COLLECT_ERROR.value: VerifierAgentNode.COLLECT_ERROR.value
            }
        )
        
        return workflow

    def _check_outcome_node(self, state: VerifierState) -> VerifierState:
        """Node: Check the installation/execution outcome with user"""
        self.logger.info("Checking installation outcome...")
        
        outcome = select(
            message="How did the installation/execution process go?",
            choices=[
                Choice("Success - everything works as expected", value=VerificationOutcome.SUCCESS.value),
                Choice("Partial success - works but with errors", value=VerificationOutcome.PARTIAL_SUCCESS.value),
                Choice("Failure - critical error occurred", value=VerificationOutcome.FAILURE.value),
            ],
            default=VerificationOutcome.SUCCESS.value
        ).unsafe_ask()
        
        state["outcome"] = outcome
        return state

    def _collect_error_node(self, state: VerifierState) -> VerifierState:
        self.logger.info("Collecting error details...")
        
        outcome = state.get("outcome") or VerificationOutcome.FAILURE
        
        error_category = select(
            message="What is the nature of the problem?",
            choices=[
                "Terminal error (Exception/Traceback)",
                "Missing expected file/directory",
                "Application does not start (hang/freeze)",
                "Incorrect output/logic",
                "Other issue"
            ]
        ).unsafe_ask()

        problem_description = text(
            message="Please describe the details or paste the error log:",
        ).unsafe_ask()
        
        if not problem_description:
            problem_description = "User provided no details."

        full_description = f"[{outcome.upper()}] Category: {error_category}. Details: {problem_description}"
        state["current_error_description"] = full_description
        
        return state

    def _ask_clarification_node(self, state: VerifierState) -> VerifierState:
        """Node: Ask clarifying questions about the error"""
        question_count = state.get("question_count", 0)
    
        full_description = state.get("current_error_description", "")
        
        if not full_description:
            full_description = "Unknown error reported by user."

        system_prompt = PlannerPrompts.COLLECT_USER_ERRORS.value.format(
            problem_description=full_description
        )
        
        try:
            messages = [HumanMessage(content=system_prompt)] + state.get("messages", [])
            result = self._llm.raw_llm.invoke(messages)
            agent_question = result.content
 
            if not agent_question:
                self.logger.info("No more questions generated.")
                state["should_continue"] = False
                state["question_count"] = question_count + 1
                return state
            
            print(f"\n[{self.name}] Clarifying question ({question_count + 1}/{self.max_questions}):")
            print(f"   \"{agent_question}\"\n")

            user_choice = select(
                message="How would you like to proceed?",
                choices=[
                    Choice("Answer the question", value="answer"),
                    Choice("Skip this question", value="skip"),
                    Choice("Stop questioning and start fixing", value="stop")
                ]
            ).unsafe_ask()

            state["question_count"] = question_count + 1

            if user_choice == "stop":
                state["should_continue"] = False
                state["user_stopped_questioning"] = True
                return state
            
            if user_choice == "skip":
                return state

            user_reply = text(message="Your answer:").unsafe_ask()
            
            if user_reply:
                messages_list = state.get("messages", [])
                messages_list.append(HumanMessage(content=f"Q: {agent_question}\nA: {user_reply}"))
                state["messages"] = messages_list
                
                current_desc = state.get("current_error_description", "")
                state["current_error_description"] = f"{current_desc}\n\nClarification Q&A:\nQ: {agent_question}\nA: {user_reply}"
            
        except Exception as e:
            self.logger.error(f"Error during clarification: {e}")
            state["should_continue"] = False
            state["question_count"] = question_count + 1
        
        return state

    def _check_continuation_node(self, state: VerifierState) -> VerifierState:
        """Check if we should continue asking questions or end the verification"""
        
        if state.get("user_stopped_questioning", False):
            self.logger.info("User explicitly stopped questioning - ending verification")
            state["should_continue"] = False
            return state
        
        if len(state.get("messages", [])) < 2:
            state["should_continue"] = True
            return state
        
        recent_messages = state["messages"][-6:]
        
        try:
            decision: ShutdownDecision = self._llm.invoke_with_messages_list(
                ShutdownDecision,
                recent_messages + [HumanMessage(content=SuccessVerifierPrompts.SHOULD_END_CONVERSATION.value)],
            )
            
            self.logger.info(f"Shutdown decision: {decision.decision} -- {decision.reason}")
            state["should_continue"] = (decision.decision == "continue")
        except Exception as e:
            self.logger.error(f"Error in continuation check: {e}")
            state["should_continue"] = False
            
        return state

    def _route_after_outcome(self, state: VerifierState) -> str:
        if state["outcome"] == VerificationOutcome.SUCCESS:
            return VerifierAgentNode.END.value
        return VerifierAgentNode.COLLECT_ERROR.value

    def _route_after_clarification(self, state: VerifierState) -> str:
        if not state.get("should_continue", True):
            return VerifierAgentNode.SHOULD_CONTINUE.value
        
        if state.get("question_count", 0) >= self.max_questions:
            self.logger.info(f"Reached max questions ({self.max_questions})")
            return VerifierAgentNode.SHOULD_CONTINUE.value
        
        return VerifierAgentNode.ASK_CLARIFICATION.value

    def _route_final(self, state: VerifierState) -> str:
        if not state.get("should_continue", True) or state.get("user_stopped_questioning", False):
            return VerifierAgentNode.END.value
        return VerifierAgentNode.COLLECT_ERROR.value
        
    def _create_execution_context(self, state: GraphState) -> str:
        """
        Constructs a system prompt summarizing the workflow history 
        based on the provided Pydantic models.
        """
        task = state["chosen_task"]
        
        context_lines = [
            f"### WORKFLOW CONTEXT",
            f"**Target Task:** {task}",
            ""
        ]
        
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
                            cmds_str = ", ".join([f"`{cmd}`" for cmd in sub.suggested_commands])
                            context_lines.append(f"      Commands: {cmds_str}")
        else:
            context_lines.append("No steps have been completed yet.")

        context_lines.append("\nUse this context to understand the current state of the environment and interact with user to verify if everything works as expected.")
        return "\n".join(context_lines)

    def invoke(self, state: GraphState) -> GraphState:
        self.logger.info("Starting success verification workflow...")
        context_messages = [SystemMessage(content=self._create_execution_context(state))] + state["messages"]
        
        result_state: VerifierState = self.subgraph.invoke(
            VerifierState(
                messages=context_messages,
                outcome=None,
                should_continue=True,
                errors=[],
                question_count=0,
                current_error_description="",
                user_stopped_questioning=False
            )
        ) # type: ignore

        error_description = result_state.get("current_error_description", "")
        if error_description:
            state["errors"] = [
                WorkflowError(
                    description="User reported issue after verification process",
                    error=error_description
                )
            ]
            state["next_node"] = Node.PLANNER_AGENT

        self.logger.info(f"Verification finished. Outcome: {result_state.get('outcome')}")
        return state
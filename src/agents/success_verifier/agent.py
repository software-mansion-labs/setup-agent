from agents.base_custom_agent import BaseCustomAgent
from graph_state import GraphState, WorkflowError, Node
from langchain_core.messages import HumanMessage, SystemMessage
from agents.planner.prompts import PlannerPrompts
from questionary import text, select, Choice
from langgraph.graph import StateGraph, END
from agents.success_verifier.types import ShutdownDecision, VerifierAgentNode, VerifierState, VerificationOutcome
from agents.success_verifier.prompts import SuccessVerifierPrompts


class SuccessVerifier(BaseCustomAgent):
    def __init__(self):
        super().__init__(
            name=Node.SUCCESS_VERIFIER.value,
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
                "continue": VerifierAgentNode.ASK_CLARIFICATION.value,
                VerifierAgentNode.SHOULD_CONTINUE.value: VerifierAgentNode.SHOULD_CONTINUE.value,
                VerifierAgentNode.END.value: VerifierAgentNode.END.value
            }
        )
        
        workflow.add_conditional_edges(
            VerifierAgentNode.SHOULD_CONTINUE.value,
            self._route_final,
            {
                "end": VerifierAgentNode.END.value,
                "continue": VerifierAgentNode.COLLECT_ERROR.value
            }
        )
        
        return workflow

    def _check_outcome_node(self, state: VerifierState) -> VerifierState:
        self.logger.info("Checking installation outcome...")
        
        outcome = select(
            message="How did the installation/execution process go?",
            choices=[
                Choice("Success - everything works as expected", value=VerificationOutcome.SUCCESS.value),
                Choice("Partial success - works but with errors", value=VerificationOutcome.PARTIAL_SUCCESS.value),
                Choice("Failure - critical error occurred", value=VerificationOutcome.FAILURE.value),
            ],
            default=VerificationOutcome.SUCCESS.value
        ).ask()
        
        state["outcome"] = outcome
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
                return state
            
            print(f"\n[{self.name}]Clarifying question ({question_count + 1}/{self.max_questions}):")
            print(f"   \"{agent_question}\"\n")

            user_choice = select(
                message="How would you like to proceed?",
                choices=[
                    Choice("Answer the question", value="answer"),
                    Choice("Skip this question", value="skip"),
                    Choice("Stop questioning and start fixing", value="stop")
                ]
            ).ask()

            if user_choice == "stop":
                state["should_continue"] = False
                return state
            
            if user_choice == "skip":
                return state

            user_reply = text(message="Your answer:").ask()
            
            if user_reply:
                errors = state.get("errors", [])
                errors.append(
                    WorkflowError(
                        description=f"Clarification: {agent_question}", 
                        error=user_reply
                    )
                )
                state["errors"] = errors
            
        except Exception as e:
            self.logger.error(f"Error during clarification: {e}")
            state["should_continue"] = False
        
        return state

    def _collect_error_node(self, state: VerifierState) -> VerifierState:
        """Node: Collect error details from user"""
        self.logger.info("Collecting error details...")
        
        errors = state.get("errors", [])
        outcome = state["outcome"] or VerificationOutcome.FAILURE
        
        error_category = select(
            message="What is the nature of the problem?",
            choices=[
                "Terminal error (Exception/Traceback)",
                "Missing expected file/directory",
                "Application does not start (hang/freeze)",
                "Incorrect output/logic",
                "Other issue"
            ]
        ).ask()

        problem_description = text(
            message="Please describe the details or paste the error log:",
        ).ask()
        
        if not problem_description:
            problem_description = "User provided no details."

        full_description = f"[{outcome.value.upper()}] Category: {error_category}. Details: {problem_description}"        
        errors.append(WorkflowError(description="User reported issue after whole process finished", error=full_description))
        state["errors"] = errors
        
        return state

    def _check_continuation_node(self, state: VerifierState) -> VerifierState:
        """Node: Check if conversation should end using LLM"""
        if len(state.get("messages", [])) < 2:
            return state
        
        recent_messages = state["messages"][-6:]
        
        decision: ShutdownDecision = self._llm.invoke_with_messages_list(
            ShutdownDecision,
            recent_messages + [HumanMessage(content=SuccessVerifierPrompts.SHOULD_END_CONVERSATION.value)],
        )
        
        self.logger.info(f"Shutdown decision: {decision.decision} -- {decision.reason}")
        state["should_continue"] = (decision.decision == "continue")
            
        return state

    def _route_after_outcome(self, state: VerifierState) -> VerifierAgentNode:
        """Route based on outcome check"""
        if state["outcome"] == VerificationOutcome.SUCCESS:
            return VerifierAgentNode.END
        return VerifierAgentNode.COLLECT_ERROR

    def _route_after_clarification(self, state: VerifierState) -> VerifierAgentNode:
        """Route after asking clarification"""
        should_continue = state["should_continue"]
        if not should_continue:
            return VerifierAgentNode.SHOULD_CONTINUE
        
        user_choice = state.get("user_choice", "")
        if user_choice == "stop":
            return VerifierAgentNode.SHOULD_CONTINUE
        
        if self._should_end_conversation(state):
            self.logger.info("Intelligent shutdown detected.")
            return VerifierAgentNode.END
        
        if state.get("question_count", 0) < self.max_questions:
            return VerifierAgentNode.ASK_CLARIFICATION
        
        return VerifierAgentNode.SHOULD_CONTINUE

    def _route_final(self, state: VerifierState) -> str:
        if state.get("should_continue", True):
            return "continue"
        return "end"

    def _should_end_conversation(self, state: VerifierState) -> bool:
        if len(state.get("messages", [])) < 2:
            return False
        
        try:
            recent_messages = state["messages"][-6:]
            messages = [HumanMessage(content=SuccessVerifierPrompts.SHOULD_END_CONVERSATION.value)] + recent_messages
            result = self._llm.invoke_with_messages_list(ShutdownDecision, messages)
            return result.decision == "end"
        except Exception as e:
            self.logger.error(f"Error in quick shutdown check: {e}")
            return False
        
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
                errors=[]
            )
        ) # type: ignore

        errors = result_state.get("errors", [])
        if errors:
            state["errors"] = errors
            state["next_node"] = Node.PLANNER_AGENT

        self.logger.info(f"Verification finished. Outcome: {result_state.get('outcome')}")
        return state
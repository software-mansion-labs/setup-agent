from agents.base_custom_agent import BaseCustomAgent
from graph_state import GraphState, WorkflowError, Node
from langchain_core.messages import HumanMessage
from agents.planner.prompts import PlannerPrompts
from questionary import text, select, Choice
from langgraph.graph import StateGraph, END
from agents.success_verifier.types import ShutdownDecision, VerifierAgentNodes, VerifierState
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
        
        workflow.add_node(VerifierAgentNodes.CHECK_OUTCOME.value, self._check_outcome_node)
        workflow.add_node(VerifierAgentNodes.COLLECT_ERROR.value, self._collect_error_node)
        workflow.add_node(VerifierAgentNodes.ASK_CLARIFICATION.value, self._ask_clarification_node)
        workflow.add_node(VerifierAgentNodes.SHOULD_CONTINUE.value, self._check_continuation_node)
        workflow.set_entry_point(VerifierAgentNodes.CHECK_OUTCOME.value)
        
        workflow.add_conditional_edges(
            VerifierAgentNodes.CHECK_OUTCOME.value,
            self._route_after_outcome,
            {
                "success": END,
                "collect_error": VerifierAgentNodes.COLLECT_ERROR.value
            }
        )
        
        workflow.add_edge(VerifierAgentNodes.COLLECT_ERROR.value, VerifierAgentNodes.ASK_CLARIFICATION.value)
        
        workflow.add_conditional_edges(
            VerifierAgentNodes.ASK_CLARIFICATION.value,
            self._route_after_clarification,
            {
                "continue": VerifierAgentNodes.ASK_CLARIFICATION.value,
                "stop": VerifierAgentNodes.SHOULD_CONTINUE.value,
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            VerifierAgentNodes.SHOULD_CONTINUE.value,
            self._route_final,
            {
                "end": END,
                "continue": VerifierAgentNodes.COLLECT_ERROR.value
            }
        )
        
        return workflow

    def _check_outcome_node(self, state: VerifierState) -> VerifierState:
        self.logger.info("Checking installation outcome...")
        
        outcome = select(
            message="How did the installation/execution process go?",
            choices=[
                Choice("Success - everything works as expected", value="success"),
                Choice("Partial success - works but with errors", value="partial"),
                Choice("Failure - critical error occurred", value="failure"),
            ],
            default="success"
        ).ask()
        
        state["outcome"] = outcome
        
        if outcome == "success":
            self.logger.info("User confirmed full success.")
            
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
        context = state.get("current_context", "failure")
        
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

        full_description = f"[{context.upper()}] Category: {error_category}. Details: {problem_description}"        
        errors.append(WorkflowError(description="User reported issue", error=full_description))
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

    def _route_after_outcome(self, state: VerifierState) -> str:
        """Route based on outcome check"""
        if state.get("outcome") == "success":
            return "success"
        return "collect_error"

    def _route_after_clarification(self, state: VerifierState) -> str:
        """Route after asking clarification"""
        if not state.get("should_continue", True):
            return "stop"
        
        user_choice = state.get("user_choice", "")
        if user_choice == "stop":
            return "stop"
        
        if self._should_end_conversation(state):
            self.logger.info("Intelligent shutdown detected.")
            return "end"
        
        if state.get("question_count", 0) < self.max_questions:
            return "continue"
        
        return "stop"

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

    def invoke(self, state: GraphState) -> GraphState:
        self.logger.info("Starting success verification workflow...")
        
        result_state: VerifierState = self.subgraph.invoke(
            VerifierState(
                messages=[],
                outcome="",
                should_continue=True,
                errors=[]
            )
        ) # type: ignore

        print(result_state)

        errors = result_state.get("errors", [])
        if errors:
            state["errors"] = errors
            state["next_node"] = Node.PLANNER_AGENT

        self.logger.info(f"Verification finished. Outcome: {result_state.get('outcome')}")
        return state
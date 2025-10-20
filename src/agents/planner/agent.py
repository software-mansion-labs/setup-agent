from collections import deque
from agents.base_agent import BaseAgent
from graph_state import GraphState, Step, Substep, WorkflowError, Node
from shell import ShellRegistry
from tools.websearch import get_websearch_tool
from typing import List
from config import Config
from langchain_core.messages import HumanMessage
from agents.planner.types import ReadmeAnalysis
from agents.planner.prompts import PlannerPrompts
from InquirerPy.prompts.list import ListPrompt
from InquirerPy.prompts.input import InputPrompt
from constants import FILE_SEPARATOR

class Planner(BaseAgent):
    def __init__(self):
        websearch_tool = get_websearch_tool()

        tools = [websearch_tool]
        super().__init__(
            name=Node.PLANNER_AGENT,
            prompt=PlannerPrompts.AGENT_DESCRIPTION_PROMPT,
            tools=tools,
        )
        self.project_root = Config.get().project_root
        self.shell_registry = ShellRegistry.get()
        
        self.cd_substep = Substep(
            description="Navigate to the project root directory",
            suggested_commands=[f"cd {self.project_root}"],
        )

        self.cd_step = Step(
            description="Navigate to the App project directory",
            substeps=[self.cd_substep],
            assigned_agent=Node.INSTALLER_AGENT,
            run_in_separate_shell=False,
        )

    def _first_analysis(self, state: GraphState) -> GraphState:
        guideline_files = state["guideline_files"]

        chosen_task = state["chosen_task"]

        if not guideline_files:
            state["plan"] = deque([
                Step(
                    description="No README found — unable to plan installation.",
                    substeps=[],
                    assigned_agent=Node.INSTALLER_AGENT
                )
            ])
            return state
        
        guideline_files_merged_content = FILE_SEPARATOR.join([guideline.content for guideline in guideline_files])

        analysis: ReadmeAnalysis = self._invoke_structured_llm(
            ReadmeAnalysis,
            PlannerPrompts.FIRST_GUIDELINES_ANALYSIS,
            f"raw_texts: {guideline_files_merged_content}\nproject_root:{self.project_root}\n**GOAL**: {chosen_task}",
        )

        planned_steps = self._assign_shells([self.cd_step] + analysis.plan)
        state["plan"] = deque(planned_steps)
        return state

    def _handle_errors(self, state: GraphState) -> GraphState:
        errors = state.get("errors", [])
        if not errors:
            return state

        analysis: ReadmeAnalysis = self._invoke_structured_llm(
            ReadmeAnalysis,
            PlannerPrompts.HANDLE_ERRORS,
            input_text=f"errors: {list(errors)}",
        )

        planned_steps = self._assign_shells(analysis.plan)

        state["plan"] = deque(planned_steps) + state["plan"]
        state["errors"] = []
        return state

    def _handle_failed_steps(self, state: GraphState) -> GraphState:
        failed_steps = state.get("failed_steps", [])
        if not failed_steps:
            return state

        analysis: ReadmeAnalysis = self._invoke_structured_llm(
            ReadmeAnalysis,
            PlannerPrompts.HANDLE_FAILED_STEPS,
            input_text=f"failed_steps: {list(failed_steps)}",
        )

        planned_steps = self._assign_shells(analysis.plan)

        state["plan"] = deque(planned_steps) + deque([failed_step.step for failed_step in failed_steps]) + state["plan"]
        state["failed_steps"] = []
        return state
    
    def _assign_shells(self, steps: List[Step]) -> List[Step]:
        """Ensure each step that needs its own shell has one."""
        for step in steps:
            if step.run_in_separate_shell:
                step.substeps = [self.cd_substep] + step.substeps
                step.shell_id = self.shell_registry.register_new_shell()
        return steps

    def _ensure_installation_success(self, state: GraphState) -> GraphState:
        self.logger.info("Checking if installation succeeded...")
        choice = ListPrompt(
            message="Did the installation/process achieve the desired goal?",
            choices=["Yes, everything worked", "No, there was a problem"],
            default="Yes, everything worked"
        ).execute()

        if choice == "Yes, everything worked":
            self.logger.info("User confirmed success.")
            return state

        return self._collect_user_error(state)
    
    def _collect_user_error(self, state: GraphState) -> GraphState:
        """Interactively collect a structured WorkflowError from the user."""
        problem_description = InputPrompt(
            message="Please describe the problem or paste the error/output here:"
        ).execute()

        description = "User reported installation issue"
        state["errors"].append(WorkflowError(description=description, error=problem_description))

        self.logger.info("Capturing clarifying details from the user...")

        while True:
            system_prompt = PlannerPrompts.COLLECT_USER_ERRORS.format(problem_description=problem_description)
            try:
                result = self.agent.invoke({"messages": [HumanMessage(content=system_prompt)]})
                agent_question = result["messages"][-1].content.strip()
            except Exception as e:
                self.logger.error(f"LLM error during clarification: {e}")
                break

            if not agent_question:
                break

            user_reply = InputPrompt(message=f"[Agent] {agent_question}\n=>").execute()
            if not user_reply.strip():
                break

            state["errors"].append(WorkflowError(
                description=f"Clarification: {agent_question}",
                error=user_reply,
            ))

        self.logger.info("Error information collected successfully.")
        return state

    def _decide_next_agent(self, state: GraphState) -> GraphState:
        plan = state.get("plan", deque())
        if not plan:
            state["next_node"] = None
            return state

        next_step = plan[0]
        state["next_node"] = next_step.assigned_agent
        return state

    def invoke(self, state: GraphState) -> GraphState:
        self.logger.info("Planning unified step sequence...")

        if "plan" not in state:
            self._first_analysis(state)

        state = self._handle_failed_steps(state)
        if len(state["plan"]) == 0:
            self._ensure_installation_success(state)
        
        state = self._handle_errors(state)
        state = self._decide_next_agent(state)
        return state

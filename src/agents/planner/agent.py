from collections import deque
from agents.base_react_agent import BaseReactAgent
from graph_state import GraphState, Step, Substep, Node
from shell import ShellRegistry
from tools import get_websearch_tool
from typing import List
from config import Config
from agents.planner.types import ReadmeAnalysis
from agents.planner.prompts import PlannerPrompts
from constants import FILE_SEPARATOR


class Planner(BaseReactAgent):
    """
    The Planner agent is responsible for analyzing project documentation (e.g., README files)
    and constructing an execution plan for installation or project setup tasks.

    It coordinates with other agents in the system to:
      - Analyze initial guidelines and tasks.
      - Generate a structured step-by-step plan.
      - Handle errors and failed steps.
      - Decide the next appropriate agent to execute.

    Attributes:
        project_root (str): The root directory of the project being analyzed.
        shell_registry (ShellRegistry): Manages shell session allocations for steps.
        cd_substep (Substep): Substep for navigating to the project directory.
        cd_step (Step): Step that ensures the working directory is correct before running commands.
    """

    def __init__(self) -> None:
        """
        Initialize the Planner agent.

        Loads the web search tool, registers shell management, and prepares
        default navigation steps for ensuring all operations occur in the project root.
        """
        websearch_tool = get_websearch_tool()
        tools = [websearch_tool]
        super().__init__(
            name=Node.PLANNER_AGENT.value,
            prompt=PlannerPrompts.AGENT_DESCRIPTION_PROMPT.value,
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
        """
        Perform the first analysis of the project's README or guideline files for given task.
        Includes context on finished steps from previous executions so the LLM can skip them.
        
        Args:
            state (GraphState): The current workflow state, containing chosen task and guideline files.

        Returns:
            GraphState: Updated state with a newly generated step plan.
        """
        guideline_files = state["guideline_files"]
        chosen_task = state["chosen_task"]
        finished_steps = state.get("finished_steps", [])

        if not guideline_files:
            state["plan"] = deque(
                [
                    Step(
                        description="No README found — unable to plan installation.",
                        substeps=[],
                        assigned_agent=Node.INSTALLER_AGENT,
                    )
                ]
            )
            return state

        finished_steps_context = ""
        if finished_steps:
            history_lines = []
            for fs in finished_steps:
                status = "SKIPPED" if fs.skipped else "COMPLETED"
                history_lines.append(f"- {fs.step.description} [{status}]")
            
            finished_steps_context = (
                "\n\n**CONTEXT: STEPS ALREADY COMPLETED (DO NOT INCLUDE IN NEW PLAN)**:\n" 
                + "\n".join(history_lines)
            )

        guideline_files_merged_content = FILE_SEPARATOR.join(
            [guideline.content for guideline in guideline_files]
        )

        prompt_input = (
            f"raw_texts:\n{guideline_files_merged_content}\n\n"
            f"project_root:\n{self.project_root}\n\n"
            f"**GOAL**:\n{chosen_task}"
            f"{finished_steps_context}"
        )

        analysis: ReadmeAnalysis = self._invoke_structured_llm(
            ReadmeAnalysis,
            PlannerPrompts.FIRST_GUIDELINES_ANALYSIS.value,
            input_text=prompt_input,
        )

        planned_steps = self._assign_shells([self.cd_step] + analysis.plan)
        state["plan"] = deque(planned_steps)
        return state

    def _handle_errors(self, state: GraphState) -> GraphState:
        """
        Handle any collected errors by invoking the LLM to replan corrective actions.

        Args:
            state (GraphState): The current state containing `errors`.

        Returns:
            GraphState: Updated state with additional steps to resolve errors.
        """
        errors = state.get("errors", [])
        if not errors:
            return state

        analysis: ReadmeAnalysis = self._invoke_structured_llm(
            ReadmeAnalysis,
            PlannerPrompts.HANDLE_ERRORS.value,
            input_text=f"errors: {list(errors)}",
        )
        plan = state.get("plan") or deque()
        planned_steps = self._assign_shells(analysis.plan)
        state["plan"] = deque(planned_steps) + plan
        state["errors"] = []
        return state

    def _handle_failed_steps(self, state: GraphState) -> GraphState:
        """
        Process any failed steps from previous executions and generate recovery steps.

        Args:
            state (GraphState): The current state containing `failed_steps`.

        Returns:
            GraphState: Updated state with new or retried steps added to the plan.
        """
        failed_steps = state.get("failed_steps", [])
        if not failed_steps:
            return state

        analysis: ReadmeAnalysis = self._invoke_structured_llm(
            ReadmeAnalysis,
            PlannerPrompts.HANDLE_FAILED_STEPS.value,
            input_text=f"failed_steps: {list(failed_steps)}",
        )
        plan = state.get("plan") or deque()

        planned_steps = self._assign_shells(analysis.plan)
        state["plan"] = (
            deque(planned_steps)
            + plan
        )

        state["failed_steps"] = []
        return state

    def _assign_shells(self, steps: List[Step]) -> List[Step]:
        """
        Ensure that each step requiring a separate shell environment is assigned one.

        Args:
            steps (List[Step]): Steps to process.

        Returns:
            List[Step]: Updated list of steps with shell IDs assigned where needed.
        """
        for step in steps:
            if step.run_in_separate_shell:
                step.substeps = [self.cd_substep] + step.substeps
                step.shell_id = self.shell_registry.register_new_shell()
        return steps


    def _decide_next_agent(self, state: GraphState) -> GraphState:
        """
        Decide which agent should execute next based on the current plan.

        Args:
            state (GraphState): The current workflow state.

        Returns:
            GraphState: Updated state with `next_node` set to the next responsible agent.
        """
        plan = state.get("plan", deque())
        if not plan:
            state["next_node"] = None
            return state

        next_step = plan[0]
        state["next_node"] = next_step.assigned_agent
        return state

    def invoke(self, state: GraphState) -> GraphState:
        """
        Execute the main planner logic.

        This orchestrates:
          - Initial guideline analysis.
          - Handling of failed or erroneous steps.
          - Verification of success.
          - Determination of the next agent to run.

        Args:
            state (GraphState): The current workflow state.

        Returns:
            GraphState: Updated state containing the next steps and assigned agents.
        """
        self.logger.info("Planning unified step sequence...")

        if state["plan"] is None:
            self._first_analysis(state)

        state = self._handle_failed_steps(state)
        state = self._handle_errors(state)
        state = self._decide_next_agent(state)
        return state

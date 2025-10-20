from itertools import chain
from typing import List

from graph_state import FinishedStep, GraphState, Node, Step, WorkflowError
from tools import run_command_tool, user_input_tool, authenticate_tool
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from shell import ShellRegistry
from InquirerPy.prompts.list import ListPrompt
from agents.runner.prompts import RunnerPrompts
from shell import BaseShell
from constants import FILE_SEPARATOR


class Runner(BaseAgent):
    """Agent responsible for executing application runtime steps.

    The `Runner` coordinates command execution, user interaction,
    and error tracking for application run workflows.

    It extends `BaseAgent` and uses the following tools:
        - `run_command_tool`: Executes shell commands.
        - `user_input_tool`: Collects user input interactively.
        - `authenticate_tool`: Handles authentication during runtime operations.
    """

    def __init__(self):
        tools = [run_command_tool, user_input_tool, authenticate_tool]
        super().__init__(
            name=Node.RUNNER_AGENT.value,
            prompt=RunnerPrompts.RUNNER_AGENT_DESCRIPTION.value,
            tools=tools,
        )
        self._shell_registry = ShellRegistry.get()

    def invoke(self, state: GraphState) -> GraphState:
        """Main entry point for executing runtime steps.

        Args:
            state (GraphState): The current workflow state.

        Returns:
            GraphState: Updated workflow state after executing (or skipping) a runtime step.
        """
        self.logger.info("Running application steps...")

        steps = state["plan"]
        if not steps:
            self.logger.warning("No remaining run steps.")
            return state

        next_step = steps.popleft()
        if next_step.assigned_agent != Node.RUNNER_AGENT:
            self.logger.warning("Received task that is not assigned to the runner")
            return state

        return self._process_step(next_step, state)

    def _process_step(self, step: Step, state: GraphState) -> GraphState:
        """Handle the logic for processing an individual runtime step.

        Args:
            step (Step): The runtime step to execute.
            state (GraphState): The current workflow state.

        Returns:
            GraphState: Updated state after processing this step.
        """
        shell = self._shell_registry.get_shell(step.shell_id)
        errors = state.get("errors", [])
        finished_steps = state.get("finished_steps", [])

        self.logger.info(f"Next step: {step.description}")
        suggested_commands = self._get_suggested_commands(step)

        if suggested_commands:
            self.logger.info(f"Suggested commands:\n{suggested_commands}")

        choice = self._choose_action()
        if choice != "Continue":
            return self._handle_non_continue_choice(choice, step, finished_steps, state)

        shell.clean_step_buffer()
        return self._execute_commands(step, shell, finished_steps, errors, state)

    def _get_suggested_commands(self, step: Step) -> str:
        """Aggregate and format all suggested shell commands from substeps.

        Args:
            step (Step): Step containing one or more substeps with suggested commands.

        Returns:
            str: A newline-separated string of all suggested commands.
        """
        return "\n".join(
            chain.from_iterable(substep.suggested_commands for substep in step.substeps)
        )

    def _choose_action(self) -> str:
        """Prompt the user to choose how to handle the current step.

        Returns:
            str: User-selected action ("Continue", "Skip", or "Learn more").
        """
        return ListPrompt(
            message="Choose an action:",
            choices=["Continue", "Skip", "Learn more"],
            default="Continue",
        ).execute()

    def _handle_non_continue_choice(
        self, choice: str, step: Step, finished_steps: List[FinishedStep], state: GraphState
    ) -> GraphState:
        """Handle user actions other than 'Continue' (Skip or Learn more).

        Args:
            choice (str): User's chosen action.
            step (Step): The current step being processed.
            finished_steps (List[FinishedStep]): List of finished steps so far.
            state (GraphState): Current workflow state.

        Returns:
            GraphState: Updated workflow state.
        """
        if choice == "Skip":
            self.logger.info(f"Skipping step: {step.description}")
            finished_steps.append(
                FinishedStep(step=step, output="Command skipped by user", skipped=True)
            )
        elif choice == "Learn more":
            # TODO: Add LLM or web search review for runtime safety
            pass
        state["finished_steps"] = finished_steps
        return state

    def _execute_commands(
        self,
        step: Step,
        shell: BaseShell,
        finished_steps: List[FinishedStep],
        errors: List[WorkflowError],
        state: GraphState,
    ) -> GraphState:
        """Execute the suggested runtime commands for a given step.

        Args:
            step (Step): The runtime step containing commands to execute.
            shell (BaseShell): The shell session used to execute the commands.
            finished_steps (List[FinishedStep]): List of completed steps.
            errors (List[WorkflowError]): List of workflow errors.
            state (GraphState): Current workflow state.

        Returns:
            GraphState: Updated state after executing the commands.
        """
        prompt = self._prepare_execution_prompt(step, finished_steps)

        try:
            self.agent.invoke(
                {"messages": [HumanMessage(content=prompt)], "shell_id": step.shell_id}
            )
            step.assigned_agent = Node.RUNNER_AGENT
            finished_steps.append(
                FinishedStep(step=step, output=shell.get_step_buffer())
            )
        except Exception as e:
            error_message = f"Error during '{step.description}': {e}"
            self.logger.error(error_message)
            errors.append(WorkflowError(description=step.description, error=str(e)))

        state["errors"] = errors
        state["finished_steps"] = finished_steps
        state["next_node"] = Node.PLANNER_AGENT
        return state

    def _prepare_execution_prompt(self, step: Step, finished_steps: List[FinishedStep]) -> str:
        """Construct a formatted prompt for the language model to guide command execution.

        Args:
            step (Step): Current step being processed.
            finished_steps (List[FinishedStep]): Previously completed steps.

        Returns:
            str: Fully formatted text prompt for LLM invocation.
        """
        commands_text = FILE_SEPARATOR.join(
            ", ".join(substep.suggested_commands) for substep in step.substeps
        )
        finished_text = (
            ", ".join(f.step.description for f in finished_steps)
            if finished_steps
            else "none"
        )

        return RunnerPrompts.STEP_RUNNING_PROMPT.value.format(
            step_description=step.description,
            commands_text=commands_text,
            finished_text=finished_text,
        )

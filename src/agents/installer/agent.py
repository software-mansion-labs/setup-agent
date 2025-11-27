from collections import deque
from itertools import chain

from graph_state import GraphState, FinishedStep, Node, WorkflowError, Step
from langchain_core.messages import HumanMessage
from tools import (
    authenticate_tool,
    get_websearch_tool,
    run_command_tool,
    user_input_tool,
    prompt_user_input_tool,
    prompt_user_selection_tool,
    use_arrow_keys_sequence,
    use_keyboard_keys
)
from agents.base_agent import BaseAgent
from shell import ShellRegistry
from agents.installer.prompts import InstallerPrompts
from typing import List
from constants import FILE_SEPARATOR
from InquirerPy.prompts.list import ListPrompt
from shell import BaseShell
from agents.installer.types import StepExplanation

class Installer(BaseAgent):
    """Agent responsible for managing installation steps within a workflow.

    The `Installer` class acts as a specialized automation agent that
    executes installation commands, interacts with users for decisions,
    and tracks installation progress and errors.

    It extends `BaseAgent` and uses tools such as:
    - Command execution (`run_command_tool`)
    - Web search (`get_websearch_tool`)
    - Authentication (`authenticate_tool`)
    - User input interaction (`user_input_tool`)
    - Use arrow keys (`use_arrow_keys_sequence`)
    - Use special keyboard keys (`use_keyboard_keys`)
    """

    def __init__(self) -> None:
        self._shell_registry = ShellRegistry.get()
        websearch_tool = get_websearch_tool()
        tools = [
            websearch_tool,
            run_command_tool,
            authenticate_tool,
            user_input_tool,
            prompt_user_input_tool,
            prompt_user_selection_tool,
            use_arrow_keys_sequence,
            use_keyboard_keys
        ]
        super().__init__(
            name=Node.INSTALLER_AGENT.value,
            prompt=InstallerPrompts.INSTALLER_AGENT_DESCRIPTION.value,
            tools=tools
        )

    def invoke(self, state: GraphState) -> GraphState:
        """Main entry point for processing installation steps.

        Args:
            state (GraphState): Current workflow state containing the installation plan and metadata.

        Returns:
            GraphState: Updated state after executing (or skipping) an installation step.
        """
        self.logger.info("Installing required tools...")
        steps = state.get("plan", deque())

        if not steps:
            self.logger.warning("No remaining installation steps.")
            return state

        next_step = steps.popleft()
        if next_step.assigned_agent != Node.INSTALLER_AGENT.value:
            return state

        return self._process_step(next_step, state)

    def _process_step(self, step: Step, state: GraphState) -> GraphState:
        """Handle execution logic for a single installation step.

        Args:
            step (Step): The installation step to process.
            state (GraphState): Current workflow state.

        Returns:
            GraphState: Updated workflow state after processing the step.
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
        """Aggregate and format suggested shell commands from substeps.

        Args:
            step (Step): Installation step containing one or more substeps.

        Returns:
            str: Formatted string of suggested commands, separated by newlines.
        """
        return "\n".join(
            chain.from_iterable(substep.suggested_commands for substep in step.substeps)
        )

    def _choose_action(self) -> str:
        """Prompt the user to choose an action for the current step.

        Options:
            - "Continue": Proceed with executing the suggested commands.
            - "Skip": Mark the step as skipped.
            - "Learn more": Placeholder for future LLM or web search integration.

        Returns:
            str: User's selected action.
        """
        return ListPrompt(
            message="Choose an action:",
            choices=["Continue", "Skip", "Learn more"],
            default="Continue",
        ).execute()

    def _handle_non_continue_choice(
        self,
        choice: str,
        step: Step,
        finished_steps: List[FinishedStep],
        state: GraphState,
    ) -> GraphState:
        """Handle user choices other than 'Continue'.

        Args:
            choice (str): User's choice ("Skip" or "Learn more").
            step (Step): Current step being processed.
            finished_steps (List[FinishedStep]): List of completed steps.
            state (GraphState): Current workflow state.

        Returns:
            GraphState: Updated workflow state after processing the user's decision.
        """
        if choice == "Skip":
            finished_steps.append(
                FinishedStep(step=step, output="Command skipped by user", skipped=True)
            )

        elif choice == "Learn more":
            explanation = self._learn_more_about_step(step)
            print("\n=== Step Explanation ===")
            print(explanation)
            print("========================\n")
            next_choice = self._choose_action()
            if next_choice == "Continue":
                shell = self._shell_registry.get_shell(step.shell_id)
                return self._execute_commands(step, shell, finished_steps, state.get("errors", []), state)
            else:
                return self._handle_non_continue_choice(next_choice, step, finished_steps, state)

        state["finished_steps"] = finished_steps
        return state

    def _learn_more_about_step(self, step: Step) -> str:
        """
        Explain what this installation step does and if it's safe.

        Args:
            step (Step): step to be explained based on description and suggested commands.
        
        Returns:
            str: Explanation of the step with it's purpose, possible effects and verdict if it's safe to be performed.
        
        """
        try:
            response: StepExplanation = self._llm.invoke(
                StepExplanation,
                InstallerPrompts.STEP_EXPLANATION_PROMPT.value,
                f"Step description: {step.description}\nSuggested commands: {self._get_suggested_commands(step)}"
            )

            return (
                f"Purpose: {response.purpose}\n"
                f"Actions: {response.actions}\n"
                f"Safe to run: {response.safe}"
            )

        except Exception as e:
            self.logger.error(f"Error explaining step '{step.description}': {e}")
            return f"Could not retrieve explanation: {e}"

    def _execute_commands(
        self,
        step: Step,
        shell: BaseShell,
        finished_steps: List[FinishedStep],
        errors: List[WorkflowError],
        state: GraphState,
    ) -> GraphState:
        """Execute the suggested installation commands for a given step.

        Args:
            step (Step): Current step containing installation commands.
            shell (BaseShell): Active shell session used to run commands.
            finished_steps (List[FinishedStep]): Completed steps so far.
            errors (List[WorkflowError]): Recorded workflow errors.
            state (GraphState): Current workflow state.

        Returns:
            GraphState: Updated state after attempting to execute the commands.
        """
        prompt = self._prepare_installation_prompt(step, finished_steps)
        try:
            self.agent.invoke(
                {"messages": [HumanMessage(content=prompt)], "shell_id": step.shell_id, "agent_name": self.name}
            )
            finished_steps.append(
                FinishedStep(step=step, output=shell.get_step_buffer())
            )
        except Exception as e:
            self.logger.error(f"Error during '{step.description}': {e}")
            errors.append(WorkflowError(description=step.description, error=str(e)))

        state["errors"] = errors
        state["finished_steps"] = finished_steps
        return state

    def _prepare_installation_prompt(
        self, step: Step, finished_steps: List[FinishedStep]
    ) -> str:
        commands_text = FILE_SEPARATOR.join(
            ", ".join(substep.suggested_commands) for substep in step.substeps
        )
        installed_text = (
            ", ".join(f.step.description for f in finished_steps)
            if finished_steps
            else "none"
        )

        return InstallerPrompts.INSTALLATION_PROMPT.value.format(
            step_description=step.description,
            installed_text=installed_text,
            commands_text=commands_text,
        )

from collections import deque
from itertools import chain

from graph_state import GraphState, FinishedStep, Node, WorkflowError, Step
from langchain_core.messages import HumanMessage
from tools.authenticate_tool import authenticate_tool
from tools.websearch import get_websearch_tool
from tools.run_command_tool import run_command_tool
from tools.user_input_tool import user_input_tool
from agents.base_agent import BaseAgent
from shell import ShellRegistry
from agents.installer.prompts import InstallerPrompts
from typing import List
from constants import FILE_SEPARATOR
from InquirerPy.prompts.list import ListPrompt


class Installer(BaseAgent):
    def __init__(self):
        self.shell_registry = ShellRegistry.get()
        websearch_tool = get_websearch_tool()
        tools = [
            websearch_tool,
            run_command_tool,
            authenticate_tool,
            user_input_tool,
        ]
        super().__init__(
            name="installation_agent",
            prompt=InstallerPrompts.INSTALLER_AGENT_DESCRIPTION.value,
            tools=tools,
        )

    def invoke(self, state: GraphState) -> GraphState:
        self.logger.info("Installing required tools...")

        steps = state.get("plan", deque())
        if not steps:
            self.logger.warning("No remaining installation steps.")
            return state

        next_step = steps.popleft()
        if next_step.assigned_agent != Node.INSTALLER_AGENT.value:
            return state

        shell = self.shell_registry.get_shell(next_step.shell_id)
        errors = state.get("errors", [])
        finished_steps = state.get("finished_steps", [])

        self.logger.info(f"Next step: {next_step.description}")

        suggested_commands = self._get_suggested_commands(next_step)
        if suggested_commands:
            self.logger.info(f"Suggested commands: {suggested_commands}")

        choice = self._choose_action()
        if choice == "Skip":
            finished_steps.append(
                FinishedStep(step=next_step, output="Command skipped by user", skipped=True)
            )
            state["finished_steps"] = finished_steps
            return state
        elif choice == "Learn more":
            # TODO: use LLM to review commands and determine if it's safe
            return state

        shell.clean_step_buffer()

        if suggested_commands:
            prompt = self._prepare_installation_prompt(next_step, finished_steps)
            try:
                self.agent.invoke(
                    {"messages": [HumanMessage(content=prompt)], "shell_id": next_step.shell_id}
                )
                finished_steps.append(
                    FinishedStep(step=next_step, output=shell.get_step_buffer())
                )
            except Exception as e:
                self.logger.error(f"Error occurred while processing '{next_step.description}': {e}")
                errors.append(WorkflowError(description=next_step.description, error=str(e)))

        state["errors"] = errors
        state["finished_steps"] = finished_steps
        return state

    def _get_suggested_commands(self, step: Step) -> str:
        """Flatten and format suggested commands for display."""
        return "\n".join(
            chain.from_iterable(substep.suggested_commands for substep in step.substeps)
        )

    def _choose_action(self) -> str:
        """Prompt user to choose how to handle the current step."""
        return ListPrompt(
            message="Choose an action:",
            choices=["Continue", "Skip", "Learn more"],
            default="Continue",
        ).execute()

    def _prepare_installation_prompt(self, step: Step, finished_steps: List[FinishedStep]) -> str:
        """Generate the formatted prompt for the agent."""
        commands_text = FILE_SEPARATOR.join(
            [", ".join(substep.suggested_commands) for substep in step.substeps]
        )
        installed_text = (
            ", ".join(finished_step.step.description for finished_step in finished_steps)
            if finished_steps else "none"
        )

        return InstallerPrompts.INSTALLATION_PROMPT.value.format(
            next_step_description=step.description,
            installed_text=installed_text,
            commands_text=commands_text
        )

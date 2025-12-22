from graph_state import FinishedStep, Node, Step
from tools import (
    authenticate_tool,
    get_websearch_tool,
    run_command_tool,
    user_input_tool,
    prompt_user_input_tool,
    prompt_user_selection_tool,
    use_arrow_keys_sequence,
    use_keyboard_keys,
)
from shell import ShellRegistry
from agents.installer.prompts import InstallerPrompts
from typing import List
from constants import FILE_SEPARATOR
from agents.base_step_executing_agent import BaseStepExecutingAgent


class Installer(BaseStepExecutingAgent):
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
            use_keyboard_keys,
        ]
        super().__init__(
            name=Node.INSTALLER_AGENT.value,
            prompt=InstallerPrompts.INSTALLER_AGENT_DESCRIPTION.value,
            tools=tools,
        )

    @property
    def step_explanation_prompt(self) -> str:
        return InstallerPrompts.STEP_EXPLANATION_PROMPT.value

    def _prepare_execution_prompt(
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

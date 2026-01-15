from typing import List

from agents.base_step_executing_agent.base_step_executing_agent import (
    BaseStepExecutingAgent,
)
from agents.runner.prompts import RunnerPrompts
from constants import FILE_SEPARATOR
from graph_state import FinishedStep, Node, Step
from tools import (
    authenticate_tool,
    prompt_user_input_tool,
    prompt_user_selection_tool,
    run_command_tool,
    use_arrow_keys_sequence,
    use_keyboard_keys,
    user_input_tool,
)


class Runner(BaseStepExecutingAgent):
    """Agent responsible for executing application runtime steps.

    The `Runner` coordinates command execution, user interaction,
    and error tracking for application run workflows.

    It extends `BaseAgent` and uses the following tools:
        - `run_command_tool`: Executes shell commands.
        - `user_input_tool`: Collects user input interactively.
        - `authenticate_tool`: Handles authentication during runtime operations.
        - `prompt_user_selection_tool`: Ask user to select from list of predefined values
        - `prompt_user_input_tool`: Ask user to input text value
        - `use_arrow_keys_sequence`: Use arrow keys
        - `use_keyboard_keys`: Use special keyboard keys
    """

    def __init__(self) -> None:
        tools = [
            run_command_tool,
            user_input_tool,
            authenticate_tool,
            prompt_user_selection_tool,
            prompt_user_input_tool,
            use_arrow_keys_sequence,
            use_keyboard_keys,
        ]
        super().__init__(
            name=Node.RUNNER_AGENT.value,
            prompt=RunnerPrompts.RUNNER_AGENT_DESCRIPTION.value,
            tools=tools,
        )

    def _prepare_execution_prompt(
        self, step: Step, finished_steps: List[FinishedStep]
    ) -> str:
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

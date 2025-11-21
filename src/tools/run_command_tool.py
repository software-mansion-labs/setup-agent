from langchain_core.tools import tool
from shell import BaseShell, StreamToShellOutput
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState
from shell import ShellRegistry
from uuid import UUID
from agents.base_agent import CustomAgentState
from typing import Optional
from utils.logger import LoggerFactory


@tool(parse_docstring=True)
def run_command_tool(
    command: str, state: Annotated[CustomAgentState, InjectedState]
) -> StreamToShellOutput:
    """
    Run a shell command in the persistent interactive shell.

    This tool executes the given `command` in a persistent shell.
    It should NOT be used for sensitive data such as passwords.

    Args:
        command (str): The shell command to execute.
        state (CustomAgentState): The current state of the agent, containing shell_id and agent_name, injected automatically.

    Returns:
        StreamToShellOutput: Structured output from the executed command, containing:
            - needs_action (bool): True if agent/user action is required (e.g., password prompt).
            - reason (Optional[str]): Description of the required action if applicable.
            - output (str): Full cleaned output of the executed command.
    """
    shell_registry = ShellRegistry.get()
    shell_id: Optional[UUID] = state["shell_id"]
    shell: BaseShell = shell_registry.get_shell(shell_id)
    name = state.get("agent_name")
    logger = LoggerFactory.get_logger(name=name)

    logger.info(f"run_command_tool called with args: {command}.")
    result = shell.run_command(command)
    return result

from typing import Optional
from uuid import UUID

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated

from agents.base_react_agent import CustomAgentState
from shell import BaseShell, ShellRegistry, StreamToShellOutput
from utils.logger import LoggerFactory


@tool(parse_docstring=True)
def user_input_tool(
    prompt: str, state: Annotated[CustomAgentState, InjectedState]
) -> StreamToShellOutput:
    """
    Prompt the user for input and send the response to the persistent interactive shell.

    This tool allows the agent to display a message to the user, capture their
    input via Python's `input()`, and send that input to the interactive shell.

    Args:
        prompt (str): The message to show the user when requesting input.
        state (CustomAgentState): The agent's current state, injected automatically.

    Returns:
        StreamToShellOutput: Structured output from the shell after sending the user's input, containing:
            - needs_action (bool): True if further agent/user action is required.
            - reason (Optional[str]): Description of the required action, if any.
            - output (str): Full cleaned output of the shell after executing the input.

    Raises:
        Exception: If an error occurs while sending the input to the shell.
    """

    shell_registry = ShellRegistry.get()
    shell_id: Optional[UUID] = state["shell_id"]
    shell: BaseShell = shell_registry.get_shell(shell_id)
    name = state.get("agent_name")
    logger = LoggerFactory.get_logger(name=name)

    logger.info("user_input_tool called with prompt: %s", prompt)

    user_response = input(f"[{name}] {prompt}\n> ")
    return shell.stream_command(user_response)

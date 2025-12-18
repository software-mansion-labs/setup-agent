from langchain_core.tools import tool
from agents.base_react_agent import CustomAgentState
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState
from enum import Enum
from shell import ShellRegistry
from typing import Optional
from uuid import UUID
from shell import StreamToShellOutput


class KeyboardKey(Enum):
    """
    Enum representing special non-character keys used in shell input.
    """

    ENTER = "ENTER"
    CTRL_C = "CTRL_C"


@tool(parse_docstring=True)
def use_keyboard_keys(
    key: KeyboardKey, state: Annotated[CustomAgentState, InjectedState]
) -> StreamToShellOutput:
    """
    Sends a single non-character key input to a shell instance.

    Args:
        key (KeyboardKey): The key to send. Supported keys are ENTER and CTRL_C.
        state (CustomAgentState): The agent's current state, injected automatically.

    Returns:
        StreamToShellOutput: The result of sending the key to the shell.

    Raises:
        Exception: If an unsupported key is provided or shell interaction fails.
    """
    shell_registry = ShellRegistry().get()
    shell_id: Optional[UUID] = state["shell_id"]
    shell = shell_registry.get_shell(shell_id)

    match key:
        case KeyboardKey.ENTER:
            return shell.send_line("")
        case KeyboardKey.CTRL_C:
            return shell.send_control("c")
        case _:
            raise Exception(f"Unsupported key: {key}")

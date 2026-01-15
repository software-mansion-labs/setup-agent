from enum import Enum
from typing import List, Optional
from uuid import UUID

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated

from agents.base_react_agent import CustomAgentState
from shell import ShellRegistry, StreamToShellOutput


class ArrowKey(Enum):
    """
    Enum representing the four directional arrow keys on a keyboard.
    """

    UP = "\x1b[A"
    DOWN = "\x1b[B"
    RIGHT = "\x1b[C"
    LEFT = "\x1b[D"


@tool(parse_docstring=True)
def use_arrow_keys_sequence(
    arrow_keys: List[ArrowKey], state: Annotated[CustomAgentState, InjectedState]
) -> StreamToShellOutput:
    """
    Sends a sequence of arrow key inputs to a shell instance.

    Args:
        arrow_keys (List[ArrowKey]): A list of arrow keys to send in sequence.
        state (CustomAgentState): The agent's current state, injected automatically.

    Returns:
        StreamToShellOutput: The result of sending the arrow key sequence to the shell.

    Raises:
        Exception: If shell interaction fails.
    """
    shell_registry = ShellRegistry().get()
    shell_id: Optional[UUID] = state["shell_id"]
    shell = shell_registry.get_shell(shell_id)

    arrows_sequence = "".join(key.value for key in arrow_keys)
    return shell.send(arrows_sequence)

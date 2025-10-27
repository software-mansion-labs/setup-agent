from langchain_core.tools import tool
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState
from agents.base_agent import CustomAgentState
from uuid import UUID
from shell import ShellRegistry, StreamToShellOutput
from typing import Optional
from utils.logger import LoggerFactory
import getpass


@tool
def authenticate_tool(
    state: Annotated[CustomAgentState, InjectedState],
) -> StreamToShellOutput:
    """
    Prompt the user for a password and send it to the persistent interactive shell.

    This tool securely requests the user's password and provides it to the
    interactive shell for authentication. It should be used whenever a command
    requires sudo or other password input.

    Returns:
        StreamToShellOutput: Structured output from the shell after providing the password,
        containing:
            - needs_action (bool): True if additional agent/user action is required.
            - reason (Optional[str]): Description of the required action if applicable.
            - output (str): Full cleaned output of the shell response.
    """
    shell_registry = ShellRegistry().get()
    shell_id: Optional[UUID] = state["shell_id"]
    shell = shell_registry.get_shell(shell_id)
    name = state.get("agent_name")
    logger = LoggerFactory.get_logger(name=name)

    logger.info("Prompting for sudo password")
    passwd = getpass.getpass(f"\n[{name}] Enter your sudo password: ")
    return shell.stream_command(command=passwd.strip())

from langchain_core.tools import tool
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState
from agents.base_react_agent import CustomAgentState
from uuid import UUID
from shell import ShellRegistry, StreamToShellOutput
from typing import Optional
from utils.logger import LoggerFactory
import getpass


@tool(parse_docstring=True)
def authenticate_tool(
    state: Annotated[CustomAgentState, InjectedState],
    prompt: str = "Enter your secret/password: "
) -> StreamToShellOutput:
    """
    Prompt the user for a secret (password, API key, token, etc.) and securely send it directly to the persistent interactive shell.

    This tool securely requests a secret from the user and provides it to the
    interactive shell. It should be used whenever a command or operation
    requires a **sudo access, password, API key, token, or any other sensitive secret** input.

    Args:
        state (CustomAgentState): The agent's current state, injected automatically.
        prompt (str): The specific prompt to show the user (e.g., "Enter your API Key: ").

    Returns:
        StreamToShellOutput: Structured output from the shell after providing the secret,
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

    display_prompt = f"[{name}] {prompt}"
    logger.info("Prompting for secret/password")
    secret = getpass.getpass(f"\n{display_prompt}")
    
    return shell.run_command(command=secret.strip(), hide_input=True)
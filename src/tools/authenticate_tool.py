from langchain_core.tools import tool
from shell.interactive_shell import get_interactive_shell
from shell.types import StreamToShellOutput
from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(name="[Authenticate Tool]")
interactive_shell = get_interactive_shell()

@tool(parse_docstring=True)
def authenticate_tool() -> StreamToShellOutput:
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

    logger.debug("authenticate_tool called.")
    
    return interactive_shell.authenticate()
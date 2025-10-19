from langchain_core.tools import tool
from shell import get_interactive_shell, StreamToShellOutput
from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(name="[Run Command Tool]")
interactive_shell = get_interactive_shell()


@tool(parse_docstring=True)
def run_command_tool(command: str) -> StreamToShellOutput:
    """
    Run a shell command in the persistent interactive shell.

    This tool executes the given `command` in a persistent shell.
    It should NOT be used for sensitive data such as passwords.

    Args:
        command (str): The shell command to execute.

    Returns:
        StreamToShellOutput: Structured output from the executed command, containing:
            - needs_action (bool): True if agent/user action is required (e.g., password prompt).
            - reason (Optional[str]): Description of the required action if applicable.
            - output (str): Full cleaned output of the executed command.
    """

    logger.info("run_command_tool called with command: %s", command)

    return interactive_shell.run_command(command)

from langchain_core.tools import tool
from shell.interactive_shell import get_interactive_shell
from shell.types import StreamToShellOutput
from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(name="[User Input Tool]")
interactive_shell = get_interactive_shell()

@tool(parse_docstring=True)
def user_input_tool(prompt: str) -> StreamToShellOutput:
    """
    Prompt the user for input and send the response to the persistent interactive shell.

    This tool allows the agent to display a message to the user, capture their
    input via Python's `input()`, and send that input to the interactive shell.

    Args:
        prompt (str): The message to show the user when requesting input.

    Returns:
        StreamToShellOutput: Structured output from the shell after sending the user's input, containing:
            - needs_action (bool): True if further agent/user action is required.
            - reason (Optional[str]): Description of the required action, if any.
            - output (str): Full cleaned output of the shell after executing the input.
    
    Raises:
        Exception: If an error occurs while sending the input to the shell.
    """
    logger.debug("user_input_tool called with prompt: %s", prompt)
    
    user_response = input(f"[Agent] {prompt}\n> ")
    return interactive_shell.stream_command(user_response)
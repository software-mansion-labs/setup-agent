from langchain_core.tools import tool
from utils.logger import LoggerFactory

@tool(parse_docstring=True)
def ask_user_tool(prompt: str) -> str:
    """
    Prompt the user for input and return their response directly to the agent.

    This tool allows the agent to request additional information, confirmation,
    or clarification from the user. Unlike `authenticate_tool`, the user's
    response is not passed to the shell, but returned directly for further
    reasoning or decision-making.

    Args:
        prompt (str): The question or instruction to show to the user.

    Returns:
        str: The user's response, returned directly to the agent.

    Raises:
        Exception: If an error occurs while collecting user input.
    """

    try:
        name = "ASK_USER_TOOL"
        logger = LoggerFactory.get_logger(name=name)
        logger.info(f"{name} called with prompt: {prompt}")
        user_input = input(f"\n[AGENT > {name}] {prompt}\n> ")
        return user_input.strip()
    except Exception as e:
        return f"[Tool] Exception: {str(e)}"

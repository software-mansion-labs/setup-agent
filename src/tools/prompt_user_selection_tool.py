from langchain_core.tools import tool
from agents.base_agent import CustomAgentState
from utils.logger import LoggerFactory
from InquirerPy.prompts.list import ListPrompt
from typing import List
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState


@tool(parse_docstring=True)
def prompt_user_selection_tool(prompt: str, choices: List[str], state: Annotated[CustomAgentState, InjectedState]) -> str:
    """
    Prompt the user to select one value from a given list of options using InquirerPy.

    This tool allows the agent to request that the user make a choice from several
    options (e.g., selecting a file, environment, or configuration value).

    Args:
        prompt (str): The question or instruction to show to the user.
        choices (list[str]): The list of possible choices the user can select from.

    Returns:
        str: The value selected by the user.

    Raises:
        Exception: If an error occurs while collecting user input.
    """
    name = state.get("agent_name")
    logger = LoggerFactory.get_logger(name=name)
    logger.info(f"prompt_user_selection_tool called with prompt: {prompt} | choices: {choices}")
    
    try:
        if not choices:
            raise ValueError("No choices provided for selection.")

        selection: str = ListPrompt(
            message=f"[{name}] {prompt}",
            choices=choices,
            default=choices[0] if choices else None,
        ).execute()

        return selection.strip()
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return f"[Tool] Exception: {str(e)}"

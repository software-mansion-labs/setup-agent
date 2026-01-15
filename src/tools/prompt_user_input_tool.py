from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from questionary import text
from typing_extensions import Annotated

from agents.base_react_agent import CustomAgentState
from utils.logger import LoggerFactory


@tool(parse_docstring=True)
def prompt_user_input_tool(
    prompt: str, state: Annotated[CustomAgentState, InjectedState]
) -> str:
    """
    Prompt the user for input and return their response directly to the agent.

    This tool allows the agent to request additional information from the user, e. g. to fill some placeholders or missing values.
    It should not be used to get confirmation from the user or to ask user a question.
    Unlike `authenticate_tool`, the user's
    response is not passed to the shell, but returned directly for further
    reasoning or decision-making.

    Args:
        prompt (str): The question or instruction to show to the user.
        state (CustomAgentState): The agent's current state, injected automatically.

    Returns:
        str: The user's response, returned directly to the agent.

    Raises:
        Exception: If an error occurs while collecting user input.
    """
    name = state.get("agent_name")
    logger = LoggerFactory.get_logger(name=name)
    logger.info(f"prompt_user_input_tool called with prompt: {prompt}")

    try:
        user_input: str = text(
            message=f"\n[{name}] {prompt}",
        ).unsafe_ask()

        return user_input.strip()
    except Exception as e:
        return f"[Tool] Exception: {str(e)}"

from typing import List
from graph_state import GraphState, Node
from nodes.base_llm_node import BaseLLMNode
from nodes.task_identifier.prompts import TaskIdentifierPrompts
from nodes.task_identifier.node_types import DeveloperTasks
from constants import FILE_SEPARATOR
from config import Config
from user_prompts.task_selector import TaskSelector


class TaskIdentifierNode(BaseLLMNode):
    """
    A node in the workflow responsible for identifying possible developer tasks
    from project guideline files using an LLM, and prompting the user to choose one.

    Responsibilities:
    - Extract potential tasks from guideline documentation via LLM.
    - Prompt the user to select a task interactively.
    - Update the workflow state with identified and chosen tasks.
    """

    def __init__(self) -> None:
        super().__init__(name=Node.TASK_IDENTIFIER_NODE.value)
        self._config = Config.get()
        self._task_selector = TaskSelector()

    def _extract_possible_tasks(self, guideline_text: str) -> List[str]:
        """
        Extracts a list of potential developer tasks from the provided guideline text
        using a structured LLM response.

        Args:
            guideline_text (str): Combined text content from all guideline files.

        Returns:
            List[str]: A list of identified developer task descriptions.
        """
        result: DeveloperTasks = self._invoke_structured_llm(
            DeveloperTasks,
            TaskIdentifierPrompts.IDENTIFY_TASKS.value,
            input_text=guideline_text,
        )
        return result.tasks

    def invoke(self, state: GraphState) -> GraphState:
        """
        Main entry point for the node. Analyzes documentation, extracts possible tasks,
        prompts for task selection, and updates the workflow state.

        Args:
            state (GraphState): Current workflow graph state containing context data.

        Returns:
            GraphState: Updated state containing possible tasks and the chosen task.
        """
        self.logger.info("Analyzing documentation to identify developer tasks.")

        user_task = self._config.task
        finished_tasks = state["finished_tasks"]
        if user_task and user_task not in finished_tasks:
            state["chosen_task"] = user_task
            return state

        guideline_files = state["selected_guideline_files"]
        if not guideline_files:
            self.logger.warning("No guideline files found.")
            state["possible_tasks"] = []
            return state

        merged_content = FILE_SEPARATOR.join(
            [guideline.content for guideline in guideline_files]
        )

        tasks = self._extract_possible_tasks(merged_content)
        chosen_task = self._task_selector.select_task(tasks)

        state["possible_tasks"] = tasks
        state["chosen_task"] = chosen_task
        return state

from typing import List
from InquirerPy.prompts.list import ListPrompt
from graph_state import GraphState
from nodes.base_llm_node import BaseLLMNode
from nodes.nodes import WorkflowNode
from nodes.task_identifier.prompts import TaskIdentifierPrompts
from nodes.task_identifier.types import DeveloperTasks


class TaskIdentifierNode(BaseLLMNode):
    """
    A node in the workflow responsible for identifying possible developer tasks
    from project guideline files using an LLM, and prompting the user to choose one.

    Responsibilities:
    - Extract potential tasks from guideline documentation via LLM.
    - Prompt the user to select a task interactively.
    - Update the workflow state with identified and chosen tasks.
    """

    def __init__(self):
        super().__init__(name=WorkflowNode.TASK_IDENTIFIER_NODE.value)

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
            TaskIdentifierPrompts.IDENTIFY_TASKS,
            input_text=guideline_text,
        )
        return result.tasks

    def _prompt_task_selection(self, tasks: List[str]) -> str:
        """
        Prompts the user to select one task from the list of identified tasks.

        Args:
            tasks (List[str]): List of possible tasks extracted from the documentation.

        Returns:
            str: The task selected by the user, or an empty string if none are found.
        """
        if not tasks:
            self.logger.warning("No tasks found.")
            return ""

        return ListPrompt(
            message="Which task would you like to perform?",
            choices=tasks,
            cycle=True,
        ).execute()

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

        guideline_files = state.get("guideline_files", [])
        if not guideline_files:
            self.logger.warning("No guideline files found.")
            state["possible_tasks"] = []
            return state

        FILE_SEPARATOR = "=" * 10 + "\n"
        merged_content = FILE_SEPARATOR.join(
            [guideline.content for guideline in guideline_files]
        )

        tasks = self._extract_possible_tasks(merged_content)
        chosen_task = self._prompt_task_selection(tasks)

        state["possible_tasks"] = tasks
        state["chosen_task"] = chosen_task
        return state

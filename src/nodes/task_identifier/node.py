from graph_state import GraphState
from typing import List
from InquirerPy.prompts.list import ListPrompt
from nodes.base_llm_node import BaseLLMNode
from nodes.nodes import WorkflowNode
from nodes.task_identifier.prompts import TaskIdentifierPrompts
from nodes.task_identifier.types import DeveloperTasks


class TaskIdentifierNode(BaseLLMNode):
    def __init__(self):
        super().__init__(name=WorkflowNode.TASK_IDENTIFIER_NODE.value)

    def _extract_possible_tasks(self, guideline_text: str) -> List[str]:
        result: DeveloperTasks = self._invoke_structured_llm(
            DeveloperTasks,
            TaskIdentifierPrompts.IDENTIFY_TASKS,
            input_text=guideline_text,
        )
        return result.tasks

    def _prompt_task_selection(self, tasks: List[str]) -> str:
        if not tasks:
            print("[TaskIdentifier] No tasks found.")
            return ""

        return ListPrompt(
            message="Which task would you like to perform?",
            choices=tasks,
            cycle=True,
        ).execute()

    def invoke(self, state: GraphState) -> GraphState:
        print("[TaskIdentifier] Analyzing documentation to identify developer tasks.")

        guideline_files = state.get("guideline_files", [])
        if not guideline_files:
            print("[TaskIdentifier] No guideline files found.")
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

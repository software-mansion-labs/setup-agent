from config import Config
from graph_state import Node, GraphState
from nodes.base_llm_node import BaseLLMNode
from questionary import select
from nodes.continue_process.types import ProcessAction
from user_prompts.guidelines_selector import GuidelinesSelector
from user_prompts.task_selector import TaskSelector
from utils.file_loader import FileLoader


class ContinueProcessNode(BaseLLMNode):
    def __init__(self) -> None:
        super().__init__(name=Node.CONTINUE_PROCESS_NODE.value)
        self._config = Config.get()
        self._file_loader = FileLoader(project_root=self._config.project_root)
        self._guidelines_selector = GuidelinesSelector(self._file_loader)
        self._task_selector = TaskSelector()

    def invoke(self, state: GraphState) -> GraphState:
        while True:
            current_task = state.get("chosen_task", "Unknown Task")

            choice = select(
                f'Task "{current_task}" completed. How would you like to proceed?',
                choices=[action.value for action in ProcessAction],
            ).unsafe_ask()

            if choice == ProcessAction.CONTINUE.value:
                current_guideline_files = state["selected_guideline_files"]
                possible_guideline_files = state["possible_guideline_files"]
                updated_files = self._guidelines_selector.select_guidelines(
                    guideline_files=possible_guideline_files,
                    default_files=current_guideline_files,
                )
                current_file_paths = set(gf.file for gf in current_guideline_files)
                updated_file_paths = set(gf.file for gf in updated_files)
                guidelines_changed = current_file_paths != updated_file_paths

                state["selected_guideline_files"] = updated_files
                state["plan"] = None
                # errors and failed steps should be empty, but we reset them for the sake of clarity
                state["errors"] = []
                state["failed_steps"] = []

                if guidelines_changed:
                    self.logger.info(
                        "Guideline files updated. Routing to task identifier node."
                    )
                    state["next_node"] = Node.TASK_IDENTIFIER_NODE
                    state["possible_tasks"] = []
                    return state

                chosen_task = state["chosen_task"]
                possible_tasks = state["possible_tasks"]
                finished_tasks = state["finished_tasks"]

                possible_tasks = [
                    task for task in possible_tasks if task != chosen_task
                ]
                finished_tasks.append(chosen_task)
                state["possible_tasks"] = possible_tasks
                state["finished_tasks"] = finished_tasks

                if possible_tasks:
                    task_choice = self._task_selector.select_task(
                        tasks=possible_tasks,
                        message="Select the next task to continue with:",
                    )
                    state["chosen_task"] = task_choice
                    state["next_node"] = Node.PLANNER_AGENT
                    return state

                self.logger.info("No more tasks available. Ending workflow.")
                state["next_node"] = Node.END
                return state

            if choice == ProcessAction.EXIT.value:
                self.logger.info("Exiting workflow as per user request.")
                state["next_node"] = Node.END
                return state

            if choice == ProcessAction.PAUSE.value:
                print("--- Workflow Paused ---")
                print("Background shells are still running.")
                input("Press [Enter] to return to the menu...")

from questionary import select

from config import Config
from graph_state import GraphState, Node
from nodes.base_llm_node import BaseLLMNode
from nodes.continue_process.node_types import ProcessAction
from user_prompts.guidelines_selector import GuidelinesSelector
from user_prompts.task_selector import TaskSelector
from utils.file_loader import FileLoader


class ContinueProcessNode(BaseLLMNode):
    """Node responsible for handling workflow continuation after task completion.

    This node acts as an interactive breakpoint, prompting the user to decide
    whether to proceed to the next task, pause the workflow, or exit. It also
    handles the logic for updating guidelines and managing the task queue
    between steps.

    Attributes:
        _config (Config): The global configuration settings.
        _file_loader (FileLoader): Utility for loading file system resources.
        _guidelines_selector (GuidelinesSelector): Helper for interactive guideline selection.
        _task_selector (TaskSelector): Helper for interactive task selection.
    """

    def __init__(self) -> None:
        """Initializes the ContinueProcessNode with necessary selectors and loaders."""
        super().__init__(name=Node.CONTINUE_PROCESS_NODE.value)
        self._config = Config.get()
        self._file_loader = FileLoader(project_root=self._config.project_root)
        self._guidelines_selector = GuidelinesSelector(self._file_loader)
        self._task_selector = TaskSelector()

    def invoke(self, state: GraphState) -> GraphState:
        """Executes the continuation logic based on user input.

        Displays a menu to the user.
        - If **CONTINUE**: Allows the user to update guidelines.
            - If guidelines change: Routes to `TASK_IDENTIFIER_NODE` to re-evaluate tasks.
            - If guidelines remain: Routes to `PLANNER_AGENT` with the next user-selected task.
            - If no tasks remain: Routes to `END`.
        - If **PAUSE**: Suspends execution until the user presses Enter.
        - If **EXIT**: Routes to `END` to terminate the workflow.

        Args:
            state (GraphState): The current state of the workflow graph containing
                completed tasks, remaining tasks, and active guidelines.

        Returns:
            GraphState: The updated state graph.
        """
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

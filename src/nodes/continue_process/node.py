from config import Config
from graph_state import Node, GraphState
from nodes.base_llm_node import BaseLLMNode
from questionary import select
from nodes.continue_process.types import ProcessAction
from user_prompts.guidelines_selector import GuidelinesSelector
from utils.file_loader import FileLoader

class ContinueProcessNode(BaseLLMNode):
    def __init__(self) -> None:
        super().__init__(name=Node.CONTINUE_PROCESS_NODE.value)
        self._config = Config.get()
        self._file_loader = FileLoader(project_root=self._config.project_root)
        self._selector = GuidelinesSelector(self._file_loader)

    def invoke(self, state: GraphState):
        while True:
            current_task = state.get("chosen_task", "Unknown Task")
            
            choice = select(
                f'Task "{current_task}" completed. How would you like to proceed?',
                choices=[action.value for action in ProcessAction]
            ).ask()

            if choice == ProcessAction.CONTINUE.value:
                current_guideline_files = state["selected_guideline_files"]
                possible_guideline_files = state["possible_guideline_files"]
                updated_files = self._selector.select_guidelines(
                    guideline_files=possible_guideline_files,
                    default_files=current_guideline_files
                )
                state["selected_guideline_files"] = updated_files
                chosen_task = state["chosen_task"]
                possible_tasks = state["possible_tasks"]
                if chosen_task in possible_tasks:
                    possible_tasks.remove(chosen_task)
                
                state["possible_tasks"] = possible_tasks
                state["plan"] = None
                state["errors"] = []
                state["failed_steps"] = []

                if possible_tasks:
                    task_choice: str = select(
                        "Select the next task to continue with:",
                        choices=possible_tasks
                    ).ask()
                    state["chosen_task"] = task_choice
                    state["next_node"] = Node.PLANNER_AGENT
                    return state
                else:
                    self.logger.info("No more tasks available. Ending workflow.")
                    state["next_node"] = Node.END
                    return state

            elif choice == ProcessAction.EXIT.value:
                self.logger.info("Exiting workflow as per user request.")
                state["next_node"] = Node.END
                return state
            
            elif choice == ProcessAction.PAUSE.value:
                print("--- Workflow Paused ---")
                print("Background shells are still running.")
                input("Press [Enter] to return to the menu...")
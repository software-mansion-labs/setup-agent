from graph_state import Node, GraphState
from nodes.base_llm_node import BaseLLMNode
from questionary import select
from nodes.continue_process.types import ProcessAction

class ContinueProcessNode(BaseLLMNode):
    def __init__(self) -> None:
        super().__init__(name=Node.CONTINUE_PROCESS_NODE.value)

    def _prompt_user_selection(self) -> None:
        pass

    def invoke(self, state: GraphState):
        while True:
            current_task = state["chosen_task"]
            choice = select(
                f'Task "{current_task}" completed. How would you like to proceed?',
                choices=[action.value for action in ProcessAction]
            ).ask()

            if choice == ProcessAction.CONTINUE.value:
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
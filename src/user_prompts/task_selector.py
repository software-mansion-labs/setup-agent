from typing import List, Literal
from questionary import select, text


class TaskSelector:
    """Handles interactive task selection from a list of possible tasks."""

    CUSTOM_TASK_OPTION = "Other: (Define custom task)"

    def select_task(
        self, tasks: List[str], message: str = "Which task would you like to perform?"
    ) -> str:
        """
        Prompts the user to select one task from the list of identified tasks,
        or define a custom task.

        Args:
            tasks (List[str]): List of possible tasks to choose from.
            message (str): The prompt message to display to the user.

        Returns:
            str: The task selected by the user, or an empty string if no tasks available.
        """
        if not tasks:
            return ""

        choices = [*tasks, self.CUSTOM_TASK_OPTION]

        selected_task = select(
            message=message, choices=choices, default=choices[0]
        ).unsafe_ask()

        if selected_task == self.CUSTOM_TASK_OPTION:
            custom_task = text(
                message="Please describe your custom task:",
                validate=self._validate_custom_task,
            ).unsafe_ask()
            return custom_task.strip() if custom_task else ""

        return selected_task

    def _validate_custom_task(self, task_input: str) -> Literal[True] | str:
        """
        Validate that custom task input is not empty.

        Args:
            task_input (str): The custom task string entered by the user.

        Returns:
            Literal[True] | str: True if valid, error message otherwise.
        """
        if task_input and task_input.strip():
            return True
        return "Task description cannot be empty."

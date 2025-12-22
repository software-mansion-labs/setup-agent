from abc import abstractmethod
from itertools import chain
from typing import List, Sequence

from questionary import select
from langchain_core.messages import HumanMessage

from agents.base_react_agent import BaseReactAgent
from graph_state import FinishedStep, GraphState, Step, WorkflowError, Node
from shell import ShellRegistry, BaseShell
from agents.base_step_executing_agent.agent_types import StepExplanation
from agents.base_step_executing_agent.prompts import BaseStepExecutingAgentPrompts
from agents.base_step_executing_agent.constants import ChooseActionPromptOptions
from langchain.tools import BaseTool


class BaseStepExecutingAgent(BaseReactAgent):
    """
    Abstract base agent for executing steps (Installation or Runtime).
    Encapsulates shared logic for user interaction, skipping, learning more,
    and command execution.
    """

    def __init__(self, name: str, prompt: str, tools: Sequence[BaseTool]) -> None:
        super().__init__(name=name, prompt=prompt, tools=tools)
        self._shell_registry = ShellRegistry.get()

    @abstractmethod
    def _prepare_execution_prompt(
        self, step: Step, finished_steps: List[FinishedStep]
    ) -> str:
        """Construct a formatted prompt for the language model to guide command execution.

        Args:
            step (Step): Current step being processed.
            finished_steps (List[FinishedStep]): Previously completed steps.

        Returns:
            str: Fully formatted text prompt for LLM invocation.
        """
        pass

    def _process_step(self, step: Step, state: GraphState) -> GraphState:
        """Handle execution logic for a single step.

        Args:
            step (Step): The step to process.
            state (GraphState): Current workflow state.

        Returns:
            GraphState: Updated workflow state after processing the step.
        """
        shell = self._shell_registry.get_shell(step.shell_id)
        errors = state.get("errors", [])
        finished_steps = state.get("finished_steps", [])

        self.logger.info(f"Next step: {step.description}")
        suggested_commands = self._get_suggested_commands(step)

        if suggested_commands:
            self.logger.info(f"Suggested commands:\n{suggested_commands}")

        choice = self._choose_action()
        if choice != ChooseActionPromptOptions.CONTINUE.value:
            return self._handle_non_continue_choice(choice, step, finished_steps, state)

        shell.clean_step_buffer()
        return self._execute_commands(step, shell, finished_steps, errors, state)

    def _get_suggested_commands(self, step: Step) -> str:
        """Aggregate and format suggested shell commands from substeps.

        Args:
            step (Step): Installation step containing one or more substeps.

        Returns:
            str: Formatted string of suggested commands, separated by newlines.
        """
        return "\n".join(
            chain.from_iterable(substep.suggested_commands for substep in step.substeps)
        )

    def _choose_action(self) -> str:
        """Prompt the user to choose an action for the current step.

        Options:
            - "Continue": Proceed with executing the suggested commands.
            - "Skip": Mark the step as skipped.
            - "Learn more": Placeholder for future LLM or web search integration.

        Returns:
            str: User's selected action.
        """
        return select(
            message="Choose an action:",
            choices=[
                ChooseActionPromptOptions.CONTINUE.value,
                ChooseActionPromptOptions.SKIP.value,
                ChooseActionPromptOptions.LEARN_MORE.value,
            ],
            default=ChooseActionPromptOptions.CONTINUE.value,
        ).unsafe_ask()

    def _handle_non_continue_choice(
        self,
        choice: str,
        step: Step,
        finished_steps: List[FinishedStep],
        state: GraphState,
    ) -> GraphState:
        """Handle user choices other than 'Continue'.

        Args:
            choice (str): User's choice ("Skip" or "Learn more").
            step (Step): Current step being processed.
            finished_steps (List[FinishedStep]): List of completed steps.
            state (GraphState): Current workflow state.

        Returns:
            GraphState: Updated workflow state after processing the user's decision.
        """
        if choice == ChooseActionPromptOptions.SKIP.value:
            self.logger.info(f"Skipping step: {step.description}")
            finished_steps.append(
                FinishedStep(step=step, output="Command skipped by user", skipped=True)
            )
        elif choice == ChooseActionPromptOptions.LEARN_MORE.value:
            explanation = self._learn_more_about_step(step)
            print("\n=== Step Explanation ===")
            print(explanation)
            print("========================\n")

            next_choice = self._choose_action()
            if next_choice == ChooseActionPromptOptions.CONTINUE.value:
                shell = self._shell_registry.get_shell(step.shell_id)
                return self._execute_commands(
                    step, shell, finished_steps, state.get("errors", []), state
                )
            else:
                return self._handle_non_continue_choice(
                    next_choice, step, finished_steps, state
                )

        state["finished_steps"] = finished_steps
        return state

    def _learn_more_about_step(self, step: Step) -> str:
        """
        Explain what given step does and if it's safe.

        Args:
            step (Step): step to be explained based on description and suggested commands.

        Returns:
            str: Explanation of the step with it's purpose, possible effects and verdict if it's safe to be performed.

        """
        try:
            response: StepExplanation = self._llm.invoke(
                StepExplanation,
                BaseStepExecutingAgentPrompts.STEP_EXPLANATION_PROMPT.value,
                f"Step description: {step.description}\nSuggested commands: {self._get_suggested_commands(step)}",
            )
            return (
                f"Purpose: {response.purpose}\n"
                f"Actions: {response.actions}\n"
                f"Safe to run: {response.safe}"
            )
        except Exception as e:
            self.logger.error(f"Error explaining step '{step.description}': {e}")
            return f"Could not retrieve explanation: {e}"

    def _execute_commands(
        self,
        step: Step,
        shell: BaseShell,
        finished_steps: List[FinishedStep],
        errors: List[WorkflowError],
        state: GraphState,
    ) -> GraphState:
        """Execute the suggested commands for a given step.

        Args:
            step (Step): Current step containing execution commands.
            shell (BaseShell): Active shell session used to run commands.
            finished_steps (List[FinishedStep]): Completed steps so far.
            errors (List[WorkflowError]): Recorded workflow errors.
            state (GraphState): Current workflow state.

        Returns:
            GraphState: Updated state after attempting to execute the commands.
        """
        prompt = self._prepare_execution_prompt(step, finished_steps)

        try:
            self.agent.invoke(
                {
                    "messages": [HumanMessage(content=prompt)],
                    "shell_id": step.shell_id,
                    "agent_name": self.name,
                }
            )
            if self.name == Node.RUNNER_AGENT.value:
                step.assigned_agent = Node.RUNNER_AGENT

            finished_steps.append(
                FinishedStep(step=step, output=shell.get_step_buffer())
            )
        except Exception as e:
            error_message = f"Error during '{step.description}': {e}"
            self.logger.error(error_message)
            errors.append(WorkflowError(description=step.description, error=str(e)))

        state["errors"] = errors
        state["finished_steps"] = finished_steps

        return state

    def invoke(self, state: GraphState) -> GraphState:
        """Main entry point for executing planned steps.

        Args:
            state (GraphState): The current workflow state.

        Returns:
            GraphState: Updated state after executing (or skipping) a step.
        """
        pass
        self.logger.info("Installing required tools")
        steps = state["plan"]
        if not steps:
            self.logger.warning("No remaining installation steps.")
            return state

        next_step = steps.popleft()
        assigned_agent = next_step.assigned_agent
        if not assigned_agent:
            self.logger.warning("No agent is assigned to the step.")
            return state

        if assigned_agent.value != self.name:
            self.logger.warning("Received task that is not assigned to the this.")
            return state

        return self._process_step(next_step, state)

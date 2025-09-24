from functools import lru_cache
import getpass
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from interactive_shell import InteractiveShell
from src.shell.types import StreamToShellOutput


class CommandReview(BaseModel):
    description: str
    safe: bool
    reason: str


class SafeInteractiveShell(InteractiveShell):
    def __init__(self):
        super().__init__()
        self.logger.info("SafeInteractiveShell initialized.")

    def authenticate(self) -> StreamToShellOutput:
        """
        Prompt the user for sudo password and send it to the shell securely.
        """
        self.logger.info("Prompting for sudo password in SafeInteractiveShell.")
        passwd = getpass.getpass("\n[Shell] Enter your sudo password: ")
        return self.stream_command(command=passwd.strip())

    def run_command(self, command: str) -> StreamToShellOutput:
        """
        Review a command using LLM before executing and log the review.
        If the command is unsafe, ask the user for confirmation before proceeding.
        Pressing Enter executes the command; any other input aborts it.
        """
        self.logger.info(f"Reviewing command before execution: {command}")
        review = self._review_command(command)

        self.logger.info(
            f"LLM review result - Description: '{review.description}', "
            f"Safe: {review.safe}, Reason: '{review.reason}'"
        )

        if not review.safe:
            self.logger.warning(f"Command marked UNSAFE: {review.reason}.")
            user_input = input(
                f"The command is marked unsafe: {review.reason}. Press Enter to proceed or type anything else to abort: "
            )
            if user_input.strip() != '':
                self.logger.info("User chose to abort execution.")
                return StreamToShellOutput(
                    needs_action=False,
                    output=f"Command aborted by user: {review.reason}"
                )
            self.logger.info("User confirmed execution of unsafe command. Proceeding...")

        self.logger.info("Executing command...")
        return super().run_command(command)

    def _review_command(self, command: str) -> CommandReview:
        """
        Use LLM to analyze a shell command and return its safety and description.
        """
        try:
            prompt = f"""
                You are a command-line safety assistant.

                Analyze the following shell command and provide:
                1. A short description of what the command does.
                2. Whether it is SAFE to run (read-only, listing, inspecting, etc.) or UNSAFE
                (installs software, deletes/modifies files, requires sudo, etc.).

                Return your response strictly as JSON following this schema:
                {{
                    "description": string,
                    "safe": boolean,
                    "reason": string
                }}

                Command to analyze:
                {command}
            """

            structured_llm = self._llm.with_structured_output(CommandReview)
            review: CommandReview = structured_llm.invoke([HumanMessage(content=prompt)])

        except Exception as e:
            self.logger.error(f"Failed to review command with LLM: {e}")
            review = CommandReview(description="Unknown", safe=False, reason="LLM failed")

        return review

@lru_cache(maxsize=1)
def get_safe_interactive_shell() -> SafeInteractiveShell:
    """Return a shared instance of SafeInteractiveShell, initialized lazily."""

    return SafeInteractiveShell()

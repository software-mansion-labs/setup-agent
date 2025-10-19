from functools import lru_cache
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from shell.interactive_shell import InteractiveShell
from shell.types import StreamToShellOutput


class CommandReview(BaseModel):
    """
    Represents the safety review of a shell command.

    Attributes:
        description (str): A brief explanation of what the command does.
        safe (bool): Indicates whether the command is considered safe to run.
        reason (str): Explanation of why the command is safe or unsafe.
    """

    description: str
    safe: bool
    reason: str


class SafeInteractiveShell(InteractiveShell):
    """
    An interactive shell wrapper that reviews commands using a language model
    before execution and allows for secure sudo authentication.

    This shell extends `InteractiveShell` to provide the following safety features:
    1. Command review via a language model to check for unsafe operations.
    2. User confirmation before executing commands flagged as unsafe.
    3. Secure password prompting for sudo authentication.
    """

    def __init__(self):
        """
        Initialize the SafeInteractiveShell instance.

        Logs initialization for auditing purposes.
        """
        super().__init__()
        self.logger.info("SafeInteractiveShell initialized.")

    def run_command(self, command: str) -> StreamToShellOutput:
        """
        Review a shell command with a language model before executing it.

        If the command is flagged as unsafe, the user is prompted for confirmation.
        Pressing Enter executes the command; typing anything else aborts it.

        Args:
            command (str): The shell command to review and execute.

        Returns:
            StreamToShellOutput: The result of the executed command or an abort message.
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
            if user_input.strip() != "":
                self.logger.info("User chose to abort execution.")
                return StreamToShellOutput(
                    needs_action=False,
                    output=f"Command aborted by user: {review.reason}",
                )
            self.logger.info(
                "User confirmed execution of unsafe command. Proceeding..."
            )

        self.logger.info("Executing command...")
        return super().run_command(command)

    def _review_command(self, command: str) -> CommandReview:
        """
        Analyze a shell command for safety using a language model.

        The review determines:
        1. A brief description of the command.
        2. Whether the command is safe to run.
        3. The reason for the safety assessment.

        Args:
            command (str): The shell command to analyze.

        Returns:
            CommandReview: A structured review containing the description, safety, and reason.
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
            review: CommandReview = structured_llm.invoke(
                [HumanMessage(content=prompt)]
            )

        except Exception as e:
            self.logger.error(f"Failed to review command with LLM: {e}")
            review = CommandReview(
                description="Unknown", safe=False, reason="LLM failed"
            )

        return review


@lru_cache(maxsize=1)
def get_safe_interactive_shell() -> SafeInteractiveShell:
    """
    Return a shared instance of SafeInteractiveShell, initialized lazily.

    Uses an LRU cache to ensure that only one instance is created and reused
    throughout the application.

    Returns:
        SafeInteractiveShell: A singleton instance of the safe shell.
    """
    return SafeInteractiveShell()

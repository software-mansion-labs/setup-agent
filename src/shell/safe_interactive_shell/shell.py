from shell.interactive_shell.shell import InteractiveShell
from shell.shell_types import StreamToShellOutput
from shell.safe_interactive_shell.shell_types import CommandReview
from shell.safe_interactive_shell.prompts import SafeInteractiveShellPrompts
from shell.security_context import SecurityContext
from typing import Optional
from uuid import UUID


class SafeInteractiveShell(InteractiveShell):
    """
    An interactive shell wrapper that reviews commands using a language model
    before execution and allows for secure sudo authentication.

    This shell extends `InteractiveShell` to provide the following safety features:
    1. Command review via a language model to check for unsafe operations.
    2. User confirmation before executing commands flagged as unsafe.
    3. Secure password prompting for sudo authentication.
    """

    def __init__(
        self,
        security_context: SecurityContext,
        id: Optional[UUID] = None,
        log_file: Optional[str] = None,
        init_timeout: int = 10,
        read_buffer_size: int = 65536,
        read_timeout: int = 2,
    ) -> None:
        """
        Initialize the SafeInteractiveShell instance.

        Logs initialization for auditing purposes.
        """
        super().__init__(
            security_context=security_context,
            id=id,
            log_file=log_file,
            init_timeout=init_timeout,
            read_buffer_size=read_buffer_size,
            read_timeout=read_timeout,
        )
        self.logger.info("SafeInteractiveShell initialized.")

    def run_command(
        self, command: str, hide_input: bool = False
    ) -> StreamToShellOutput:
        """
        Review a shell command with a language model before executing it.

        If the command is flagged as unsafe, the user is prompted for confirmation.
        Pressing Enter executes the command; typing anything else aborts it.

        Args:
            command (str): The shell command to execute.
            hide_input (bool, optional): If True, masks the command in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: A structured object representing the command output.
        """
        command_to_display = self._mask_sequence(
            sequence=command, hide_input=hide_input
        )
        self.logger.info(f"Reviewing command before execution: {command_to_display}")
        review = self._review_command(command_to_display)

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
        return super().run_command(command, hide_input=hide_input)

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
            review = self._llm.invoke(
                schema=CommandReview,
                system_message=SafeInteractiveShellPrompts.REVIEW_COMMAND_SAFETY.value,
                input_text=command,
            )

        except Exception as e:
            self.logger.error(f"Failed to review command with LLM: {e}")
            review = CommandReview(
                description="Unknown", safe=False, reason="LLM failed"
            )

        return review
